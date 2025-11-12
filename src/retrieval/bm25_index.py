"""
BM25 index for sparse retrieval in hybrid search.
"""

from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
import pickle
import os
from pathlib import Path
import numpy as np


class BM25Index:
    """BM25 index for sparse text retrieval"""
    
    def __init__(self, persist_path: str = "./bm25_index"):
        """
        Initialize BM25 index.
        
        Args:
            persist_path: Path to persist the index
        """
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        
        self.bm25 = None
        self.documents = []
        self.doc_ids = []
        self.metadata = []
        
        # Try to load existing index
        self._load_index()
    
    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Build BM25 index from chunks.
        
        Args:
            chunks: List of chunks with 'text' and metadata
        """
        print("Building BM25 index...")
        
        # Extract documents and metadata
        self.documents = []
        self.doc_ids = []
        self.metadata = []
        
        for i, chunk in enumerate(chunks):
            text = chunk.get('text', '')
            # Tokenize for BM25 (simple whitespace tokenization)
            tokenized_text = text.lower().split()
            
            self.documents.append(tokenized_text)
            self.doc_ids.append(str(i))  # Use index as ID
            self.metadata.append({k: v for k, v in chunk.items() if k != 'text'})
        
        # Build BM25 index
        self.bm25 = BM25Okapi(self.documents)
        
        # Save index
        self._save_index()
        
        print(f"BM25 index built with {len(self.documents)} documents")
    
    def search(self, query: str, top_k: int = 25) -> List[Tuple[int, float]]:
        """
        Search using BM25.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (doc_index, score) tuples
        """
        if self.bm25 is None:
            print("BM25 index not built")
            return []
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        # Return indices with scores
        results = [(int(idx), float(scores[idx])) for idx in top_indices if scores[idx] > 0]
        
        return results
    
    def get_documents_by_indices(self, indices: List[int]) -> List[Dict[str, Any]]:
        """
        Get documents by their indices.
        
        Args:
            indices: List of document indices
            
        Returns:
            List of documents with metadata
        """
        results = []
        
        for idx in indices:
            if 0 <= idx < len(self.documents):
                # Reconstruct the document
                doc = {
                    'text': ' '.join(self.documents[idx]),
                    'doc_id': self.doc_ids[idx],
                    **self.metadata[idx]
                }
                results.append(doc)
        
        return results
    
    def _save_index(self) -> None:
        """Save BM25 index to disk"""
        index_data = {
            'documents': self.documents,
            'doc_ids': self.doc_ids,
            'metadata': self.metadata,
            'bm25_params': {
                'k1': self.bm25.k1 if self.bm25 else 1.2,
                'b': self.bm25.b if self.bm25 else 0.75,
                'epsilon': self.bm25.epsilon if self.bm25 else 0.25
            }
        }
        
        index_file = self.persist_path / "bm25_index.pkl"
        with open(index_file, 'wb') as f:
            pickle.dump(index_data, f)
        
        print(f"BM25 index saved to {index_file}")
    
    def _load_index(self) -> bool:
        """Load BM25 index from disk"""
        index_file = self.persist_path / "bm25_index.pkl"
        
        if not index_file.exists():
            return False
        
        try:
            with open(index_file, 'rb') as f:
                index_data = pickle.load(f)
            
            self.documents = index_data['documents']
            self.doc_ids = index_data['doc_ids']
            self.metadata = index_data['metadata']
            
            # Rebuild BM25 with saved parameters
            if self.documents:
                params = index_data.get('bm25_params', {})
                self.bm25 = BM25Okapi(
                    self.documents,
                    k1=params.get('k1', 1.2),
                    b=params.get('b', 0.75),
                    epsilon=params.get('epsilon', 0.25)
                )
                print(f"BM25 index loaded with {len(self.documents)} documents")
                return True
        except Exception as e:
            print(f"Error loading BM25 index: {e}")
        
        return False
    
    def clear_index(self) -> None:
        """Clear the BM25 index"""
        self.bm25 = None
        self.documents = []
        self.doc_ids = []
        self.metadata = []
        
        # Remove saved index
        index_file = self.persist_path / "bm25_index.pkl"
        if index_file.exists():
            index_file.unlink()
        
        print("BM25 index cleared")
