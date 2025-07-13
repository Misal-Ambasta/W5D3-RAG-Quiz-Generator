"""
LangChain v0.3 RAG Service - Phases 1-7 Integration
Comprehensive implementation using LangChain abstractions for document processing,
chunking, embeddings, vector stores, retrievers, and reranking.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import MetadataQuery
from weaviate.classes.config import Configure
import redis
from langchain.schema import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.retrievers import BM25Retriever
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain.retrievers.document_compressors import CrossEncoderReranker
from sentence_transformers import CrossEncoder
from services.init_db import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LangChainRAGService:
    def __init__(self, db_manager: DatabaseManager, 
                 weaviate_config: Optional[Dict[str, Any]] = None,
                 redis_config: Optional[Dict[str, str]] = None,
                 google_api_key: Optional[str] = None):
        self.db_manager = db_manager
        self.weaviate_config = weaviate_config
        self.redis_config = redis_config
        self.google_api_key = google_api_key
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.embeddings = self._init_embeddings()
        self.llm = self._init_llm()
        self.vector_store = self._init_vector_store(weaviate_config)
        self.bm25_retriever = self._init_bm25_retriever()
        self.reranker = self._init_reranker()
        self.redis_client = self._init_redis(redis_config)
        
        print("✅ LangChain RAG Service initialized successfully!")
    
    def _init_embeddings(self):
        """Initialize HuggingFace embeddings"""
        try:
            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            raise
    
    def _init_llm(self):
        """Initialize Google Gemini LLM"""
        try:
            return ChatGoogleGenerativeAI(
                model="models/gemini-2.0-flash",
                temperature=0.3,
                max_tokens=1024,
                timeout=60,
                max_retries=2,
                google_api_key=self.google_api_key
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise
    
    def _init_vector_store(self, weaviate_config: Optional[Dict[str, Any]]):
        """Initialize LangChain vector store for Phase 4"""
        if weaviate_config:
            try:
                # Check if this is a cloud configuration
                if weaviate_config.get("cluster_url") and weaviate_config.get("auth_credentials"):
                    # Connect to Weaviate Cloud
                    client = weaviate.connect_to_weaviate_cloud(
                        cluster_url=weaviate_config["cluster_url"],
                        auth_credentials=Auth.api_key(weaviate_config["auth_credentials"])
                    )
                    print("🌩️  Connecting to Weaviate Cloud...")
                else:
                    # Connect to local Weaviate
                    # Handle both old format (host/port) and new format (url)
                    if "url" in weaviate_config:
                        # Parse URL to extract host and port
                        from urllib.parse import urlparse
                        parsed = urlparse(weaviate_config["url"])
                        host = parsed.hostname or "localhost"
                        port = parsed.port or 8080
                    else:
                        # Use direct host/port configuration
                        host = weaviate_config.get("host", "localhost")
                        port = weaviate_config.get("port", 8080)
                    
                    client = weaviate.connect_to_local(
                        host=host,
                        port=port,
                        grpc_port=weaviate_config.get("grpc_port", 50051)
                    )
                    print("🏠 Connecting to local Weaviate...")
                
                # Test connection
                if not client.is_ready():
                    raise ConnectionError("Weaviate client is not ready")
                
                print("✅ Weaviate connection established")
                
                # Create vector store using langchain-weaviate
                vector_store = WeaviateVectorStore(
                    client=client,
                    index_name="DocumentChunks",
                    text_key="content",
                    embedding=self.embeddings,
                    attributes=["content", "metadata"]
                )
                
                return vector_store
                
            except Exception as e:
                print(f"⚠️  Weaviate initialization failed: {e}")
                print("Check your Weaviate Cloud cluster URL and authentication credentials.")
                return None
        else:
            print("⚠️  No Weaviate configuration provided. Vector search disabled.")
            return None
    
    def _init_bm25_retriever(self):
        """Initialize BM25 retriever for Phase 5"""
        try:
            documents = self._get_documents_from_db()
            if not documents:
                self.logger.warning("No documents found for BM25 retriever")
                return None
                
            return BM25Retriever.from_documents(documents)
        except Exception as e:
            self.logger.error(f"Failed to initialize BM25 retriever: {e}")
            return None

    def _get_documents_from_db(self) -> List[Document]:
        """Get documents from database for BM25 retriever"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT content, chunk_metadata 
                    FROM document_chunks 
                    WHERE content IS NOT NULL AND content != ''
                """)
                
                documents = []
                for row in cursor.fetchall():
                    doc = Document(
                        page_content=row[0],
                        metadata=eval(row[1]) if row[1] else {}
                    )
                    documents.append(doc)
                
                return documents
        except Exception as e:
            self.logger.error(f"Error retrieving documents from database: {e}")
            return []

    def _init_reranker(self) -> Optional[object]:
        """Initialize CrossEncoderReranker for Phase 6"""
        try:
            from langchain.retrievers.document_compressors import CrossEncoderReranker
            from sentence_transformers import CrossEncoder
            
            # Create CrossEncoder model instance
            model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            
            # Create reranker with the model instance
            reranker = CrossEncoderReranker(model=model)
            
            self.logger.info("✅ CrossEncoderReranker initialized successfully")
            return reranker
        except Exception as e:
            self.logger.error(f"Failed to initialize reranker: {e}")
            return None

    def process_document(self, file_path: str, filename: str) -> dict:
        """Process a document file, chunk, embed, and store it. Returns a result dict."""
        try:
            # Read file content with multiple encoding attempts
            content = None
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise ValueError(f"Could not decode file {filename} with any of the tried encodings: {encodings}")
            
            # Create a Document
            from langchain_core.documents import Document
            doc = Document(page_content=content, metadata={"filename": filename})
            
            # Add to vector store
            added = self.add_documents([doc])
            
            # Return a result dict
            return {
                "document_id": None,  # Fill in if you have DB integration
                "content_length": len(content),
                "chunks_created": 1,  # Update if you chunk
                "learning_objectives": [],  # Update if you extract
                "vector_indexed": added
            }
        except Exception as e:
            self.logger.error(f"Error processing document: {e}")
            raise
    
    def search(self, query: str, method: str = "hybrid", top_k: int = 5) -> List[Dict[str, Any]]:
        """Unified search method supporting multiple retrieval strategies"""
        try:
            results = []
            
            if method == "vector" and self.vector_store:
                # Vector search using Weaviate
                docs = self.vector_store.similarity_search(query, k=top_k)
                results = self._format_search_results(docs, "vector")
                
            elif method == "bm25" and self.bm25_retriever:
                # BM25 search
                docs = self.bm25_retriever.get_relevant_documents(query)[:top_k]
                results = self._format_search_results(docs, "bm25")
                
            elif method == "hybrid":
                # Hybrid search combining vector and BM25
                vector_results = []
                bm25_results = []
                
                if self.vector_store:
                    vector_docs = self.vector_store.similarity_search(query, k=top_k)
                    vector_results = self._format_search_results(vector_docs, "vector")
                
                if self.bm25_retriever:
                    bm25_docs = self.bm25_retriever.get_relevant_documents(query)[:top_k]
                    bm25_results = self._format_search_results(bm25_docs, "bm25")
                
                # Combine and deduplicate results
                results = self._combine_results(vector_results, bm25_results, top_k)
                
            else:
                # Fallback to database search
                results = self._database_search(query, top_k)
            
            # Apply reranking if available
            if self.reranker and results:
                results = self._rerank_results(query, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def _format_search_results(self, docs: List[Document], method: str) -> List[Dict[str, Any]]:
        """Format search results consistently"""
        results = []
        for doc in docs:
            result = {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "method": method,
                "score": doc.metadata.get("score", 0.0)
            }
            results.append(result)
        return results
    
    def _combine_results(self, vector_results: List[Dict], bm25_results: List[Dict], top_k: int) -> List[Dict]:
        """Combine and deduplicate results from different methods"""
        combined = {}
        
        # Add vector results
        for result in vector_results:
            content = result["content"]
            combined[content] = result
        
        # Add BM25 results (avoiding duplicates)
        for result in bm25_results:
            content = result["content"]
            if content not in combined:
                combined[content] = result
        
        # Sort by score and return top_k
        sorted_results = sorted(combined.values(), key=lambda x: x.get("score", 0), reverse=True)
        return sorted_results[:top_k]
    
    def _database_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Fallback database search using simple text matching"""
        try:
            with self.db_manager.get_session() as session:
                sql_query = """
                SELECT content, chunk_metadata 
                FROM document_chunks 
                WHERE content LIKE :query
                LIMIT :limit
                """
                
                result = session.execute(sql_query, {
                    "query": f"%{query}%",
                    "limit": top_k
                })
                
                results = []
                for row in result:
                    results.append({
                        "content": row.content,
                        "metadata": row.chunk_metadata or {},
                        "method": "database",
                        "score": 0.5
                    })
                
                return results
        except Exception as e:
            logger.error(f"Database search error: {e}")
            return []
    
    def _rerank_results(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank results using cross-encoder"""
        try:
            if not self.reranker or len(results) <= 1:
                return results
            
            # Convert to Document objects for reranker
            documents = []
            for result in results:
                doc = Document(
                    page_content=result["content"],
                    metadata=result["metadata"]
                )
                documents.append(doc)
            
            # Apply reranking using compress_documents method
            reranked_docs = self.reranker.compress_documents(documents, query)
            
            # Convert back to our format
            reranked_results = []
            for doc in reranked_docs:
                result = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "method": "reranked",
                    "score": doc.metadata.get("relevance_score", 0.0)
                }
                reranked_results.append(result)
            
            return reranked_results
            
        except Exception as e:
            logger.error(f"Reranking error: {e}")
            return results
    
    def generate_answer(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Generate answer using LLM with retrieved context"""
        try:
            # Prepare context string
            context_str = "\n\n".join([
                f"Document {i+1}: {doc['content']}"
                for i, doc in enumerate(context[:3])  # Limit to top 3 documents
            ])
            
            # Create prompt
            prompt = f"""Based on the following context, please answer the question. If the answer is not in the context, say "I don't have enough information to answer this question."

Context:
{context_str}

Question: {query}

Answer:"""
            
            # Generate response
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            return "I apologize, but I encountered an error while generating the answer."
    
    def get_cached_result(self, query: str) -> Optional[str]:
        """Get cached result from Redis"""
        if not self.redis_client:
            return None
            
        try:
            cache_key = f"rag_query:{hash(query)}"
            return self.redis_client.get(cache_key)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    def cache_result(self, query: str, result: str, ttl: int = 3600):
        """Cache result in Redis"""
        if not self.redis_client:
            return
            
        try:
            cache_key = f"rag_query:{hash(query)}"
            self.redis_client.setex(cache_key, ttl, result)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to vector store"""
        try:
            if self.vector_store:
                # Add to vector store
                self.vector_store.add_documents(documents)
                
                # Refresh BM25 retriever
                self.bm25_retriever = self._init_bm25_retriever()
                
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all components"""
        status = {
            "embeddings": bool(self.embeddings),
            "llm": bool(self.llm),
            "vector_store": bool(self.vector_store),
            "bm25_retriever": bool(self.bm25_retriever),
            "reranker": bool(self.reranker),
            "redis": bool(self.redis_client)
        }
        
        # Test Weaviate connection if available
        if self.vector_store:
            try:
                # Test with a simple query
                test_results = self.vector_store.similarity_search("test", k=1)
                status["weaviate_connection"] = True
            except Exception as e:
                status["weaviate_connection"] = False
                status["weaviate_error"] = str(e)
        
        return status

    def _init_redis(self, redis_config: Optional[Dict[str, str]]):
        """Initialize Redis client for Phase 7"""
        if not redis_config:
            return None
        try:
            import redis
            client = redis.Redis(
                host=redis_config.get("host", "localhost"),
                port=int(redis_config.get("port", 6379)),
                db=int(redis_config.get("db", 0)),
                decode_responses=True
            )
            # Test connection
            client.ping()
            return client
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis: {e}")
            return None