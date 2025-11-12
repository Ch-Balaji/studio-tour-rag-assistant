"""
ChromaDB client for vector storage and retrieval.
Handles ingestion and querying of document chunks with metadata.
"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import uuid


class ChromaDBClient:
    """Client for interacting with ChromaDB vector database"""
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "silverlight_studios_rag"
    ):
        """
        Initialize ChromaDB client.
        
        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the collection to use
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        print(f"ChromaDB initialized with collection: {collection_name}")
        print(f"Current document count: {self.collection.count()}")
    
    def ingest_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]] = None
    ) -> None:
        """
        Ingest chunks into ChromaDB with metadata.
        Handles batching to avoid exceeding ChromaDB's batch size limits.
        
        Args:
            chunks: List of chunk dictionaries with text and metadata
            embeddings: Optional pre-computed embeddings (if None, ChromaDB will generate)
        """
        if not chunks:
            print("No chunks to ingest")
            return
        
        # ChromaDB batch size limit (use conservative value)
        BATCH_SIZE = 5000
        
        total_chunks = len(chunks)
        print(f"Ingesting {total_chunks} chunks in batches of {BATCH_SIZE}...")
        
        for batch_start in range(0, total_chunks, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_chunks)
            batch_chunks = chunks[batch_start:batch_end]
            
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            batch_embeddings = None
            
            for i, chunk in enumerate(batch_chunks):
                # Generate unique ID
                chunk_id = str(uuid.uuid4())
                ids.append(chunk_id)
                
                # Extract text
                documents.append(chunk["text"])
                
                # Extract metadata (exclude text field)
                metadata = {k: v for k, v in chunk.items() if k != "text"}
                # Convert all metadata values to strings for ChromaDB compatibility
                metadata = {k: str(v) for k, v in metadata.items()}
                metadatas.append(metadata)
            
            # Get embeddings for this batch
            if embeddings is not None:
                batch_embeddings = embeddings[batch_start:batch_end]
            
            # Add to collection
            try:
                if batch_embeddings is not None:
                    self.collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas,
                        embeddings=batch_embeddings
                    )
                else:
                    self.collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas
                    )
                
                print(f"  Batch {batch_start}-{batch_end}: Ingested {len(batch_chunks)} chunks")
                
            except Exception as e:
                print(f"  Error ingesting batch {batch_start}-{batch_end}: {e}")
                raise
        
        print(f"✓ Successfully ingested {total_chunks} chunks into ChromaDB")
        print(f"Total documents in collection: {self.collection.count()}")
    
    def query_collection(
        self,
        query_text: str = None,
        query_embedding: List[float] = None,
        top_k: int = 10,
        filter_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Query the collection for similar documents.
        
        Args:
            query_text: Query text (used if query_embedding is None)
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            Dictionary with ids, documents, metadatas, and distances
        """
        if query_embedding is None and query_text is None:
            raise ValueError("Either query_text or query_embedding must be provided")
        
        query_kwargs = {
            "n_results": top_k,
        }
        
        if filter_metadata:
            # Convert filter values to strings for ChromaDB
            filter_metadata = {k: str(v) for k, v in filter_metadata.items()}
            query_kwargs["where"] = filter_metadata
        
        if query_embedding is not None:
            query_kwargs["query_embeddings"] = [query_embedding]
        else:
            query_kwargs["query_texts"] = [query_text]
        
        results = self.collection.query(**query_kwargs)
        
        return results
    
    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        """
        Retrieve documents by their IDs.
        
        Args:
            ids: List of document IDs
            
        Returns:
            Dictionary with documents and metadata
        """
        return self.collection.get(ids=ids)
    
    def reset_collection(self) -> None:
        """Delete and recreate the collection"""
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            print(f"Collection doesn't exist or error deleting: {e}")
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"Created new collection: {self.collection_name}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "persist_directory": self.persist_directory
        }

