"""
RAG Service wrapper around existing components
"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Generator
import logging

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.embeddings import EmbeddingService
from src.vector_store import ChromaDBClient
from src.retrieval import RAGRetriever
from src.llm import OllamaClient
from src.llm.groq_client import GroqClient
from src.chat import MemoryManager
from src.query import QueryEnhancer

logger = logging.getLogger(__name__)


class RAGService:
    """Service wrapper for RAG functionality"""
    
    def __init__(self, config):
        """
        Initialize RAG service with all components
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # Initialize embedding service
        self.embedding_service = EmbeddingService(
            model_name=config.embeddings_config['model_name'],
            device=config.embeddings_config['device'],
            batch_size=config.embeddings_config['batch_size']
        )
        
        # Initialize vector store
        self.vector_store = ChromaDBClient(
            persist_directory=config.vector_db_config['persist_directory'],
            collection_name=config.vector_db_config['collection_name']
        )
        
        # Initialize retriever with hybrid search
        self.retriever = RAGRetriever(
            vector_store=self.vector_store,
            embedding_service=self.embedding_service,
            reranker_model=config.retrieval_config['reranker_model'],
            use_reranking=config.retrieval_config['use_reranking'],
            use_hybrid_search=True,
            bm25_index_path=str(config.bm25_index_path)
        )
        
        # Initialize LLM based on provider
        llm_provider = config.llm_provider
        
        if llm_provider == "groq":
            logger.info("Using Groq API for LLM (fast inference)")
            self.llm_client = GroqClient(
                api_key=config.groq_api_key,
                model_name="llama-3.1-8b-instant",
                temperature=config.llm_config['temperature'],
                max_tokens=config.llm_config['max_tokens']
            )
        else:  # Default to ollama
            logger.info("Using local Ollama for LLM")
            self.llm_client = OllamaClient(
                model_name=config.llm_config['model_name'],
                base_url=config.llm_config['base_url'],
                temperature=config.llm_config['temperature'],
                max_tokens=config.llm_config['max_tokens']
            )
        
        # Initialize query enhancer
        self.query_enhancer = QueryEnhancer()
        
        logger.info("RAG Service initialized successfully")
    
    def check_health(self) -> Dict[str, bool]:
        """Check health of services"""
        return {
            "llm_connected": self.llm_client.check_connection(),
            "llm_provider": self.config.llm_provider,
            "vector_store_loaded": self.vector_store.get_collection_stats()['document_count'] > 0
        }
    
    def create_memory_manager(self, max_turns: int = None) -> MemoryManager:
        """Create a new memory manager instance for a session"""
        if max_turns is None:
            max_turns = self.config.memory_config.get('k', 5)
        return MemoryManager(max_turns=max_turns)
    
    def enhance_query(self, query: str) -> str:
        """Enhance query using query enhancer"""
        return self.query_enhancer.enhance_query(query)
    
    def retrieve_context(
        self,
        query: str,
        initial_top_k: int = 25,
        final_top_n: int = 5,
        similarity_threshold: float = 0.3,
        use_reranking: bool = True,
        hybrid_alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for query
        
        Args:
            query: User query
            initial_top_k: Initial retrieval size
            final_top_n: Final number of results after reranking
            similarity_threshold: Minimum similarity score
            use_reranking: Whether to use reranking
            hybrid_alpha: Weight for hybrid search (0=keyword, 1=semantic)
        
        Returns:
            List of retrieved chunks with metadata
        """
        # Update retriever settings
        self.retriever.use_reranking = use_reranking
        self.retriever.use_hybrid_search = True
        
        # Retrieve chunks
        chunks = self.retriever.retrieve(
            query=query,
            initial_top_k=initial_top_k,
            final_top_n=final_top_n,
            similarity_threshold=similarity_threshold,
            hybrid_alpha=hybrid_alpha
        )
        
        return chunks
    
    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into context string"""
        return self.retriever.format_context(chunks)
    
    def generate_response(
        self,
        query: str,
        context: str,
        chat_history: List[Dict[str, str]],
        citation_style: str = "clean"
    ) -> str:
        """
        Generate non-streaming response
        
        Args:
            query: User query
            context: Retrieved context
            chat_history: Conversation history
            citation_style: Citation style to use
        
        Returns:
            Generated response
        """
        self.llm_client.set_citation_style(citation_style)
        
        response = ""
        for chunk in self.llm_client.generate_response_stream(
            query=query,
            context=context,
            chat_history=chat_history
        ):
            response += chunk
        
        return response
    
    def generate_response_stream(
        self,
        query: str,
        context: str,
        chat_history: List[Dict[str, str]],
        citation_style: str = "clean"
    ) -> Generator[str, None, None]:
        """
        Generate streaming response
        
        Args:
            query: User query
            context: Retrieved context
            chat_history: Conversation history
            citation_style: Citation style to use
        
        Yields:
            Response chunks
        """
        self.llm_client.set_citation_style(citation_style)
        
        for chunk in self.llm_client.generate_response_stream(
            query=query,
            context=context,
            chat_history=chat_history
        ):
            yield chunk
    
    def generate_suggested_questions(
        self,
        response: str,
        chunks: List[Dict[str, Any]],
        num_questions: int = 3
    ) -> List[str]:
        """
        Generate suggested follow-up questions based on response and retrieved chunks
        
        Args:
            response: The generated response
            chunks: Retrieved chunks from RAG
            num_questions: Number of questions to generate
            
        Returns:
            List of suggested questions
        """
        try:
            # Extract key information from chunks
            chunk_contents = []
            chunk_topics = set()
            
            for chunk in chunks[:5]:  # Use top 5 chunks for question generation
                content = chunk.get('content', '')
                metadata = chunk.get('metadata', {})
                
                # Add chunk content
                chunk_contents.append(content[:300])  # First 300 chars of each chunk
                
                # Extract topics from metadata if available
                if 'topic' in metadata:
                    chunk_topics.add(metadata['topic'])
                if 'title' in metadata:
                    chunk_topics.add(metadata['title'])
            
            # Create context for question generation
            chunks_summary = "\n".join([f"- {content}" for content in chunk_contents])
            
            # Create prompt for generating questions
            prompt = f"""Based on the following information from the documentation, generate {num_questions} detailed follow-up questions that users might ask.

Current response summary:
{response[:500]}...

Related content from documentation:
{chunks_summary}

Requirements for questions:
1. Each question should be 10-20 words long (detailed and specific)
2. Questions should explore different aspects found in the documentation chunks
3. Questions must be answerable from the provided documentation
4. Focus on practical information users would want to know
5. Make questions diverse - covering different topics from the chunks

Generate exactly {num_questions} questions, one per line, without numbering or bullet points."""

            # Generate questions using LLM
            questions_response = ""
            for chunk in self.llm_client.generate_response_stream(
                query=prompt,
                context="",  # No additional context needed
                chat_history=[]
            ):
                questions_response += chunk
            
            # Parse questions from response
            questions = []
            for line in questions_response.strip().split('\n'):
                line = line.strip()
                # Remove any numbering or bullet points
                line = line.lstrip('0123456789.-) ')
                if line and len(line) > 20:  # Ensure minimum length
                    questions.append(line)
            
            # Ensure we have the requested number of questions
            if len(questions) < num_questions:
                # Add some fallback questions based on chunk content
                fallback_prompts = [
                    "What specific details about",
                    "Can you explain more about",
                    "What are the requirements for",
                    "How does the process work for",
                    "What should visitors know about"
                ]
                
                for i in range(len(questions), num_questions):
                    if chunk_topics:
                        topic = list(chunk_topics)[i % len(chunk_topics)]
                        questions.append(f"{fallback_prompts[i % len(fallback_prompts)]} {topic}?")
                    else:
                        questions.append(f"Can you provide more information about the topics mentioned above?")
            
            # Return exactly the requested number of questions
            return questions[:num_questions]
            
        except Exception as e:
            logger.error(f"Error generating suggested questions: {e}")
            # Return fallback questions on error
            return [
                "What are the specific requirements and restrictions for this service?",
                "Can you provide more details about the process and availability?",
                "What additional features or options are available?"
            ]

