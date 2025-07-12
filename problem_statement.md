# Automated Quiz Generator

## Problem Statement

Create an advanced assessment generation system that can create personalized quizzes, assignments, and tests based on educational content. The instructor should be able to upload educational docs based on the topics he has taught. The system should understand learning objectives, difficulty levels, and generate diverse question types with proper explanations.

## Requirements

- Implement Hybrid RAG combining dense and sparse retrieval methods
- Add Advanced Reranking using cross-encoder models
- Implement Contextual Compression with dynamic chunk sizing
- Add a Caching layer using Redis for frequently accessed content
- Combine dense embeddings (sentence-transformers) with sparse retrieval (BM25)
- Use cross-encoder models for sophisticated reranking
- Implement Redis caching for:
  - Frequently accessed document chunks
  - Generated assessments
  - User preferences and history
- Integrate tool calling for:
  - Educational content APIs
  - Dynamic difficulty adjustment based on user performance

## Expected Deliverables

- Hybrid RAG implementation
- Redis caching layer
- Tool calling integration
- Advanced reranking system
- Demo with educational content
