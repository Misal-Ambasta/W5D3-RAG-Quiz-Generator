"""
Enhanced LangChain v0.3 RAG Service with Complete Upload Pipeline
Implements proper document loading, chunking, and RAG operations
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import MetadataQuery
from weaviate.classes.config import Configure
import redis

# LangChain imports
from langchain.schema import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.retrievers import BM25Retriever
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain.retrievers.document_compressors.cross_encoder_rerank import CrossEncoderReranker
from sentence_transformers import CrossEncoder

# Document loaders
from langchain_community.document_loaders import (
    PyPDFLoader, 
    Docx2txtLoader, 
    TextLoader,
    UnstructuredHTMLLoader
)

# Text splitter
from langchain.text_splitter import RecursiveCharacterTextSplitter

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
        self.weaviate_client = None
        # Initialize components
        self.embeddings = self._init_embeddings()
        self.llm = self._init_llm()
        self.text_splitter = self._init_text_splitter()
        self.vector_store = self._init_vector_store(weaviate_config)
        self.bm25_retriever = None
        self.reranker = None
        self.redis_client = self._init_redis(redis_config)
        
        print("✅ Enhanced LangChain RAG Service initialized successfully!")
    
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
    
    def _init_text_splitter(self):
        """Initialize text splitter for chunking"""
        return RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def _init_vector_store(self, weaviate_config: Optional[Dict[str, Any]]):
        """Initialize LangChain vector store"""
        if weaviate_config:
            try:
                if weaviate_config.get("cluster_url") and weaviate_config.get("auth_credentials"):
                    client = weaviate.connect_to_weaviate_cloud(
                        cluster_url=weaviate_config["cluster_url"],
                        auth_credentials=Auth.api_key(weaviate_config["auth_credentials"])
                    )
                    print("🌩️  Connecting to Weaviate Cloud...")
                else:
                    if "url" in weaviate_config:
                        from urllib.parse import urlparse
                        parsed = urlparse(weaviate_config["url"])
                        host = parsed.hostname or "localhost"
                        port = parsed.port or 8080
                    else:
                        host = weaviate_config.get("host", "localhost")
                        port = weaviate_config.get("port", 8080)
                    
                    client = weaviate.connect_to_local(
                        host=host,
                        port=port,
                        grpc_port=weaviate_config.get("grpc_port", 50051)
                    )
                    print("🏠 Connecting to local Weaviate...")
                
                if not client.is_ready():
                    raise ConnectionError("Weaviate client is not ready")
                
                print("✅ Weaviate connection established")
                
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
                return None
        else:
            print("⚠️  No Weaviate configuration provided. Vector search disabled.")
            return None
    
    def _init_bm25_retriever(self):
        """Initialize BM25 retriever"""
        try:
            documents = self._get_documents_from_db()
            if not documents:
                self.logger.warning("No documents found for BM25 retriever")
                return None
                
            return BM25Retriever.from_documents(documents)
        except Exception as e:
            self.logger.error(f"Failed to initialize BM25 retriever: {e}")
            return None
    
    def _init_reranker(self):
        """Initialize cross-encoder reranker."""
        try:
            reranker = CrossEncoderReranker(
                model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
                top_n=3
            )
            return reranker
        except Exception as e:
            logger.error(f"Failed to initialize reranker: {e}")
            return None
    
    def _init_redis(self, redis_config: Optional[Dict[str, str]]):
        """Initialize Redis client"""
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
            client.ping()
            return client
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis: {e}")
            return None
        
    def cleanup(self):
        """Clean up resources on shutdown"""
        try:
            if self.weaviate_client:
                self.weaviate_client.close()
                print("🧹 Weaviate client closed")
            
            if self.redis_client:
                self.redis_client.close()
                print("🧹 Redis client closed")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return None
            
    def get_document_loader(self, file_path: str, file_extension: str):
        """Get appropriate document loader based on file extension"""
        loaders = {
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.txt': TextLoader,
            '.html': UnstructuredHTMLLoader
        }
        print("------- Loading document with extension------ ")
        loader_class = loaders.get(file_extension.lower())
        if not loader_class:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        return loader_class(file_path)
    
    def extract_learning_objectives(self, content: str) -> List[str]:
        """Extract learning objectives from document content using LLM"""
        try:
            prompt = f"""
            Analyze the following document content and extract learning objectives or key topics.
            Return a list of 3-5 main learning objectives or key concepts covered.
            
            Content: {content[:2000]}...
            
            Learning Objectives:
            """
            
            response = self.llm.invoke(prompt)
            objectives = response.content.strip().split('\n')
            return [obj.strip('- ').strip() for obj in objectives if obj.strip()]
        except Exception as e:
            self.logger.error(f"Error extracting learning objectives: {e}")
            return []
    
    def process_document(self, file_path: str, filename: str) -> dict:
        """Enhanced document processing with proper RAG pipeline"""
        try:
            print("------- Processing document------------", filename)
            # Step 1: Insert document record to get real ID
            file_ext = Path(filename).suffix.lower()
            document_id = self._insert_document_record(filename, file_ext)
            print("------- Document record inserted with ID--------")
            print("------- Document record inserted with ID:", document_id)
            # Step 2: Load document using appropriate loader
            
            try:
                loader = self.get_document_loader(file_path, file_ext)
                documents = loader.load()
                print("------- Loaded {len(documents)} pages/sections from document -------" )
                if not documents:
                    raise ValueError("No content extracted from document")
                
                # Combine all pages/sections into single content
                full_content = "\n\n".join([doc.page_content for doc in documents])
                
            except Exception as e:
                # Fallback to simple text reading
                self.logger.warning(f"Loader failed, falling back to text reading: {e}")
                full_content = self._read_file_with_fallback(file_path)
            
            # Step 3: Extract learning objectives
            learning_objectives = self.extract_learning_objectives(full_content)
            self.logger.info("------- Extracted {len(learning_objectives)} learning objectives")
            print("------- Extracted {len(learning_objectives)} learning objectives -------")
            # Step 4: Split document into chunks
            chunks = self.text_splitter.split_text(full_content)
            self.logger.info("------- Split document into {len(chunks)} chunks ")
            print("------- Split document into {len(chunks)} chunks -------")
            # Step 5: Create Document objects with enhanced metadata
            chunk_documents = []
            for i, chunk in enumerate(chunks):
                metadata = {
                    "filename": filename,
                    "file_type": file_ext,
                    "file_path": str(file_path),
                    "chunk_index": i,
                    "chunk_id": f"{document_id}_{i}",
                    "document_id": document_id,
                    "total_chunks": len(chunks),
                    "timestamp": str(datetime.now()),
                    "source": "document_upload",
                    "learning_objectives": ", ".join(learning_objectives)
                }
                
                doc = Document(page_content=chunk, metadata=metadata)
                chunk_documents.append(doc)
            
            # Step 6: Add to vector store
            vector_success = False
            vectors_created = 0
            
            if self.vector_store:
                try:
                    self.vector_store.add_documents(chunk_documents)
                    vector_success = True
                    vectors_created = len(chunk_documents)
                    self.logger.info(f"Added {vectors_created} vectors to Weaviate")
                except Exception as e:
                    self.logger.error(f"Vector store addition failed: {e}")
            
            # Step 7: Store in database for BM25 retrieval
            self._store_document_chunks(document_id, chunk_documents, chunk_size=len(chunks))
            
            # Step 8: Update document record
            self._update_document_record(
                document_id=document_id,
                content_length=len(full_content),
                chunks_created=len(chunks),
                status="processed" if vector_success else "partial",
                vector_indexed=vector_success,
                learning_objectives=learning_objectives
            )
            
            # Step 9: Refresh BM25 retriever
            self.bm25_retriever = self._init_bm25_retriever()
            
            # Step 10: Return comprehensive result
            return {
                "document_id": document_id,
                "filename": filename,
                "content_length": len(full_content),
                "chunks_created": len(chunks),
                "learning_objectives": learning_objectives,
                "vector_indexed": {
                    "success": vector_success,
                    "vectors_created": vectors_created,
                    "index_name": "DocumentChunks"
                },
                "processing_details": {
                    "file_type": file_ext,
                    "loader_used": loader.__class__.__name__ if 'loader' in locals() else "text_fallback",
                    "chunk_size": 1000,
                    "chunk_overlap": 200
                },
                "status": "processed" if vector_success else "partial"
            }
            
        except Exception as e:
            self.logger.error(f"Error processing document: {e}")
            
            # Update document status to failed
            if 'document_id' in locals():
                self._update_document_status(document_id, "failed", str(e))
            
            return {
                "document_id": locals().get('document_id', -1),
                "filename": filename,
                "content_length": 0,
                "chunks_created": 0,
                "learning_objectives": [],
                "vector_indexed": {
                    "success": False,
                    "error": str(e)
                },
                "status": "failed"
            }
    
    def _read_file_with_fallback(self, file_path: str) -> str:
        """Read file with multiple encoding attempts"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        raise ValueError(f"Could not decode file with any encoding: {encodings}")
    
    def _store_document_chunks(self, document_id: int, chunk_documents: List[Document], chunk_size: int):
        """Store document chunks in database"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # First, store the full document content
                full_content = "\n\n".join([doc.page_content for doc in chunk_documents])
                cursor.execute("""
                    UPDATE documents 
                    SET raw_content = ?, metadata = ?
                    WHERE id = ?
                """, (full_content, json.dumps(chunk_documents[0].metadata), document_id))
                
                # Then store individual chunks
                for doc in chunk_documents:
                    cursor.execute("""
                        INSERT OR REPLACE INTO document_chunks 
                        (document_id, chunk_index, content, chunk_size, chunk_metadata)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        document_id,
                        doc.metadata.get('chunk_index', 0),
                        doc.page_content,
                        chunk_size,
                        json.dumps(doc.metadata)
                    ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error storing document chunks: {e}")
    
    def _insert_document_record(self, filename: str, file_ext: str) -> int:
        """Insert document record and return ID"""
        try:
            print("------- Inserting document record for", filename)
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO documents (filename, original_filename, file_type, file_size, upload_date, status, content_length, chunks_created)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (filename, filename, file_ext, 0, datetime.now(), "processing", 0, 0))
                
                document_id = cursor.lastrowid
                conn.commit()
                
                if document_id is None:
                    raise ValueError("Failed to get document ID after insertion")
                self.logger.info(f"Inserted document record with ID: {document_id}")
                return document_id
                
        except Exception as e:
            self.logger.error(f"Error inserting document record: {e}")
            raise
    
    def _update_document_record(self, document_id: int, content_length: int, 
                               chunks_created: int, status: str, vector_indexed: bool,
                               learning_objectives: List[str]):
        """Update document record with processing results"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE documents 
                    SET content_length = ?, chunks_created = ?, status = ?, 
                        vector_indexed = ?, processed_date = ?, learning_objectives = ?
                    WHERE id = ?
                """, (content_length, chunks_created, status, vector_indexed, 
                      datetime.now(), json.dumps(learning_objectives), document_id))
                
                conn.commit()
                self.logger.info(f"Updated document record ID: {document_id}")
                
        except Exception as e:
            self.logger.error(f"Error updating document record: {e}")
    
    def _update_document_status(self, document_id: int, status: str, error_message: str = None):
        """Update document status for error handling"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE documents 
                    SET status = ?, error_message = ?, processed_date = ?
                    WHERE id = ?
                """, (status, error_message, datetime.now(), document_id))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error updating document status: {e}")
    
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
                    metadata = {}
                    if row[1]:
                        try:
                            metadata = json.loads(row[1])
                        except:
                            metadata = {}
                    
                    doc = Document(
                        page_content=row[0],
                        metadata=metadata
                    )
                    documents.append(doc)
                
                return documents
        except Exception as e:
            self.logger.error(f"Error retrieving documents from database: {e}")
            return []
    
    # Keep all existing search, retrieval, and utility methods from original code
    def search(self, query: str, method: str = "hybrid", top_k: int = 5) -> List[Dict[str, Any]]:
        """Unified search method supporting multiple retrieval strategies"""
        try:
            results = []
            
            if method == "vector" and self.vector_store:
                docs = self.vector_store.similarity_search(query, k=top_k)
                results = self._format_search_results(docs, "vector")
                
            elif method == "bm25" and self.bm25_retriever:
                if self.bm25_retriever is None:
                    self.bm25_retriever = self._init_bm25_retriever()

                if self.bm25_retriever:   
                    docs = self.bm25_retriever.get_relevant_documents(query)[:top_k]
                    results = self._format_search_results(docs, "bm25")
                
            elif method == "hybrid":
                vector_results = []
                bm25_results = []
                
                if self.vector_store:
                    vector_docs = self.vector_store.similarity_search(query, k=top_k)
                    vector_results = self._format_search_results(vector_docs, "vector")

                if self.bm25_retriever is None:
                    self.bm25_retriever = self._init_bm25_retriever()
                    
                if self.bm25_retriever:
                    bm25_docs = self.bm25_retriever.get_relevant_documents(query)[:top_k]
                    bm25_results = self._format_search_results(bm25_docs, "bm25")
                
                results = self._combine_results(vector_results, bm25_results, top_k)
                
            else:
                results = self._database_search(query, top_k)
            
            if results:
                if self.reranker is None:
                    self.reranker = self._init_reranker()
                if self.reranker:
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
        """Combine and deduplicate results"""
        combined = {}
        
        for result in vector_results:
            content = result["content"]
            combined[content] = result
        
        for result in bm25_results:
            content = result["content"]
            if content not in combined:
                combined[content] = result
        
        sorted_results = sorted(combined.values(), key=lambda x: x.get("score", 0), reverse=True)
        return sorted_results[:top_k]
    
    def _database_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Fallback database search"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT content, chunk_metadata 
                    FROM document_chunks 
                    WHERE content LIKE ?
                    LIMIT ?
                """, (f"%{query}%", top_k))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "content": row[0],
                        "metadata": json.loads(row[1]) if row[1] else {},
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
            
            documents = []
            for result in results:
                doc = Document(
                    page_content=result["content"],
                    metadata=result["metadata"]
                )
                documents.append(doc)
            
            reranked_docs = self.reranker.compress_documents(documents, query)
            
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
            context_str = "\n\n".join([
                f"Document {i+1}: {doc['content']}"
                for i, doc in enumerate(context[:3])
            ])
            
            prompt = f"""Based on the following context, please answer the question. If the answer is not in the context, say "I don't have enough information to answer this question."

            Context:
            {context_str}

            Question: {query}

            Answer:"""
            
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            return "I apologize, but I encountered an error while generating the answer."
    
    def generate_quiz(self, topic: str, question_count: int = 5, difficulty: str = "medium") -> Dict[str, Any]:
        """Generate a quiz based on the given topic using hybrid RAG
        
        Args:
            topic: The topic for the quiz
            question_count: Number of questions to generate
            difficulty: Difficulty level (easy, medium, hard)
            
        Returns:
            Dictionary containing quiz data
        """
        # Check cache first if Redis is available
        if self.redis_client:
            cache_key = f"quiz:{topic}:{question_count}:{difficulty}"
            cached_quiz = self.redis_client.get(cache_key)
            if cached_quiz:
                try:
                    quiz_data = json.loads(cached_quiz)
                    quiz_data["cached"] = True
                    self.logger.info(f"Retrieved cached quiz for topic: {topic}")
                    return quiz_data
                except Exception as e:
                    self.logger.error(f"Error parsing cached quiz: {e}")
        
        # Retrieve relevant context using hybrid search
        search_results = self.search(
            query=f"educational content about {topic}",
            method="hybrid",
            top_k=10
        )
        
        # Extract content from search results
        context = [result["content"] for result in search_results]
        context_str = "\n\n".join(context)
        
        # Generate quiz using LLM
        difficulty_descriptions = {
            "easy": "basic understanding and recall of fundamental concepts",
            "medium": "application of concepts and some analysis",
            "hard": "advanced analysis, synthesis, and evaluation of complex concepts"
        }
        
        difficulty_desc = difficulty_descriptions.get(difficulty.lower(), difficulty_descriptions["medium"])
        
        # Define question types based on difficulty
        question_types = {
            "easy": ["multiple_choice", "true_false"],
            "medium": ["multiple_choice", "short_answer", "fill_in_blank"],
            "hard": ["multiple_choice", "short_answer", "essay"]
        }
        
        selected_types = question_types.get(difficulty.lower(), question_types["medium"])
        question_types_str = ", ".join(selected_types)
        
        prompt = f"""You are an expert educational assessment creator. Create a quiz on the topic of '{topic}' with {question_count} questions at {difficulty} difficulty level ({difficulty_desc}).

        Use the following educational content as reference:
        {context_str}

        Generate a quiz with the following requirements:
        1. Include {question_count} questions of these types: {question_types_str}
        2. For multiple-choice questions, provide 4 options with one correct answer
        3. For each question, include a detailed explanation of the correct answer
        4. For each question, include the source of information from the context
        5. Structure your response as a JSON object with the following format:

        {{
        "title": "Quiz title",
        "topic": "{topic}",
        "difficulty": "{difficulty}",
        "questions": [
            {{
            "id": 1,
            "type": "multiple_choice",
            "question": "Question text",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Correct option",
            "explanation": "Detailed explanation",
            "source": "Source from context"
            }},
            // Additional questions...
        ]
        }}

        Ensure the questions are directly based on the provided context and are appropriate for the {difficulty} difficulty level.
        """
        
        try:
            # Generate quiz using LLM
            response = self.llm.invoke(prompt)
            quiz_content = response.content
            
            # Parse JSON response
            try:
                quiz_data = json.loads(quiz_content)
            except json.JSONDecodeError:
                # Attempt to extract JSON if the response contains additional text
                import re
                json_match = re.search(r'(\{.*\})', quiz_content, re.DOTALL)
                if json_match:
                    quiz_data = json.loads(json_match.group(1))
                else:
                    raise ValueError("Failed to parse quiz data as JSON")
            
            # Add metadata
            quiz_data["cached"] = False
            quiz_data["generated_at"] = str(datetime.now())
            
            # Cache the result if Redis is available
            if self.redis_client:
                cache_key = f"quiz:{topic}:{question_count}:{difficulty}"
                self.redis_client.set(cache_key, json.dumps(quiz_data))
                # Set expiration (24 hours)
                self.redis_client.expire(cache_key, 86400)
                self.logger.info(f"Cached quiz for topic: {topic}")
            
            return quiz_data
            
        except Exception as e:
            self.logger.error(f"Error generating quiz: {e}")
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all components"""
        status = {
            "embeddings": bool(self.embeddings),
            "llm": bool(self.llm),
            "text_splitter": bool(self.text_splitter),
            "vector_store": bool(self.vector_store),
            # "bm25_retriever": bool(self.bm25_retriever),
            # "reranker": bool(self.reranker),
            "redis": bool(self.redis_client)
        }
        
        if self.vector_store:
            try:
                test_results = self.vector_store.similarity_search("test", k=1)
                status["weaviate_connection"] = True
            except Exception as e:
                status["weaviate_connection"] = False
                status["weaviate_error"] = str(e)
        
        return status