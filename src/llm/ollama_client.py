"""
Ollama LLM client for generating responses.
Integrates with Ollama API for local LLM inference.
"""

from typing import Dict, List, Any, Iterator, Optional
import ollama
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class OllamaClient:
    """Client for interacting with Ollama LLM"""
    
    def __init__(
        self,
        model_name: str = "llama3.1",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        citation_style: str = "clean"
    ):
        """
        Initialize Ollama client.
        
        Args:
            model_name: Name of the Ollama model
            base_url: Base URL for Ollama API
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            citation_style: Style for citations ("clean", "none")
        """
        self.model_name = model_name
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.citation_style = citation_style
        
        # Initialize LangChain Ollama client
        self.llm = ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=temperature,
            num_predict=max_tokens
        )
        
        # Create RAG prompt template
        self.rag_prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{query}")
        ])
        
        print(f"Ollama client initialized with model: {model_name}")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for RAG based on citation style"""
        if self.citation_style == "none":
            return """You are a helpful AI assistant with access to information from documents. 
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
            return """You are a knowledgeable assistant for Silverlight Studios with access to production documents.

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
        Generate a response using the LLM.
        
        Args:
            query: User query
            context: Retrieved context from RAG
            chat_history: Conversation history
            
        Returns:
            Generated response
        """
        # Format system prompt with context
        system_message = self._get_system_prompt().format(context=context)
        
        # Prepare messages
        messages = [SystemMessage(content=system_message)]
        
        # Add chat history
        if chat_history:
            for msg in chat_history:
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    messages.append(AIMessage(content=msg['content']))
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        # Generate response
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def generate_response_stream(
        self,
        query: str,
        context: str = "",
        chat_history: List[Dict[str, str]] = None
    ) -> Iterator[str]:
        """
        Generate a streaming response using the LLM.
        
        Args:
            query: User query
            context: Retrieved context from RAG
            chat_history: Conversation history
            
        Yields:
            Response chunks
        """
        # Format system prompt with context
        system_message = self._get_system_prompt().format(context=context)
        
        # Prepare messages
        messages = [SystemMessage(content=system_message)]
        
        # Add chat history
        if chat_history:
            for msg in chat_history:
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    messages.append(AIMessage(content=msg['content']))
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        # Generate streaming response
        try:
            for chunk in self.llm.stream(messages):
                if hasattr(chunk, 'content'):
                    yield chunk.content
        except Exception as e:
            yield f"Error generating response: {str(e)}"
    
    def check_connection(self) -> bool:
        """
        Check if Ollama service is available.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            ollama.list()
            return True
        except Exception as e:
            print(f"Failed to connect to Ollama: {e}")
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

