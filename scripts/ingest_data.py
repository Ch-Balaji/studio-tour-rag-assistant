"""
Data ingestion pipeline for PDF documents.
Processes PDFs, creates chunks, generates embeddings, and stores in ChromaDB.
"""

import os
import sys
import argparse
import yaml
from pathlib import Path
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.chunking import chunk_document, ChunkingStrategy
from src.embeddings import EmbeddingService
from src.vector_store import ChromaDBClient
from src.retrieval import BM25Index


def load_config(config_path: str = "config/config.yaml"):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def ingest_documents(
    data_dir: str,
    chunking_strategy: ChunkingStrategy,
    config: dict,
    reset_db: bool = False
):
    """
    Main ingestion pipeline.
    
    Args:
        data_dir: Directory containing PDF files
        chunking_strategy: Strategy to use for chunking
        config: Configuration dictionary
        reset_db: Whether to reset the database before ingesting
    """
    print("=" * 80)
    print("Silverlight Studios RAG - Data Ingestion Pipeline")
    print("=" * 80)
    
    # Initialize services
    print("\n1. Initializing services...")
    
    embedding_service = EmbeddingService(
        model_name=config['embeddings']['model_name'],
        device=config['embeddings']['device'],
        batch_size=config['embeddings']['batch_size']
    )
    
    vector_store = ChromaDBClient(
        persist_directory=config['vector_db']['persist_directory'],
        collection_name=config['vector_db']['collection_name']
    )
    
    if reset_db:
        print("\n2. Resetting vector database...")
        vector_store.reset_collection()
    
    # Find PDF files
    print(f"\n3. Scanning for PDF files in: {data_dir}")
    pdf_files = list(Path(data_dir).glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {data_dir}")
        return
    
    print(f"Found {len(pdf_files)} PDF files:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")
    
    # Process each PDF
    print(f"\n4. Processing PDFs with {chunking_strategy.value} chunking...")
    
    all_chunks = []
    
    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")
        
        # Get chunking parameters based on strategy
        if chunking_strategy == ChunkingStrategy.FIXED:
            chunk_params = config['chunking']['fixed']
        elif chunking_strategy == ChunkingStrategy.RECURSIVE:
            chunk_params = config['chunking']['recursive']
        elif chunking_strategy == ChunkingStrategy.SEMANTIC:
            chunk_params = config['chunking']['semantic']
            # Add embedding model for semantic chunking
            chunk_params['embedding_model'] = embedding_service.model
        elif chunking_strategy == ChunkingStrategy.HYBRID:
            chunk_params = config['chunking']['hybrid']
            # Add embedding model for hybrid chunking
            chunk_params['embedding_model'] = embedding_service.model
        else:
            chunk_params = {}
        
        # Chunk the document with metadata enrichment
        chunks = chunk_document(
            str(pdf_file),
            strategy=chunking_strategy,
            enrich_metadata=True,
            **chunk_params
        )
        
        print(f"  Created {len(chunks)} chunks")
        all_chunks.extend(chunks)
    
    print(f"\nTotal chunks created: {len(all_chunks)}")
    
    # Generate embeddings
    print("\n5. Generating embeddings...")
    chunk_texts = [chunk['text'] for chunk in all_chunks]
    
    embeddings = []
    batch_size = config['embeddings']['batch_size']
    
    for i in tqdm(range(0, len(chunk_texts), batch_size), desc="Embedding batches"):
        batch = chunk_texts[i:i + batch_size]
        batch_embeddings = embedding_service.embed_texts(batch)
        embeddings.extend(batch_embeddings.tolist())
    
    print(f"Generated {len(embeddings)} embeddings")
    
    # Ingest into vector store
    print("\n6. Ingesting into ChromaDB...")
    vector_store.ingest_chunks(all_chunks, embeddings)
    
    # Show statistics
    print("\n7. Ingestion complete!")
    stats = vector_store.get_collection_stats()
    print(f"\nVector Store Statistics:")
    print(f"  Collection: {stats['collection_name']}")
    print(f"  Total Documents: {stats['document_count']}")
    print(f"  Storage Location: {stats['persist_directory']}")
    
    # Build BM25 index for hybrid search
    print("\n8. Building BM25 index for hybrid search...")
    bm25_index = BM25Index()
    bm25_index.build_index(all_chunks)
    
    print("\n" + "=" * 80)
    print("Ingestion pipeline completed successfully!")
    print("=" * 80)


def main():
    """Main entry point for the ingestion script"""
    parser = argparse.ArgumentParser(
        description="Ingest PDF documents into ChromaDB for RAG"
    )
    
    parser.add_argument(
        '--data-dir',
        type=str,
        default='data',
        help='Directory containing PDF files'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--chunking-strategy',
        type=str,
        choices=['fixed', 'recursive', 'semantic', 'hybrid'],
        default='recursive',
        help='Chunking strategy to use'
    )
    
    parser.add_argument(
        '--reset-db',
        action='store_true',
        help='Reset the vector database before ingesting'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Convert strategy string to enum
    strategy = ChunkingStrategy(args.chunking_strategy)
    
    # Run ingestion
    try:
        ingest_documents(
            data_dir=args.data_dir,
            chunking_strategy=strategy,
            config=config,
            reset_db=args.reset_db
        )
    except Exception as e:
        print(f"\nError during ingestion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

