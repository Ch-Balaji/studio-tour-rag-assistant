"""
Chunking strategies for text processing in RAG pipeline.
Supports fixed, recursive, and semantic chunking methods.
"""

from typing import List, Dict, Any
from enum import Enum
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.metadata import MetadataExtractor


class ChunkingStrategy(str, Enum):
    """Enum for different chunking strategies"""
    FIXED = "fixed"
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


def extract_text_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract text from PDF with page-level metadata.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries containing page text and metadata
    """
    doc = fitz.open(pdf_path)
    pages = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        pages.append({
            "text": text,
            "page_num": page_num + 1,
            "source_file": pdf_path.split("/")[-1]
        })
    
    doc.close()
    return pages


def fixed_chunking(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Fixed-size chunking with overlap.
    
    Args:
        text: Input text to chunk
        chunk_size: Size of each chunk in characters
        chunk_overlap: Overlap between consecutive chunks
        metadata: Additional metadata to attach to chunks
        
    Returns:
        List of chunk dictionaries with text and metadata
    """
    chunks = []
    start = 0
    chunk_id = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]
        
        chunk_data = {
            "text": chunk_text,
            "chunk_id": chunk_id,
            "chunk_method": ChunkingStrategy.FIXED.value,
            "start_char": start,
            "end_char": end
        }
        
        if metadata:
            chunk_data.update(metadata)
        
        chunks.append(chunk_data)
        chunk_id += 1
        start += (chunk_size - chunk_overlap)
    
    return chunks


def recursive_chunking(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    separators: List[str] = None,
    metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Recursive chunking using LangChain's RecursiveCharacterTextSplitter.
    Attempts to split on natural boundaries (paragraphs, sentences, words).
    
    Args:
        text: Input text to chunk
        chunk_size: Target size of each chunk
        chunk_overlap: Overlap between chunks
        separators: List of separators to try in order
        metadata: Additional metadata to attach to chunks
        
    Returns:
        List of chunk dictionaries with text and metadata
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", " ", ""]
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        length_function=len
    )
    
    text_chunks = splitter.split_text(text)
    
    chunks = []
    for chunk_id, chunk_text in enumerate(text_chunks):
        chunk_data = {
            "text": chunk_text,
            "chunk_id": chunk_id,
            "chunk_method": ChunkingStrategy.RECURSIVE.value
        }
        
        if metadata:
            chunk_data.update(metadata)
        
        chunks.append(chunk_data)
    
    return chunks


def semantic_chunking(
    text: str,
    embedding_model: SentenceTransformer = None,
    buffer_size: int = 1,
    breakpoint_threshold: float = 0.5,
    metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Semantic chunking based on sentence similarity.
    Groups sentences together based on semantic similarity.
    
    Args:
        text: Input text to chunk
        embedding_model: Sentence transformer model for embeddings
        buffer_size: Number of sentences to combine for comparison
        breakpoint_threshold: Similarity threshold for creating breakpoints
        metadata: Additional metadata to attach to chunks
        
    Returns:
        List of chunk dictionaries with text and metadata
    """
    if embedding_model is None:
        embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    # Split into sentences
    sentences = text.replace('\n', ' ').split('. ')
    sentences = [s.strip() + '.' for s in sentences if s.strip()]
    
    if len(sentences) <= 1:
        return [{
            "text": text,
            "chunk_id": 0,
            "chunk_method": ChunkingStrategy.SEMANTIC.value,
            **(metadata or {})
        }]
    
    # Create sentence groups for comparison
    sentence_groups = []
    for i in range(len(sentences)):
        group_start = max(0, i - buffer_size)
        group_end = min(len(sentences), i + buffer_size + 1)
        group = ' '.join(sentences[group_start:group_end])
        sentence_groups.append(group)
    
    # Generate embeddings
    embeddings = embedding_model.encode(sentence_groups)
    
    # Calculate similarities between consecutive groups
    similarities = []
    for i in range(len(embeddings) - 1):
        similarity = np.dot(embeddings[i], embeddings[i + 1]) / (
            np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i + 1])
        )
        similarities.append(similarity)
    
    # Find breakpoints where similarity drops below threshold
    breakpoints = [0]
    for i, sim in enumerate(similarities):
        if sim < breakpoint_threshold:
            breakpoints.append(i + 1)
    breakpoints.append(len(sentences))
    
    # Create chunks based on breakpoints
    chunks = []
    for chunk_id, i in enumerate(range(len(breakpoints) - 1)):
        start_idx = breakpoints[i]
        end_idx = breakpoints[i + 1]
        chunk_text = ' '.join(sentences[start_idx:end_idx])
        
        chunk_data = {
            "text": chunk_text,
            "chunk_id": chunk_id,
            "chunk_method": ChunkingStrategy.SEMANTIC.value,
            "sentence_start": start_idx,
            "sentence_end": end_idx
        }
        
        if metadata:
            chunk_data.update(metadata)
        
        chunks.append(chunk_data)
    
    return chunks


def hybrid_chunking(
    text: str,
    min_size: int = 256,
    max_size: int = 768,
    chunk_overlap: int = 50,
    embedding_model: SentenceTransformer = None,
    metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Hybrid chunking that combines semantic boundaries with size constraints.
    Uses semantic similarity to find natural breakpoints while ensuring chunks
    stay within size limits.
    
    Args:
        text: Input text to chunk
        min_size: Minimum chunk size in characters
        max_size: Maximum chunk size in characters
        chunk_overlap: Overlap between chunks
        embedding_model: Sentence transformer model for embeddings
        metadata: Additional metadata to attach to chunks
        
    Returns:
        List of chunk dictionaries with text and metadata
    """
    if embedding_model is None:
        embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    # First, use semantic chunking to find natural boundaries
    semantic_chunks = semantic_chunking(
        text, 
        embedding_model=embedding_model,
        buffer_size=1,
        breakpoint_threshold=0.4,  # Lower threshold for more breakpoints
        metadata=metadata
    )
    
    # Now, combine or split semantic chunks to meet size constraints
    final_chunks = []
    current_chunk = ""
    current_start = 0
    chunk_id = 0
    
    for sc in semantic_chunks:
        chunk_text = sc['text']
        
        # If adding this chunk would exceed max_size, save current and start new
        if current_chunk and len(current_chunk) + len(chunk_text) > max_size:
            # Save current chunk if it meets min size
            if len(current_chunk) >= min_size:
                chunk_data = {
                    "text": current_chunk,
                    "chunk_id": chunk_id,
                    "chunk_method": ChunkingStrategy.HYBRID.value,
                    "start_char": current_start,
                    "end_char": current_start + len(current_chunk)
                }
                if metadata:
                    chunk_data.update(metadata)
                final_chunks.append(chunk_data)
                chunk_id += 1
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk) - chunk_overlap)
                current_chunk = current_chunk[overlap_start:] + chunk_text
                current_start = current_start + overlap_start
            else:
                # Current chunk too small, add anyway
                current_chunk += " " + chunk_text
        elif len(chunk_text) > max_size:
            # Single semantic chunk exceeds max size, need to split it
            # First save any accumulated chunk
            if current_chunk and len(current_chunk) >= min_size:
                chunk_data = {
                    "text": current_chunk,
                    "chunk_id": chunk_id,
                    "chunk_method": ChunkingStrategy.HYBRID.value,
                    "start_char": current_start,
                    "end_char": current_start + len(current_chunk)
                }
                if metadata:
                    chunk_data.update(metadata)
                final_chunks.append(chunk_data)
                chunk_id += 1
                current_chunk = ""
            
            # Split the large chunk
            sub_chunks = fixed_chunking(
                chunk_text,
                chunk_size=max_size,
                chunk_overlap=chunk_overlap,
                metadata=metadata
            )
            
            for sub in sub_chunks:
                sub['chunk_id'] = chunk_id
                sub['chunk_method'] = ChunkingStrategy.HYBRID.value
                final_chunks.append(sub)
                chunk_id += 1
            
            current_chunk = ""
            current_start = current_start + len(chunk_text)
        else:
            # Add to current chunk
            if current_chunk:
                current_chunk += " " + chunk_text
            else:
                current_chunk = chunk_text
    
    # Don't forget the last chunk
    if current_chunk and len(current_chunk) >= min_size:
        chunk_data = {
            "text": current_chunk,
            "chunk_id": chunk_id,
            "chunk_method": ChunkingStrategy.HYBRID.value,
            "start_char": current_start,
            "end_char": current_start + len(current_chunk)
        }
        if metadata:
            chunk_data.update(metadata)
        final_chunks.append(chunk_data)
    
    return final_chunks


def chunk_document(
    pdf_path: str,
    strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
    enrich_metadata: bool = True,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Complete document chunking pipeline with metadata enrichment.
    
    Args:
        pdf_path: Path to PDF file
        strategy: Chunking strategy to use
        enrich_metadata: Whether to extract additional metadata
        **kwargs: Additional arguments for chunking functions
        
    Returns:
        List of all chunks with metadata
    """
    pages = extract_text_from_pdf(pdf_path)
    all_chunks = []
    
    # Initialize metadata extractor if needed
    metadata_extractor = MetadataExtractor() if enrich_metadata else None
    
    for page_data in pages:
        text = page_data["text"]
        metadata = {
            "page_num": page_data["page_num"],
            "source_file": page_data["source_file"]
        }
        
        if strategy == ChunkingStrategy.FIXED:
            chunks = fixed_chunking(text, metadata=metadata, **kwargs)
        elif strategy == ChunkingStrategy.RECURSIVE:
            chunks = recursive_chunking(text, metadata=metadata, **kwargs)
        elif strategy == ChunkingStrategy.SEMANTIC:
            chunks = semantic_chunking(text, metadata=metadata, **kwargs)
        elif strategy == ChunkingStrategy.HYBRID:
            chunks = hybrid_chunking(text, metadata=metadata, **kwargs)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
        
        # Enrich metadata for each chunk
        if enrich_metadata and metadata_extractor:
            for chunk in chunks:
                # Extract additional metadata
                extra_metadata = metadata_extractor.extract_all_metadata(
                    chunk['text'], 
                    page_data["source_file"]
                )
                # Merge with existing metadata
                chunk.update(extra_metadata)
        
        all_chunks.extend(chunks)
    
    return all_chunks

