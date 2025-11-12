================================================================================
PERFORMANCE METRICS TRACKER - README
================================================================================

PURPOSE:
--------
Track detailed performance metrics for the Harry Potter RAG system using Groq API.
Measures timing for each component from user query to final response.

COMPONENTS TRACKED:
-------------------
1. Query Enhancement - Query expansion and optimization
2. Retrieval Pipeline:
   - Query Embedding (sentence-transformers)
   - Dense Retrieval (Vector similarity via ChromaDB)
   - Sparse Retrieval (BM25 keyword matching)
   - RRF Fusion (Reciprocal Rank Fusion)
   - Reranking (Cross-encoder scoring)
3. Context Formatting - Preparing context for LLM
4. LLM Generation - Groq API response (with time-to-first-token)

SETUP:
------
1. Ensure conda environment is activated:
   conda activate hp_rag_voice

2. Set your Groq API key:
   export GROQ_API_KEY='your_api_key_here'

3. Run metrics:
   python metrics/performance_tracker.py        # Full test (5 queries)
   python metrics/quick_metrics.py              # Quick test (2 queries)

USING THE SHELL SCRIPT:
-----------------------
./metrics/run_metrics.sh

(Make sure to set GROQ_API_KEY in your environment first)

OUTPUT FILES:
-------------
- metrics_report_TIMESTAMP.json  - Detailed metrics in JSON format
- metrics_table_TIMESTAMP.txt    - Human-readable table format

EXAMPLE OUTPUT:
---------------
Component                                Time (ms)       Time (s)
---------------------------------------- --------------- ---------------
1. Query Enhancement                     0.36           0.0004
2. Retrieval Pipeline (Total)            57.86          0.0579         5 chunks
   • Query Embedding                     29.30          0.0293
   • Dense Retrieval (Vector)            8.77           0.0088
   • Sparse Retrieval (BM25)             19.35          0.0194
   • RRF Fusion                          0.01           0.0000
   • Reranking                           146.98         0.1470
3. Context Formatting                    0.01           0.0000         2986 chars
4. LLM Generation (Total)                1245.32        1.2453         127 tokens
   • Time to First Token                 89.45          0.0895
----------------------------------------------------------------------------------------------------
TOTAL PIPELINE TIME                      1303.55        1.3036

TROUBLESHOOTING:
----------------
- If you get "Invalid API Key": Set correct GROQ_API_KEY
- If BM25 index not found: Run scripts/ingest_data.py first
- If ChromaDB empty: Run scripts/ingest_data.py to populate database
- If imports fail: Make sure you're in the project root directory

NOTES:
------
- This script does NOT modify your existing codebase
- All metrics files are saved in the metrics/ folder
- Uses Groq API (llama-3.1-8b-instant) for fast responses
- For production use, consider running multiple iterations for statistical significance

================================================================================

