"""
Groq LLM client for ultra-fast inference.
Provides streaming response generation using Groq API.
"""

from typing import Dict, List, Iterator, Optional
import os


class GroqClient:
    """Client for interacting with Groq API for fast LLM inference"""
    
    def __init__(
        self,
        api_key: str = None,
        model_name: str = "llama-3.1-8b-instant",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        citation_style: str = "clean"
    ):
        """
        Initialize Groq client.
        
        Args:
            api_key: Groq API key (uses env var if not provided)
            model_name: Name of the Groq model
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            citation_style: Style for citations ("clean", "none")
        """
        try:
            from groq import Groq
        except ImportError:
            raise ImportError("groq package is required. Install with: pip install groq")
        
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key not found. Set GROQ_API_KEY environment variable.")
        
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.citation_style = citation_style
        
        # Initialize Groq client
        self.client = Groq(api_key=self.api_key)
        
        print(f"Groq client initialized with model: {model_name}")
    
    def _get_system_prompt(self, context: str) -> str:
        """Get the system prompt for RAG based on citation style"""
        if self.citation_style == "none":
            return f"""You are a helpful AI assistant with access to information from documents. 
Your task is to answer questions based on the provided context.

Guidelines:
1. Use the context provided to answer questions accurately
2. Write in a natural, conversational style
3. Do NOT include any citations or source references in your response
4. If the context doesn't contain relevant information, say so honestly
5. Answer based solely on the provided context - do not make up information

Context:
{context}

Answer the following question based on the context above in a natural way without any citations."""
        
        else:  # "clean" style (default)
            return f"""You are a knowledgeable assistant for Silverlight Studios with access to production documents.

CRITICAL RULES:
1. Answer questions DIRECTLY and NATURALLY using ONLY information from the context below
2. DO NOT start with phrases like "According to the documents" or "Based on the context" - just answer naturally
3. NEVER use your general knowledge or training data - ONLY use the context provided
4. If the context has the information, answer confidently and naturally
5. SYNTHESIZE and CONNECT information from multiple sources when relevant
6. Use [1], [2], etc. for citations at the end of relevant sentences
7. Include a "Sources:" section at the end listing all citations
8. ONLY if the context truly doesn't have relevant information, say: "I don't have information about that in the available documents."

Write in a clear, professional, conversational style - as if you're an expert who has this information memorized.

The context below contains excerpts labeled as [Source N: filename, Page X].
Cite these as [1], [2], etc.

Context:
{context}

Answer naturally and directly. Don't mention "the context" or "the documents" unless the information is missing."""
    
    def generate_response(
        self,
        query: str,
        context: str = "",
        chat_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate a response using Groq API.
        
        Args:
            query: User query
            context: Retrieved context from RAG
            chat_history: Conversation history
            
        Returns:
            Generated response
        """
        # Prepare messages
        messages = [
            {"role": "system", "content": self._get_system_prompt(context)}
        ]
        
        # Add chat history
        if chat_history:
            for msg in chat_history:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Generate response (non-streaming)
        try:
            response = ""
            for chunk in self.generate_response_stream(query, context, chat_history):
                response += chunk
            return response
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def generate_response_stream(
        self,
        query: str,
        context: str = "",
        chat_history: List[Dict[str, str]] = None
    ) -> Iterator[str]:
        """
        Generate a streaming response using Groq API.
        
        Args:
            query: User query
            context: Retrieved context from RAG
            chat_history: Conversation history
            
        Yields:
            Response chunks
        """
        # Prepare messages
        messages = [
            {"role": "system", "content": self._get_system_prompt(context)}
        ]
        
        # Add chat history
        if chat_history:
            for msg in chat_history:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Generate streaming response
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=1,
                stream=True,
                stop=None
            )
            
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error generating response: {str(e)}"
    
    def check_connection(self) -> bool:
        """
        Check if Groq API is available.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try a simple API call
            self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            print(f"Failed to connect to Groq: {e}")
            return False
    
    def set_citation_style(self, style: str) -> None:
        """
        Update the citation style.
        
        Args:
            style: Citation style ("clean" or "none")
        """
        if style in ["clean", "none"]:
            self.citation_style = style
        else:
            print(f"Invalid citation style: {style}. Using 'clean' instead.")
            self.citation_style = "clean"

