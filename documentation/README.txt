================================================================================
DOCUMENTATION FOLDER - STUDIO TOURS AI ASSISTANT
================================================================================

This folder contains high-level architecture documentation for your
PowerPoint presentation.

================================================================================
CONTENTS
================================================================================

1. DETAILED TECHNICAL ARCHITECTURE
   -------------------------------
   Files:
   - architecture_diagram.png (High-resolution, 300 DPI)
   - architecture_diagram.pdf (Vector format, scalable)
   
   Description:
   Comprehensive layered architecture showing all system components:
   - Frontend Layer (Next.js UI components)
   - Backend API Layer (FastAPI endpoints)
   - RAG Pipeline (Query enhancement, hybrid retrieval, reranking)
   - Data Storage Layer (ChromaDB, BM25 index)
   - Language Model Layer (Ollama/Llama 3.1)
   - Data Ingestion Pipeline
   
   Best for: Technical audiences, detailed system design discussions


2. SIMPLIFIED ARCHITECTURE (Non-Technical)
   ----------------------------------------
   Files:
   - simplified_architecture.png (High-resolution, 300 DPI)
   - simplified_architecture.pdf (Vector format, scalable)
   
   Description:
   Easy-to-understand end-to-end flow diagram showing:
   - User interaction (voice/text input)
   - Web interface components
   - AI processing steps (numbered 1-4)
   - Knowledge base
   - Response delivery
   - Key features and technologies
   
   Best for: Executive presentations, stakeholder demos, non-technical audiences


3. TEXT OVERVIEW
   -------------
   File: ARCHITECTURE_OVERVIEW.txt
   
   Description:
   Comprehensive text-based documentation covering:
   - System architecture layers (detailed breakdown)
   - Component descriptions and responsibilities
   - Data flow explanations
   - Technology stack details
   - Deployment considerations
   - Key features and highlights
   
   Best for: Reference document, detailed written explanations


================================================================================
USAGE RECOMMENDATIONS FOR POWERPOINT
================================================================================

Slide 1: Project Overview
- Use: simplified_architecture.png
- Audience: Everyone
- Focus: Show the big picture, end-to-end user experience

Slide 2: Technical Deep-Dive (Optional)
- Use: architecture_diagram.png
- Audience: Technical evaluators
- Focus: Show system components, hybrid RAG approach

Slide 3: Architecture Details (Optional)
- Use: Text from ARCHITECTURE_OVERVIEW.txt
- Copy relevant sections as bullet points
- Highlight: Hybrid search, streaming, local processing


================================================================================
KEY POINTS TO HIGHLIGHT IN PRESENTATION
================================================================================

1. HYBRID RAG APPROACH
   - Combines vector search (semantic) + BM25 search (keyword)
   - Reciprocal Rank Fusion (RRF) for optimal results
   - Cross-encoder reranking for precision

2. USER EXPERIENCE
   - Voice-enabled interface
   - Real-time streaming responses (< 3 seconds)
   - Source citations with every answer
   - Context-aware conversations

3. PRIVACY & DEPLOYMENT
   - 100% local processing (Ollama)
   - No external API dependencies
   - All data stays on-premise

4. TECHNICAL EXCELLENCE
   - Modern stack (Next.js, FastAPI, ChromaDB)
   - 2000+ document chunks indexed
   - Multi-language support
   - Scalable architecture


================================================================================
ARCHITECTURE EXCLUSIONS (AS REQUESTED)
================================================================================

The following components have been excluded from the architecture diagrams
as per your request:

- Text-to-Speech (TTS) features
- Groq API integration

The architecture focuses on the core RAG system with local LLM (Ollama).


================================================================================
FILE FORMATS
================================================================================

PNG Format:
- High resolution (300 DPI)
- Ready for PowerPoint insertion
- Best for: Most presentations, printing
- File size: Larger, but maintains quality

PDF Format:
- Vector format (infinitely scalable)
- Best for: Professional presentations, scaling without quality loss
- File size: Smaller, crisp at any zoom level


================================================================================
TIPS FOR POWERPOINT
================================================================================

1. Inserting Images:
   - Insert > Pictures > choose PNG or PDF file
   - PDF maintains quality when zooming during presentation
   - PNG is more compatible with older PowerPoint versions

2. Sizing:
   - Both diagrams are optimized for 16:9 widescreen slides
   - Can be resized without losing clarity (especially PDFs)

3. Annotations:
   - Add callout boxes to highlight specific components
   - Use PowerPoint's built-in shapes to draw attention to key areas
   - Add animations to reveal layers progressively

4. Color Scheme:
   - Diagrams use professional color palette:
     * Blue: User-facing components
     * Green: Backend/API layer
     * Orange: RAG/AI processing
     * Purple: Data storage
     * Red: LLM layer


================================================================================
QUESTIONS OR MODIFICATIONS?
================================================================================

If you need:
- Different color schemes
- Additional annotations
- Focus on specific components
- Alternate layouts

The architecture overview (ARCHITECTURE_OVERVIEW.txt) provides all the
technical details needed to create custom diagrams.


================================================================================
END OF DOCUMENTATION INDEX
================================================================================







