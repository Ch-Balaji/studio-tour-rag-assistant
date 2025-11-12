"""
Performance Profiling Script for RAG System
Measures latency of each component to identify bottlenecks
"""

import os
import sys
import time
import yaml
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.embeddings import EmbeddingService
from src.vector_store import ChromaDBClient
from src.retrieval import RAGRetriever
from src.llm import OllamaClient
from src.query import QueryEnhancer


class PerformanceProfiler:
    """Profile performance of RAG pipeline components"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize profiler with config"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.timings: Dict[str, float] = {}
        self.start_time = None
        
    def _load_config(self) -> dict:
        """Load configuration"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def start_timer(self, label: str):
        """Start timing a component"""
        self.start_time = time.time()
        self.current_label = label
    
    def end_timer(self):
        """End timing and record result"""
        if self.start_time:
            elapsed = (time.time() - self.start_time) * 1000  # Convert to ms
            self.timings[self.current_label] = elapsed
            return elapsed
        return 0
    
    def profile_full_pipeline(self, query: str, verbose: bool = True):
        """Profile the complete RAG pipeline"""
        
        print("=" * 80)
        print("🔍 RAG PERFORMANCE PROFILING")
        print("=" * 80)
        print(f"\n📝 Query: '{query}'")
        print(f"⚙️  Settings: Hybrid search with reranking")
        print("\n" + "=" * 80)
        
        # ==================== INITIALIZATION ====================
        if verbose:
            print("\n🚀 Initializing services...")
        
        self.start_timer("1. Load Embedding Model")
        embedding_service = EmbeddingService(
            model_name=self.config['embeddings']['model_name'],
            device=self.config['embeddings']['device'],
            batch_size=self.config['embeddings']['batch_size']
        )
        load_embedding_time = self.end_timer()
        if verbose:
            print(f"   ✓ Embedding model loaded: {load_embedding_time:.2f}ms")
        
        self.start_timer("2. Connect to Vector Store")
        vector_store = ChromaDBClient(
            persist_directory=self.config['vector_db']['persist_directory'],
            collection_name=self.config['vector_db']['collection_name']
        )
        load_vectorstore_time = self.end_timer()
        if verbose:
            print(f"   ✓ Vector store connected: {load_vectorstore_time:.2f}ms")
        
        self.start_timer("3. Load Retriever (BM25 + Reranker)")
        retriever = RAGRetriever(
            vector_store=vector_store,
            embedding_service=embedding_service,
            reranker_model=self.config['retrieval']['reranker_model'],
            use_reranking=True,
            use_hybrid_search=True,
            bm25_index_path="./bm25_index"
        )
        load_retriever_time = self.end_timer()
        if verbose:
            print(f"   ✓ Retriever initialized: {load_retriever_time:.2f}ms")
        
        self.start_timer("4. Initialize LLM Client")
        llm_client = OllamaClient(
            model_name=self.config['llm']['model_name'],
            base_url=self.config['llm']['base_url'],
            temperature=self.config['llm']['temperature'],
            max_tokens=self.config['llm']['max_tokens']
        )
        load_llm_time = self.end_timer()
        if verbose:
            print(f"   ✓ LLM client ready: {load_llm_time:.2f}ms")
        
        self.start_timer("5. Initialize Query Enhancer")
        query_enhancer = QueryEnhancer()
        load_enhancer_time = self.end_timer()
        if verbose:
            print(f"   ✓ Query enhancer ready: {load_enhancer_time:.2f}ms")
        
        total_init = sum([load_embedding_time, load_vectorstore_time, load_retriever_time, 
                         load_llm_time, load_enhancer_time])
        if verbose:
            print(f"\n   📊 Total initialization: {total_init:.2f}ms ({total_init/1000:.2f}s)")
            print("\n" + "=" * 80)
        
        # ==================== QUERY PROCESSING ====================
        print("\n⚡ Processing Query...")
        print("-" * 80)
        
        # Query Enhancement
        self.start_timer("6. Query Enhancement")
        enhanced_query = query_enhancer.enhance_query(query)
        enhance_time = self.end_timer()
        print(f"\n1️⃣  Query Enhancement: {enhance_time:.2f}ms")
        if enhanced_query != query:
            print(f"   Original: {query}")
            print(f"   Enhanced: {enhanced_query}")
        else:
            print(f"   No enhancement needed")
        
        # Full Retrieval (all steps combined)
        self.start_timer("7. Full Hybrid Retrieval + Reranking")
        final_chunks = retriever.retrieve(
            query=enhanced_query,
            initial_top_k=self.config['retrieval']['initial_top_k'],
            final_top_n=self.config['retrieval']['final_top_n'],
            similarity_threshold=self.config['retrieval']['similarity_threshold'],
            hybrid_alpha=0.5
        )
        retrieval_time = self.end_timer()
        
        print(f"\n2️⃣  Full Retrieval (Hybrid + Rerank): {retrieval_time:.2f}ms")
        print(f"   Initial top-k: {self.config['retrieval']['initial_top_k']}")
        print(f"   Final top-n: {len(final_chunks)} results")
        print(f"   Includes: Vector search + BM25 + Fusion + Reranking")
        
        # Context Formatting
        self.start_timer("8. Context Formatting")
        context = retriever.format_context(final_chunks)
        format_time = self.end_timer()
        print(f"\n3️⃣  Context Formatting: {format_time:.2f}ms")
        print(f"   Context length: {len(context)} characters")
        
        total_retrieval = enhance_time + retrieval_time + format_time
        print(f"\n   📊 Total Retrieval Time: {total_retrieval:.2f}ms ({total_retrieval/1000:.2f}s)")
        
        # ==================== LLM GENERATION ====================
        print("\n" + "=" * 80)
        print("🤖 LLM Response Generation...")
        print("-" * 80)
        
        # Time to First Token
        first_token_time = None
        full_response = ""
        chunk_count = 0
        
        llm_start = time.time()
        first_token_received = False
        
        for chunk in llm_client.generate_response_stream(
            query=query,
            context=context,
            chat_history=[]
        ):
            if not first_token_received:
                first_token_time = (time.time() - llm_start) * 1000
                print(f"\n4️⃣  Time to First Token (TTFT): {first_token_time:.2f}ms")
                print(f"   Time from query to first word: {(enhance_time + retrieval_time + format_time + first_token_time)/1000:.2f}s")
                first_token_received = True
            
            full_response += chunk
            chunk_count += 1
        
        full_generation_time = (time.time() - llm_start) * 1000
        tokens_per_sec = len(full_response.split()) / (full_generation_time / 1000)
        
        print(f"\n5️⃣  Full Response Generation: {full_generation_time:.2f}ms ({full_generation_time/1000:.2f}s)")
        print(f"   Response length: {len(full_response)} characters / {len(full_response.split())} words")
        print(f"   Chunks received: {chunk_count}")
        print(f"   Avg chars per chunk: {len(full_response) / chunk_count if chunk_count > 0 else 0:.1f}")
        print(f"   Generation speed: {len(full_response) / (full_generation_time/1000):.1f} chars/sec")
        print(f"   Tokens/sec: {tokens_per_sec:.1f} words/sec")
        
        # ==================== SUMMARY ====================
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 80)
        
        total_time = total_retrieval + full_generation_time
        
        breakdown = [
            ("Query Enhancement", enhance_time, enhance_time/total_time*100),
            ("Hybrid Retrieval", retrieval_time, retrieval_time/total_time*100),
            ("Context Formatting", format_time, format_time/total_time*100),
            ("LLM First Token (TTFT)", first_token_time, first_token_time/total_time*100),
            ("LLM Continuation", full_generation_time - first_token_time, (full_generation_time - first_token_time)/total_time*100),
        ]
        
        print(f"\n{'Component':<30} {'Time (ms)':<15} {'Time (s)':<12} {'% of Total':<12}")
        print("-" * 80)
        
        for component, time_ms, percentage in breakdown:
            time_s = time_ms / 1000
            print(f"{component:<30} {time_ms:>10.2f}ms    {time_s:>8.2f}s    {percentage:>8.1f}%")
        
        print("-" * 80)
        print(f"{'TOTAL RETRIEVAL':<30} {total_retrieval:>10.2f}ms    {total_retrieval/1000:>8.2f}s    {total_retrieval/total_time*100:>8.1f}%")
        print(f"{'TOTAL LLM':<30} {full_generation_time:>10.2f}ms    {full_generation_time/1000:>8.2f}s    {full_generation_time/total_time*100:>8.1f}%")
        print(f"{'TOTAL TIME':<30} {total_time:>10.2f}ms    {total_time/1000:>8.2f}s    100.0%")
        
        # ==================== BOTTLENECK ANALYSIS ====================
        print("\n" + "=" * 80)
        print("🎯 BOTTLENECK ANALYSIS")
        print("=" * 80)
        
        # Find slowest components
        sorted_components = sorted(breakdown, key=lambda x: x[1], reverse=True)
        
        print("\n🐌 Slowest Components:")
        for i, (component, time_ms, percentage) in enumerate(sorted_components[:5], 1):
            print(f"   {i}. {component}: {time_ms:.2f}ms ({percentage:.1f}%)")
        
        # Optimization suggestions
        print("\n💡 Optimization Suggestions:")
        
        if full_generation_time > 5000:
            print(f"   • LLM is the bottleneck ({full_generation_time/1000:.1f}s - {full_generation_time/total_time*100:.1f}% of time)")
            print(f"     → Consider using a smaller/faster model")
            print(f"     → GPU acceleration would help significantly")
            print(f"     → Current: {self.config['llm']['model_name']}")
        
        if retrieval_time > 1000:
            print(f"   • Retrieval is slow ({retrieval_time:.0f}ms)")
            print(f"     → Reduce initial_top_k (currently {self.config['retrieval']['initial_top_k']})")
            print(f"     → Consider disabling reranking (saves ~300-500ms)")
            print(f"     → Try pure vector search (disable hybrid)")
        
        if enhance_time > 50:
            print(f"   • Query enhancement taking time ({enhance_time:.0f}ms)")
            print(f"     → Can be disabled if not needed")
        
        if total_retrieval < 1500:
            print(f"   ✅ Retrieval is excellent ({total_retrieval:.0f}ms < 1.5s)")
            print(f"      Main latency is from LLM generation (expected)")
            print(f"      This is optimal - focus on LLM speed if needed")
        
        if first_token_time > 2000:
            print(f"   • High latency to first token ({first_token_time:.0f}ms)")
            print(f"     → Ollama may be cold-starting")
            print(f"     → Check if model is loaded in memory")
        
        print(f"\n🎯 Performance Rating:")
        if total_retrieval < 1000:
            print(f"   Retrieval: ⭐⭐⭐⭐⭐ Excellent (<1s)")
        elif total_retrieval < 2000:
            print(f"   Retrieval: ⭐⭐⭐⭐ Good (<2s)")
        else:
            print(f"   Retrieval: ⭐⭐⭐ Acceptable (>2s, can optimize)")
        
        if full_generation_time < 8000:
            print(f"   LLM Speed: ⭐⭐⭐⭐⭐ Excellent (<8s)")
        elif full_generation_time < 15000:
            print(f"   LLM Speed: ⭐⭐⭐⭐ Good (<15s)")
        else:
            print(f"   LLM Speed: ⭐⭐⭐ Slow (>15s, consider smaller model)")
        
        # ==================== DETAILED RESULTS ====================
        print("\n" + "=" * 80)
        print("📚 RETRIEVED SOURCES")
        print("=" * 80)
        
        print(f"\nTop {len(final_chunks)} sources:")
        for i, chunk in enumerate(final_chunks, 1):
            metadata = chunk.get('metadata', {})
            print(f"\n   {i}. {metadata.get('source_file', 'Unknown')}, Page {metadata.get('page_num', '?')}")
            print(f"      Similarity: {chunk.get('similarity', 0):.3f}")
            if 'rerank_score' in chunk:
                print(f"      Rerank: {chunk.get('rerank_score'):.3f}")
            if 'bm25_score' in chunk:
                print(f"      BM25: {chunk.get('bm25_score'):.3f}")
            print(f"      Text preview: {chunk['text'][:100]}...")
        
        # ==================== RESPONSE PREVIEW ====================
        print("\n" + "=" * 80)
        print("💬 GENERATED RESPONSE")
        print("=" * 80)
        print(f"\n{full_response[:500]}...")
        if len(full_response) > 500:
            print(f"\n   [... {len(full_response) - 500} more characters]")
        
        print("\n" + "=" * 80)
        print("✅ PROFILING COMPLETE")
        print("=" * 80)
        
        return {
            'timings': self.timings,
            'total_retrieval_ms': total_retrieval,
            'total_generation_ms': full_generation_time,
            'total_time_ms': total_time,
            'response_length': len(full_response),
            'sources_count': len(final_chunks)
        }


def run_profiling_test():
    """Run the profiling test with sample query"""
    
    # Test query
    query = "Who is Dumbledore and explain his characteristics?"
    
    # Create profiler
    profiler = PerformanceProfiler()
    
    # Run profiling
    results = profiler.profile_full_pipeline(query, verbose=True)
    
    # Additional analysis
    print("\n" + "=" * 80)
    print("📈 PERFORMANCE METRICS")
    print("=" * 80)
    
    retrieval_pct = (results['total_retrieval_ms'] / results['total_time_ms']) * 100
    generation_pct = (results['total_generation_ms'] / results['total_time_ms']) * 100
    
    print(f"\nRetrieval:  {results['total_retrieval_ms']:.0f}ms ({retrieval_pct:.1f}% of total)")
    print(f"Generation: {results['total_generation_ms']:.0f}ms ({generation_pct:.1f}% of total)")
    print(f"Total Time: {results['total_time_ms']:.0f}ms ({results['total_time_ms']/1000:.2f}s)")
    
    print(f"\nSources Retrieved: {results['sources_count']}")
    print(f"Response Length: {results['response_length']} characters")
    
    # Save results
    output_file = Path("tests/profiling_results.txt")
    with open(output_file, 'w') as f:
        f.write("RAG PERFORMANCE PROFILING RESULTS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Query: {query}\n")
        f.write(f"Total Time: {results['total_time_ms']:.0f}ms ({results['total_time_ms']/1000:.2f}s)\n\n")
        
        f.write("Component Breakdown:\n")
        for component, time_ms in profiler.timings.items():
            f.write(f"  {component}: {time_ms:.2f}ms\n")
    
    print(f"\n💾 Results saved to: {output_file}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n🎯 Starting RAG Performance Profiling...\n")
    
    # Check if Ollama is running
    import subprocess
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/version"],
            capture_output=True,
            timeout=2
        )
        if result.returncode != 0:
            print("⚠️  Warning: Ollama doesn't seem to be running!")
            print("   Please start it: ollama serve")
            sys.exit(1)
    except Exception as e:
        print(f"⚠️  Could not check Ollama status: {e}")
        print("   Make sure Ollama is running: ollama serve")
    
    # Run profiling
    try:
        run_profiling_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Profiling interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during profiling: {e}")
        import traceback
        traceback.print_exc()

