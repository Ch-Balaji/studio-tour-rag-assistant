"""
Advanced retrieval system with reranking and threshold tuning.
Implements a two-stage retrieval process: initial retrieval + reranking.
Supports hybrid search combining dense and sparse retrieval.
"""

from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import CrossEncoder
import numpy as np
from .bm25_index import BM25Index


class RAGRetriever:
    """Advanced retriever with reranking and hybrid search capabilities"""
    
    def __init__(
        self,
        vector_store,
        embedding_service,
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        use_reranking: bool = True,
        use_hybrid_search: bool = True,
        bm25_index_path: str = "./bm25_index"
    ):
        """
        Initialize the RAG retriever.
        
        Args:
            vector_store: ChromaDB client instance
            embedding_service: Embedding service instance
            reranker_model: Cross-encoder model for reranking
            use_reranking: Whether to use reranking
            use_hybrid_search: Whether to use hybrid search
            bm25_index_path: Path to BM25 index
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.use_reranking = use_reranking
        self.use_hybrid_search = use_hybrid_search
        
        if use_reranking:
            print(f"Loading reranker model: {reranker_model}")
            self.reranker = CrossEncoder(reranker_model)
        else:
            self.reranker = None
        
        # Initialize BM25 index for hybrid search
        if use_hybrid_search:
            self.bm25_index = BM25Index(persist_path=bm25_index_path)
        else:
            self.bm25_index = None
    
    def retrieve(
        self,
        query: str,
        initial_top_k: int = 25,
        final_top_n: int = 5,
        similarity_threshold: float = 0.3,
        filter_metadata: Dict[str, Any] = None,
        hybrid_alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks using hybrid search and two-stage retrieval.
        
        Args:
            query: Query text
            initial_top_k: Number of candidates for initial retrieval
            final_top_n: Final number of results after reranking
            similarity_threshold: Minimum similarity score to include
            filter_metadata: Optional metadata filters
            hybrid_alpha: Weight for dense retrieval (0=pure sparse, 1=pure dense)
            
        Returns:
            List of retrieved chunks with scores and metadata
        """
        if self.use_hybrid_search and self.bm25_index is not None:
            # Use hybrid search
            candidates = self._hybrid_retrieve(
                query, initial_top_k, similarity_threshold, filter_metadata, hybrid_alpha
            )
        else:
            # Use dense-only retrieval
            candidates = self._dense_retrieve(
                query, initial_top_k, similarity_threshold, filter_metadata
            )
        
        if not candidates:
            return []
        
        # Stage 2: Reranking (if enabled)
        if self.use_reranking and self.reranker is not None:
            candidates = self._rerank(query, candidates)
        
        # Return top N results
        final_results = candidates[:final_top_n]
        
        return final_results
    
    def _dense_retrieve(
        self,
        query: str,
        top_k: int,
        similarity_threshold: float,
        filter_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Dense retrieval using vector similarity"""
        query_embedding = self.embedding_service.embed_query(query)
        
        results = self.vector_store.query_collection(
            query_embedding=query_embedding.tolist(),
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        # Extract results
        candidates = []
        for i in range(len(results['ids'][0])):
            candidate = {
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i],
                'similarity': 1 - results['distances'][0][i],  # Convert distance to similarity
                'retrieval_method': 'dense'
            }
            candidates.append(candidate)
        
        # Filter by threshold
        candidates = [c for c in candidates if c['similarity'] >= similarity_threshold]
        
        return candidates
    
    def _hybrid_retrieve(
        self,
        query: str,
        top_k: int,
        similarity_threshold: float,
        filter_metadata: Dict[str, Any] = None,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval combining dense and sparse search.
        
        Args:
            query: Query text
            top_k: Number of candidates to retrieve
            similarity_threshold: Minimum similarity threshold
            filter_metadata: Optional metadata filters
            alpha: Weight for dense retrieval (0=pure sparse, 1=pure dense)
            
        Returns:
            Combined and reranked results
        """
        # Get dense results
        dense_results = self._dense_retrieve(query, top_k, 0.0, filter_metadata)  # No threshold yet
        
        # Get sparse results from BM25
        sparse_results = []
        bm25_results = self.bm25_index.search(query, top_k)
        
        if bm25_results:
            # Get document details for BM25 results
            indices = [idx for idx, _ in bm25_results]
            bm25_docs = self.bm25_index.get_documents_by_indices(indices)
            
            # Create candidate format for BM25 results
            for (idx, score), doc in zip(bm25_results, bm25_docs):
                # Try to find corresponding document in vector store
                # This assumes the BM25 index was built from the same documents
                sparse_results.append({
                    'id': doc.get('doc_id', str(idx)),
                    'text': doc['text'],
                    'metadata': {k: v for k, v in doc.items() if k not in ['text', 'doc_id']},
                    'bm25_score': score,
                    'retrieval_method': 'sparse'
                })
        
        # Combine results using reciprocal rank fusion
        combined_results = self._reciprocal_rank_fusion(
            dense_results, sparse_results, alpha
        )
        
        # Apply similarity threshold after fusion
        # Note: fusion scores are typically much smaller than similarity scores
        # So we apply threshold only to documents that have a similarity score
        if similarity_threshold > 0:
            combined_results = [
                r for r in combined_results 
                if r.get('similarity', 0) >= similarity_threshold or r.get('retrieval_method') == 'sparse'
            ]
        
        return combined_results
    
    def _reciprocal_rank_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        alpha: float = 0.5,
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Combine dense and sparse results using Reciprocal Rank Fusion.
        
        Args:
            dense_results: Results from dense retrieval
            sparse_results: Results from sparse retrieval
            alpha: Weight for dense retrieval
            k: Constant for RRF formula
            
        Returns:
            Combined and reranked results
        """
        # Create dictionaries to store scores by document text
        doc_scores = {}
        doc_data = {}
        
        # Process dense results
        for rank, result in enumerate(dense_results):
            doc_key = result['text'][:100]  # Use first 100 chars as key
            score = alpha / (k + rank + 1)
            
            if doc_key not in doc_scores:
                doc_scores[doc_key] = 0
                doc_data[doc_key] = result
            
            doc_scores[doc_key] += score
            # Store the best similarity score
            if 'similarity' in result:
                doc_data[doc_key]['similarity'] = max(
                    doc_data[doc_key].get('similarity', 0),
                    result['similarity']
                )
        
        # Process sparse results
        for rank, result in enumerate(sparse_results):
            doc_key = result['text'][:100]  # Use first 100 chars as key
            score = (1 - alpha) / (k + rank + 1)
            
            if doc_key not in doc_scores:
                doc_scores[doc_key] = 0
                doc_data[doc_key] = result
            
            doc_scores[doc_key] += score
            # Store BM25 score
            if 'bm25_score' in result:
                doc_data[doc_key]['bm25_score'] = result['bm25_score']
        
        # Create final results
        final_results = []
        for doc_key, fusion_score in doc_scores.items():
            result = doc_data[doc_key].copy()
            result['fusion_score'] = fusion_score
            result['retrieval_method'] = 'hybrid'
            final_results.append(result)
        
        # Sort by fusion score
        final_results.sort(key=lambda x: x['fusion_score'], reverse=True)
        
        return final_results
    
    def _rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rerank candidates using cross-encoder.
        
        Args:
            query: Query text
            candidates: List of candidate documents
            
        Returns:
            Reranked list of candidates
        """
        if not candidates:
            return candidates
        
        # Prepare pairs for reranking
        pairs = [(query, candidate['text']) for candidate in candidates]
        
        # Get reranking scores
        rerank_scores = self.reranker.predict(pairs)
        
        # Add rerank scores to candidates
        for candidate, score in zip(candidates, rerank_scores):
            candidate['rerank_score'] = float(score)
        
        # Sort by rerank score (descending)
        candidates.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        return candidates
    
    def retrieve_with_context(
        self,
        query: str,
        conversation_history: List[Dict[str, str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Retrieve with conversation context.
        Combines current query with recent conversation for better retrieval.
        
        Args:
            query: Current query
            conversation_history: List of previous messages
            **kwargs: Additional arguments for retrieve()
            
        Returns:
            List of retrieved chunks
        """
        # Enhance query with conversation context
        if conversation_history:
            # Take last few messages for context
            recent_messages = conversation_history[-3:]
            context_parts = [msg.get('content', '') for msg in recent_messages]
            context_parts.append(query)
            enhanced_query = ' '.join(context_parts)
        else:
            enhanced_query = query
        
        # Use original query for user-facing purposes but enhanced for retrieval
        return self.retrieve(enhanced_query, **kwargs)
    
    def format_context(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Format retrieved chunks into context string for LLM.
        
        Args:
            retrieved_chunks: List of retrieved chunk dictionaries
            
        Returns:
            Formatted context string
        """
        if not retrieved_chunks:
            return "No relevant context found."
        
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            metadata = chunk.get('metadata', {})
            source = metadata.get('source_file', 'Unknown')
            page = metadata.get('page_num', 'Unknown')
            
            context_parts.append(
                f"[Source {i}: {source}, Page {page}]\n{chunk['text']}\n"
            )
        
        return "\n".join(context_parts)

