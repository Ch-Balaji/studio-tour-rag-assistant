"""
Streamlit-based chatbot interface for Silverlight Studios RAG system.
Provides interactive chat with conversation memory and source citations.
"""

import os
import sys
import yaml
import streamlit as st
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.embeddings import EmbeddingService
from src.vector_store import ChromaDBClient
from src.retrieval import RAGRetriever
from src.llm import OllamaClient
from src.chat import MemoryManager
from src.query import QueryEnhancer


@st.cache_resource
def load_config():
    """Load configuration (cached)"""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


@st.cache_resource
def initialize_services(_config):
    """Initialize all services (cached to avoid reloading)"""
    
    # Initialize embedding service
    embedding_service = EmbeddingService(
        model_name=_config['embeddings']['model_name'],
        device=_config['embeddings']['device'],
        batch_size=_config['embeddings']['batch_size']
    )
    
    # Initialize vector store
    vector_store = ChromaDBClient(
        persist_directory=_config['vector_db']['persist_directory'],
        collection_name=_config['vector_db']['collection_name']
    )
    
    # Initialize retriever with hybrid search
    retriever = RAGRetriever(
        vector_store=vector_store,
        embedding_service=embedding_service,
        reranker_model=_config['retrieval']['reranker_model'],
        use_reranking=_config['retrieval']['use_reranking'],
        use_hybrid_search=True,  # Enable hybrid search
        bm25_index_path="./bm25_index"
    )
    
    # Initialize LLM
    llm_client = OllamaClient(
        model_name=_config['llm']['model_name'],
        base_url=_config['llm']['base_url'],
        temperature=_config['llm']['temperature'],
        max_tokens=_config['llm']['max_tokens']
    )
    
    # Initialize query enhancer
    query_enhancer = QueryEnhancer()
    
    return embedding_service, vector_store, retriever, llm_client, query_enhancer


def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'memory_manager' not in st.session_state:
        config = load_config()
        st.session_state.memory_manager = MemoryManager(
            max_turns=config['memory']['k']
        )
    
    if 'retrieved_sources' not in st.session_state:
        st.session_state.retrieved_sources = []


def display_sources(sources, message_id=None):
    """Display retrieved sources in an expandable section"""
    if not sources:
        return
    
    # Generate unique identifier for this set of sources
    if message_id is None:
        message_id = id(sources)
    
    with st.expander(f"📚 View {len(sources)} Retrieved Sources", expanded=False):
        for i, source in enumerate(sources, 1):
            metadata = source.get('metadata', {})
            similarity = source.get('similarity', 0)
            rerank_score = source.get('rerank_score', None)
            
            st.markdown(f"**Source {i}** - {metadata.get('source_file', 'Unknown')}, "
                       f"Page {metadata.get('page_num', '?')}")
            
            score_text = f"Similarity: {similarity:.3f}"
            if rerank_score is not None:
                score_text += f" | Rerank: {rerank_score:.3f}"
            
            # Add retrieval method if available
            retrieval_method = source.get('retrieval_method', 'unknown')
            if retrieval_method != 'unknown':
                score_text += f" | Method: {retrieval_method}"
            
            # Add BM25 score if available
            bm25_score = source.get('bm25_score', None)
            if bm25_score is not None:
                score_text += f" | BM25: {bm25_score:.3f}"
                
            st.caption(score_text)
            
            st.text_area(
                f"Content {i}",
                source['text'],
                height=100,
                key=f"source_{message_id}_{i}",
                label_visibility="collapsed"
            )
            
            # Show enriched metadata if available
            characters = metadata.get('characters', [])
            locations = metadata.get('locations', [])
            spells = metadata.get('spells', [])
            
            if characters or locations or spells:
                with st.expander("📋 Metadata", expanded=False):
                    if characters:
                        st.write(f"**Characters:** {', '.join(characters[:5])}")
                    if locations:
                        st.write(f"**Locations:** {', '.join(locations[:3])}")
                    if spells:
                        st.write(f"**Spells:** {', '.join(spells[:3])}")
            
            if i < len(sources):
                st.divider()


def main():
    """Main Streamlit application"""
    
    # Page configuration
    config = load_config()
    st.set_page_config(
        page_title=config['app']['title'],
        page_icon=config['app']['page_icon'],
        layout=config['app']['layout']
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize services
    with st.spinner("Loading models and services..."):
        embedding_service, vector_store, retriever, llm_client, query_enhancer = initialize_services(config)
    
    # Sidebar
    st.sidebar.title("⚙️ Settings")
    
    # Check Ollama connection
    ollama_connected = llm_client.check_connection()
    if ollama_connected:
        st.sidebar.success("✅ Ollama Connected")
    else:
        st.sidebar.error("❌ Ollama Not Connected")
        st.sidebar.warning("Make sure Ollama is running: `ollama serve`")
    
    # Vector store stats
    stats = vector_store.get_collection_stats()
    st.sidebar.metric("Documents in DB", stats['document_count'])
    
    st.sidebar.divider()
    
    # Retrieval settings
    st.sidebar.subheader("🔍 Retrieval Settings")
    
    use_reranking = st.sidebar.checkbox(
        "Enable Reranking",
        value=config['retrieval']['use_reranking'],
        help="Use cross-encoder to rerank results"
    )
    
    initial_top_k = st.sidebar.slider(
        "Initial Retrieval (top-k)",
        min_value=5,
        max_value=50,
        value=config['retrieval']['initial_top_k'],
        help="Number of candidates to retrieve initially"
    )
    
    final_top_n = st.sidebar.slider(
        "Final Results (top-n)",
        min_value=1,
        max_value=10,
        value=config['retrieval']['final_top_n'],
        help="Number of final results after reranking"
    )
    
    similarity_threshold = st.sidebar.slider(
        "Similarity Threshold",
        min_value=0.0,
        max_value=1.0,
        value=config['retrieval']['similarity_threshold'],
        step=0.05,
        help="Minimum similarity score to include results"
    )
    
    # Update retriever settings
    retriever.use_reranking = use_reranking
    
    st.sidebar.divider()
    
    # Hybrid search settings
    st.sidebar.subheader("🔀 Hybrid Search")
    
    use_hybrid = st.sidebar.checkbox(
        "Enable Hybrid Search",
        value=True,
        help="Combine dense (semantic) and sparse (keyword) search"
    )
    
    hybrid_alpha = st.sidebar.slider(
        "Dense Weight (α)",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="0 = pure keyword search, 1 = pure semantic search"
    )
    
    use_query_enhancement = st.sidebar.checkbox(
        "Enable Query Enhancement",
        value=True,
        help="Expand queries with character variations and corrections"
    )
    
    # Update retriever settings
    retriever.use_hybrid_search = use_hybrid
    
    st.sidebar.divider()
    
    # Citation settings
    st.sidebar.subheader("📝 Citation Style")
    
    citation_style = st.sidebar.radio(
        "How should sources be cited?",
        ["clean", "none"],
        format_func=lambda x: {
            "clean": "Clean (numbered footnotes)",
            "none": "No citations"
        }.get(x, x),
        help="Choose how sources are referenced in responses"
    )
    
    st.sidebar.divider()
    
    # Memory settings
    st.sidebar.subheader("💭 Memory")
    memory_stats = st.session_state.memory_manager.get_conversation_summary()
    st.sidebar.metric("Conversation Turns", memory_stats['turns'])
    
    if st.sidebar.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.session_state.memory_manager.clear_history()
        st.session_state.retrieved_sources = []
        st.rerun()
    
    # Main chat interface
    st.title(f"{config['app']['page_icon']} {config['app']['title']}")
    st.caption("Ask me anything about Silverlight Studios!")
    
    # Display chat messages
    for msg_idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display sources for assistant messages
            if message["role"] == "assistant" and "sources" in message:
                display_sources(message["sources"], message_id=msg_idx)
    
    # Chat input
    if prompt := st.chat_input("What would you like to know about Silverlight Studios?"):
        
        if not ollama_connected:
            st.error("⚠️ Please start Ollama service first: `ollama serve`")
            st.stop()
        
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Add to memory
        st.session_state.memory_manager.add_user_message(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                
                # Enhance query if enabled
                enhanced_query = prompt
                if use_query_enhancement:
                    enhanced_query = query_enhancer.enhance_query(prompt)
                    if enhanced_query != prompt:
                        st.caption(f"🔍 Enhanced query: {enhanced_query}")
                
                # Retrieve relevant context
                retrieved_chunks = retriever.retrieve(
                    query=enhanced_query,
                    initial_top_k=initial_top_k,
                    final_top_n=final_top_n,
                    similarity_threshold=similarity_threshold,
                    hybrid_alpha=hybrid_alpha
                )
                
                # Format context for LLM
                context = retriever.format_context(retrieved_chunks)
                
                # Get chat history
                chat_history = st.session_state.memory_manager.get_history()
                
                # Update citation style
                llm_client.set_citation_style(citation_style)
                
                # Generate streaming response
                response_placeholder = st.empty()
                full_response = ""
                
                for chunk in llm_client.generate_response_stream(
                    query=prompt,
                    context=context,
                    chat_history=chat_history[:-1]  # Exclude current user message
                ):
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")
                
                response_placeholder.markdown(full_response)
                
                # Display sources (use unique ID based on message count)
                display_sources(retrieved_chunks, message_id=len(st.session_state.messages))
            
            # Add assistant message to chat
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "sources": retrieved_chunks
            })
            
            # Add to memory
            st.session_state.memory_manager.add_assistant_message(full_response)


if __name__ == "__main__":
    main()

