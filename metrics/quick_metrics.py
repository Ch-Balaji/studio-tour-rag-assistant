"""
Quick performance tracking script - runs 2 queries for faster testing.
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from performance_tracker import PerformanceTracker, format_metrics_table
import json


def main():
    """Run quick performance tracking with 2 queries."""
    print("🚀 Quick Metrics Test - 2 Queries\n")
    
    # Test queries
    test_queries = [
        "What are the operating hours for Silverlight Studios?",
        "What types of tours are available?"
    ]
    
    # Initialize tracker
    tracker = PerformanceTracker()
    
    # Run metrics
    all_metrics = []
    
    for query in test_queries:
        metrics = tracker.run_full_pipeline(query, top_k=10, top_n=5)
        all_metrics.append(metrics)
        time.sleep(0.5)  # Brief pause
    
    # Generate formatted table
    table = format_metrics_table(all_metrics)
    print(table)
    
    # Save results
    output_dir = Path(__file__).parent
    
    # Save JSON
    json_path = output_dir / f"quick_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    print(f"\n💾 Metrics saved to: {json_path}")
    
    # Save text table
    txt_path = output_dir / f"quick_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(txt_path, 'w') as f:
        f.write(table)
    print(f"📊 Table saved to: {txt_path}")
    
    print("\n✅ Quick metrics complete!")


if __name__ == "__main__":
    main()

