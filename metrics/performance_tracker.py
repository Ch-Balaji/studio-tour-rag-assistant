"""
Performance tracking script for Silverlight Studios RAG system.
Measures timing for each component from user query to final response.
"""

import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple
import json
from datetime import datetime

# Add parent directory to path to import existing modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.query.query_enhancer import QueryEnhancer
from src.chat.memory_manager import MemoryManager
from src.retrieval.retriever import RAGRetriever
from src.embeddings.embedding_service import EmbeddingService
from src.vector_store.chroma_client import ChromaDBClient
from src.retrieval.bm25_index import BM25Index
from groq import Groq
import yaml


class PerformanceTracker:
    """Track performance metrics for each component of the RAG pipeline."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the performance tracker with all necessary components."""
        print("🚀 Initializing Performance Tracker...\n")
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.query_enhancer = QueryEnhancer()
        self.memory_manager = MemoryManager(max_turns=5)
        
        # Initialize embedding service
        embedding_model = self.config['embeddings']['model_name']
        self.embedding_service = EmbeddingService(model_name=embedding_model)
        
        # Initialize vector store
        chroma_path = self.config['vector_db']['persist_directory']
        collection_name = self.config['vector_db']['collection_name']
        self.vector_store = ChromaDBClient(
            persist_directory=chroma_path,
            collection_name=collection_name
        )
        
        # Initialize BM25 index path
        bm25_path = self.config.get('bm25', {}).get('persist_path', 'bm25_index')
        
        # Initialize retriever
        self.retriever = RAGRetriever(
            vector_store=self.vector_store,
            embedding_service=self.embedding_service,
            bm25_index_path=bm25_path,
            use_reranking=True,
            use_hybrid_search=True
        )
        
        # Get BM25 index from retriever for direct timing measurements
        self.bm25_index = self.retriever.bm25_index
        
        # Initialize Groq client
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable not set. "
                "Please set it with: export GROQ_API_KEY='your_api_key_here'"
            )
        self.groq_client = Groq(api_key=groq_api_key)
        self.groq_model = "llama-3.1-8b-instant"
        
        print("✅ All components initialized successfully!\n")
    
    def track_query_enhancement(self, query: str) -> Tuple[str, float]:
        """Track query enhancement timing."""
        start_time = time.time()
        enhanced_query = self.query_enhancer.enhance_query(query)
        elapsed_time = time.time() - start_time
        return enhanced_query, elapsed_time
    
    def track_retrieval(self, query: str, top_k: int = 10, top_n: int = 5) -> Tuple[List, float]:
        """Track retrieval timing (includes embedding, search, fusion, reranking)."""
        start_time = time.time()
        results = self.retriever.retrieve(query, initial_top_k=top_k, final_top_n=top_n)
        elapsed_time = time.time() - start_time
        return results, elapsed_time
    
    def track_retrieval_detailed(self, query: str, top_k: int = 10, top_n: int = 5) -> Dict[str, float]:
        """Track detailed retrieval timing for each sub-component."""
        timings = {}
        
        # 1. Query Embedding
        start_time = time.time()
        query_embedding = self.embedding_service.embed_query(query)
        timings['query_embedding'] = time.time() - start_time
        
        # 2. Dense (Vector) Retrieval
        start_time = time.time()
        dense_results = self.vector_store.query_collection(
            query_embedding=query_embedding,
            top_k=top_k
        )
        timings['dense_retrieval'] = time.time() - start_time
        
        # 3. Sparse (BM25) Retrieval
        start_time = time.time()
        sparse_results = self.bm25_index.search(query, top_k=top_k)
        timings['sparse_retrieval'] = time.time() - start_time
        
        # 4. Reciprocal Rank Fusion
        start_time = time.time()
        # Combine results using RRF
        fused_results = self._perform_rrf(dense_results, sparse_results, top_k)
        timings['rrf_fusion'] = time.time() - start_time
        
        # 5. Reranking
        if len(fused_results) > 0:
            start_time = time.time()
            # Get texts for reranking
            texts = [doc.get('text', '') for doc in fused_results[:top_k]]
            if self.retriever.reranker and texts:
                pairs = [[query, text] for text in texts]
                scores = self.retriever.reranker.predict(pairs)
                timings['reranking'] = time.time() - start_time
            else:
                timings['reranking'] = 0.0
        else:
            timings['reranking'] = 0.0
        
        return timings
    
    def _perform_rrf(self, dense_results: Dict, sparse_results: List, top_k: int) -> List:
        """Simple RRF implementation for timing."""
        # This is simplified; actual retriever has more complex logic
        combined = []
        
        # Add dense results
        if 'documents' in dense_results and dense_results['documents']:
            for i, doc in enumerate(dense_results['documents'][0][:top_k]):
                combined.append({
                    'text': doc,
                    'metadata': dense_results.get('metadatas', [[]])[0][i] if dense_results.get('metadatas') else {},
                    'score': 1.0 / (i + 1)
                })
        
        return combined[:top_k]
    
    def track_llm_response(self, query: str, context: str, chat_history: str = "") -> Tuple[str, float, Dict]:
        """Track LLM response generation timing."""
        # Build prompt
        prompt = self._build_prompt(query, context, chat_history)
        
        # Track first token time and total time separately
        start_time = time.time()
        first_token_time = None
        response_chunks = []
        
        # Stream response from Groq
        stream = self.groq_client.chat.completions.create(
            model=self.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                if first_token_time is None:
                    first_token_time = time.time() - start_time
                response_chunks.append(chunk.choices[0].delta.content)
        
        total_time = time.time() - start_time
        full_response = ''.join(response_chunks)
        
        timings = {
            'time_to_first_token': first_token_time or 0.0,
            'total_generation_time': total_time,
            'tokens_generated': len(full_response.split())
        }
        
        return full_response, total_time, timings
    
    def _build_prompt(self, query: str, context: str, chat_history: str = "") -> str:
        """Build the prompt for LLM."""
        system_prompt = """You are a helpful Harry Potter expert assistant. Use the provided context from the Harry Potter books to answer questions accurately.

If the context doesn't contain relevant information, say so. Always cite which book or source you're using.

Context from Harry Potter books:
{context}

{history}

User Question: {query}

Answer:"""
        
        history_text = f"\nConversation History:\n{chat_history}" if chat_history else ""
        
        return system_prompt.format(
            context=context,
            history=history_text,
            query=query
        )
    
    def run_full_pipeline(self, query: str, top_k: int = 10, top_n: int = 5) -> Dict:
        """Run the full pipeline and track all metrics."""
        print(f"📝 Query: '{query}'\n")
        print("=" * 80)
        
        total_start = time.time()
        metrics = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'config': {
                'top_k': top_k,
                'top_n': top_n,
                'llm_model': self.groq_model
            }
        }
        
        # 1. Query Enhancement
        print("\n🔧 Step 1: Query Enhancement")
        enhanced_query, qe_time = self.track_query_enhancement(query)
        metrics['query_enhancement'] = {
            'original_query': query,
            'enhanced_query': enhanced_query,
            'time_seconds': round(qe_time, 4)
        }
        print(f"   ⏱️  Time: {qe_time*1000:.2f}ms")
        print(f"   ✏️  Enhanced: '{enhanced_query}'")
        
        # 2. Detailed Retrieval
        print("\n🔍 Step 2: Retrieval Pipeline")
        retrieval_timings = self.track_retrieval_detailed(enhanced_query, top_k, top_n)
        results, total_retrieval_time = self.track_retrieval(enhanced_query, top_k, top_n)
        
        metrics['retrieval'] = {
            'total_time_seconds': round(total_retrieval_time, 4),
            'breakdown': {k: round(v, 4) for k, v in retrieval_timings.items()},
            'chunks_retrieved': len(results)
        }
        
        print(f"   📊 Sub-components:")
        print(f"      • Query Embedding: {retrieval_timings['query_embedding']*1000:.2f}ms")
        print(f"      • Dense Retrieval (Vector): {retrieval_timings['dense_retrieval']*1000:.2f}ms")
        print(f"      • Sparse Retrieval (BM25): {retrieval_timings['sparse_retrieval']*1000:.2f}ms")
        print(f"      • RRF Fusion: {retrieval_timings['rrf_fusion']*1000:.2f}ms")
        print(f"      • Reranking: {retrieval_timings['reranking']*1000:.2f}ms")
        print(f"   ⏱️  Total Retrieval: {total_retrieval_time*1000:.2f}ms")
        print(f"   📚 Chunks Retrieved: {len(results)}")
        
        # 3. Format Context
        print("\n📖 Step 3: Context Formatting")
        context_start = time.time()
        context = self.retriever.format_context(results)
        context_time = time.time() - context_start
        metrics['context_formatting'] = {
            'time_seconds': round(context_time, 4),
            'context_length_chars': len(context)
        }
        print(f"   ⏱️  Time: {context_time*1000:.2f}ms")
        print(f"   📏 Context Length: {len(context)} characters")
        
        # 4. LLM Response Generation
        print("\n🤖 Step 4: LLM Response Generation (Groq)")
        response, llm_time, llm_timings = self.track_llm_response(
            enhanced_query, 
            context,
            ""
        )
        metrics['llm_generation'] = {
            'total_time_seconds': round(llm_time, 4),
            'time_to_first_token_seconds': round(llm_timings['time_to_first_token'], 4),
            'tokens_generated': llm_timings['tokens_generated'],
            'model': self.groq_model
        }
        print(f"   ⏱️  Time to First Token: {llm_timings['time_to_first_token']*1000:.2f}ms")
        print(f"   ⏱️  Total Generation: {llm_time*1000:.2f}ms")
        print(f"   📝 Tokens Generated: {llm_timings['tokens_generated']}")
        
        # Total time
        total_time = time.time() - total_start
        metrics['total_pipeline'] = {
            'time_seconds': round(total_time, 4),
            'time_milliseconds': round(total_time * 1000, 2)
        }
        
        # Response preview
        metrics['response_preview'] = response[:200] + "..." if len(response) > 200 else response
        
        print("\n" + "=" * 80)
        print(f"\n⏱️  TOTAL TIME: {total_time*1000:.2f}ms ({total_time:.3f}s)")
        print(f"\n💬 Response Preview:\n{response[:300]}...\n")
        
        return metrics


def format_metrics_table(metrics_list: List[Dict]) -> str:
    """Format metrics as a nice table."""
    table = "\n" + "=" * 100 + "\n"
    table += " " * 35 + "PERFORMANCE METRICS SUMMARY\n"
    table += "=" * 100 + "\n\n"
    
    for i, metrics in enumerate(metrics_list, 1):
        table += f"\n{'─' * 100}\n"
        table += f"Query #{i}: {metrics['query']}\n"
        table += f"{'─' * 100}\n\n"
        
        table += f"{'Component':<40} {'Time (ms)':<15} {'Time (s)':<15} {'Details'}\n"
        table += f"{'-' * 40} {'-' * 15} {'-' * 15} {'-' * 30}\n"
        
        # Query Enhancement
        qe = metrics['query_enhancement']
        table += f"{'1. Query Enhancement':<40} {qe['time_seconds']*1000:<15.2f} {qe['time_seconds']:<15.4f}\n"
        
        # Retrieval breakdown
        ret = metrics['retrieval']
        table += f"{'2. Retrieval Pipeline (Total)':<40} {ret['total_time_seconds']*1000:<15.2f} {ret['total_time_seconds']:<15.4f} {ret['chunks_retrieved']} chunks\n"
        
        for component, time_val in ret['breakdown'].items():
            comp_name = f"   • {component.replace('_', ' ').title()}"
            table += f"{comp_name:<40} {time_val*1000:<15.2f} {time_val:<15.4f}\n"
        
        # Context Formatting
        cf = metrics['context_formatting']
        table += f"{'3. Context Formatting':<40} {cf['time_seconds']*1000:<15.2f} {cf['time_seconds']:<15.4f} {cf['context_length_chars']} chars\n"
        
        # LLM Generation
        llm = metrics['llm_generation']
        table += f"{'4. LLM Generation (Total)':<40} {llm['total_time_seconds']*1000:<15.2f} {llm['total_time_seconds']:<15.4f} {llm['tokens_generated']} tokens\n"
        table += f"{'   • Time to First Token':<40} {llm['time_to_first_token_seconds']*1000:<15.2f} {llm['time_to_first_token_seconds']:<15.4f}\n"
        
        # Total
        total = metrics['total_pipeline']
        table += f"\n{'-' * 100}\n"
        table += f"{'TOTAL PIPELINE TIME':<40} {total['time_milliseconds']:<15.2f} {total['time_seconds']:<15.4f}\n"
        table += f"{'-' * 100}\n"
    
    # Average statistics if multiple queries
    if len(metrics_list) > 1:
        table += f"\n\n{'=' * 100}\n"
        table += " " * 40 + "AVERAGE METRICS\n"
        table += f"{'=' * 100}\n\n"
        
        avg_qe = sum(m['query_enhancement']['time_seconds'] for m in metrics_list) / len(metrics_list)
        avg_ret = sum(m['retrieval']['total_time_seconds'] for m in metrics_list) / len(metrics_list)
        avg_cf = sum(m['context_formatting']['time_seconds'] for m in metrics_list) / len(metrics_list)
        avg_llm = sum(m['llm_generation']['total_time_seconds'] for m in metrics_list) / len(metrics_list)
        avg_total = sum(m['total_pipeline']['time_seconds'] for m in metrics_list) / len(metrics_list)
        
        table += f"{'Component':<40} {'Avg Time (ms)':<15} {'Avg Time (s)':<15}\n"
        table += f"{'-' * 40} {'-' * 15} {'-' * 15}\n"
        table += f"{'Query Enhancement':<40} {avg_qe*1000:<15.2f} {avg_qe:<15.4f}\n"
        table += f"{'Retrieval Pipeline':<40} {avg_ret*1000:<15.2f} {avg_ret:<15.4f}\n"
        table += f"{'Context Formatting':<40} {avg_cf*1000:<15.2f} {avg_cf:<15.4f}\n"
        table += f"{'LLM Generation':<40} {avg_llm*1000:<15.2f} {avg_llm:<15.4f}\n"
        table += f"{'-' * 100}\n"
        table += f"{'AVERAGE TOTAL TIME':<40} {avg_total*1000:<15.2f} {avg_total:<15.4f}\n"
        table += f"{'=' * 100}\n"
    
    return table


def main():
    """Main function to run performance tracking."""
    # Test queries
    test_queries = [
        "Who is Harry Potter's best friend?",
        "What is the Patronus charm and how does it work?",
        "Describe the Battle of Hogwarts",
        "What are the Deathly Hallows?",
        "Tell me about Severus Snape's role in the story"
    ]
    
    # Initialize tracker
    tracker = PerformanceTracker()
    
    # Run metrics for all queries
    all_metrics = []
    
    for query in test_queries:
        metrics = tracker.run_full_pipeline(query, top_k=10, top_n=5)
        all_metrics.append(metrics)
        time.sleep(1)  # Brief pause between queries
    
    # Generate formatted table
    table = format_metrics_table(all_metrics)
    print(table)
    
    # Save results
    output_dir = Path(__file__).parent
    
    # Save JSON
    json_path = output_dir / f"metrics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    print(f"\n💾 Detailed metrics saved to: {json_path}")
    
    # Save text table
    txt_path = output_dir / f"metrics_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(txt_path, 'w') as f:
        f.write(table)
    print(f"📊 Metrics table saved to: {txt_path}")
    
    print("\n✅ Performance tracking complete!")


if __name__ == "__main__":
    main()

