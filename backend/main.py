"""
FastAPI Backend for Silverlight Studios Voice Chat Interface
"""
import logging
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import config
from backend.models.schemas import (
    TranscriptionRequest,
    TranscriptionResponse,
    ChatRequest,
    ChatResponse,
    ChatSettings,
    HealthResponse,
    SettingsResponse,
    VoiceSampleRequest,
    VoiceSampleResponse,
    VoiceStatusResponse
)
from backend.services.transcription_service import TranscriptionService
from backend.services.rag_service import RAGService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Silverlight Studios Voice Chat API",
    description="Backend API for voice chat interface with RAG",
    version="1.0.0"
)

# Configure CORS - allow all origins for public deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for public access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
transcription_service: TranscriptionService = None
rag_service: RAGService = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.memory_managers: Dict[str, any] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.memory_managers[client_id] = rag_service.create_memory_manager()
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.memory_managers:
            del self.memory_managers[client_id]
        logger.info(f"Client {client_id} disconnected")
    
    def get_memory_manager(self, client_id: str):
        return self.memory_managers.get(client_id)

manager = ConnectionManager()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global transcription_service, rag_service
    
    try:
        logger.info("Initializing services...")
        
        # Initialize transcription service with local Whisper model
        transcription_service = TranscriptionService(model_size=config.whisper_model_size)
        
        # Initialize RAG service
        rag_service = RAGService(config)
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Silverlight Studios Voice Chat API", "status": "running"}


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        health = rag_service.check_health()
        return HealthResponse(
            status="healthy" if health["llm_connected"] else "degraded",
            llm_connected=health["llm_connected"],
            llm_provider=health["llm_provider"],
            services_loaded=health["vector_store_loaded"]
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            llm_connected=False,
            llm_provider="unknown",
            services_loaded=False
        )


@app.get("/api/settings", response_model=SettingsResponse)
async def get_settings():
    """Get available RAG settings and their ranges"""
    defaults = ChatSettings(
        use_reranking=config.retrieval_config.get('use_reranking', True),
        initial_top_k=config.retrieval_config.get('initial_top_k', 25),
        final_top_n=config.retrieval_config.get('final_top_n', 5),
        similarity_threshold=config.retrieval_config.get('similarity_threshold', 0.3),
        use_hybrid_search=True,
        hybrid_alpha=0.5,
        use_query_enhancement=True,
        citation_style=config.llm_config.get('citation_style', 'clean')
    )
    
    ranges = {
        "initial_top_k": {"min": 5, "max": 50, "step": 5},
        "final_top_n": {"min": 1, "max": 10, "step": 1},
        "similarity_threshold": {"min": 0.0, "max": 1.0, "step": 0.05},
        "hybrid_alpha": {"min": 0.0, "max": 1.0, "step": 0.05}
    }
    
    return SettingsResponse(defaults=defaults, ranges=ranges)


@app.post("/api/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(request: TranscriptionRequest):
    """Transcribe audio to text using OpenAI Whisper"""
    try:
        text = transcription_service.transcribe_audio(
            audio_data=request.audio,
            audio_format=request.format
        )
        return TranscriptionResponse(text=text, success=True)
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return TranscriptionResponse(
            text="",
            success=False,
            error=str(e)
        )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Standard REST chat endpoint (non-streaming)"""
    try:
        settings = request.settings or ChatSettings()
        
        # Enhance query if enabled
        enhanced_query = request.query
        if settings.use_query_enhancement:
            enhanced_query = rag_service.enhance_query(request.query)
        
        # Retrieve context
        chunks = rag_service.retrieve_context(
            query=enhanced_query,
            initial_top_k=settings.initial_top_k,
            final_top_n=settings.final_top_n,
            similarity_threshold=settings.similarity_threshold,
            use_reranking=settings.use_reranking,
            hybrid_alpha=settings.hybrid_alpha
        )
        
        # Format context
        context = rag_service.format_context(chunks)
        
        # Generate response
        response = rag_service.generate_response(
            query=request.query,
            context=context,
            chat_history=[],
            citation_style=settings.citation_style
        )
        
        # Generate suggested questions
        suggested_questions = []
        try:
            suggested_questions = rag_service.generate_suggested_questions(
                response=response,
                chunks=chunks,
                num_questions=3
            )
        except Exception as e:
            logger.error(f"Error generating suggested questions: {e}")
        
        return ChatResponse(
            response=response,
            sources=chunks,
            enhanced_query=enhanced_query if enhanced_query != request.query else None,
            suggested_questions=suggested_questions if suggested_questions else None
        )
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for streaming chat"""
    client_id = None
    
    try:
        # Generate client ID from connection info
        client_id = f"{websocket.client.host}:{websocket.client.port}"
        await manager.connect(websocket, client_id)
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            query = data.get("query")
            settings_data = data.get("settings", {})
            
            if not query:
                await websocket.send_json({
                    "type": "error",
                    "content": "No query provided"
                })
                continue
            
            # Parse settings
            settings = ChatSettings(**settings_data) if settings_data else ChatSettings()
            
            try:
                # Get memory manager for this client
                memory_manager = manager.get_memory_manager(client_id)
                
                # Enhance query if enabled
                enhanced_query = query
                if settings.use_query_enhancement:
                    enhanced_query = rag_service.enhance_query(query)
                    if enhanced_query != query:
                        await websocket.send_json({
                            "type": "enhanced_query",
                            "content": enhanced_query
                        })
                
                # Retrieve context
                chunks = rag_service.retrieve_context(
                    query=enhanced_query,
                    initial_top_k=settings.initial_top_k,
                    final_top_n=settings.final_top_n,
                    similarity_threshold=settings.similarity_threshold,
                    use_reranking=settings.use_reranking,
                    hybrid_alpha=settings.hybrid_alpha
                )
                
                # Send sources
                await websocket.send_json({
                    "type": "sources",
                    "content": chunks
                })
                
                # Format context
                context = rag_service.format_context(chunks)
                
                # Get chat history
                chat_history = memory_manager.get_history()
                
                # Add user message to memory
                memory_manager.add_user_message(query)
                
                # Stream response with batching for better performance
                full_response = ""
                chunk_buffer = ""
                MIN_CHUNK_SIZE = 40  # Minimum characters before sending (optimized for performance while maintaining smooth UX)
                
                for chunk in rag_service.generate_response_stream(
                    query=query,
                    context=context,
                    chat_history=chat_history,
                    citation_style=settings.citation_style
                ):
                    full_response += chunk
                    chunk_buffer += chunk
                    
                    # Send when buffer reaches minimum size or contains sentence-ending punctuation
                    if len(chunk_buffer) >= MIN_CHUNK_SIZE or chunk in ['.', '!', '?', '\n']:
                        await websocket.send_json({
                            "type": "chunk",
                            "content": str(chunk_buffer)  # Ensure it's a string
                        })
                        chunk_buffer = ""
                
                # Send any remaining buffered content
                if chunk_buffer:
                    await websocket.send_json({
                        "type": "chunk",
                        "content": str(chunk_buffer)  # Ensure it's a string
                    })
                
                # Add assistant message to memory
                memory_manager.add_assistant_message(full_response)
                
                # Generate suggested questions based on response and chunks
                try:
                    suggested_questions = rag_service.generate_suggested_questions(
                        response=full_response,
                        chunks=chunks,
                        num_questions=3
                    )
                    
                    # Send suggested questions
                    await websocket.send_json({
                        "type": "suggested_questions",
                        "content": suggested_questions
                    })
                except Exception as e:
                    logger.error(f"Error generating suggested questions: {e}")
                    # Continue even if question generation fails
                
                # Send completion signal
                await websocket.send_json({
                    "type": "done"
                })
            
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "content": str(e)
                })
    
    except WebSocketDisconnect:
        if client_id:
            manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if client_id:
            manager.disconnect(client_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=config.backend_port,
        reload=True
    )

