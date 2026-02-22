
import sys
import os
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.hti_layer import HTILayer

def run_ml_research():
    hti = HTILayer()
    print("=== SRA Deep Research Loop: ML Autopoiesis ===")
    
    queries = [
        "autopoietic machine learning architectures for AI agents",
        "recursive self-improvement algorithms for large language models",
        "neuro-symbolic self-evolution",
        "active inference and homeostatic control in autonomous agents",
        "differentiable architecture search for agentic workflows"
    ]
    
    all_findings = []
    for q in queries:
        print(f"\n[Researching] {q}...")
        results = hti.deep_recursive_research(q, depth=1)
        # Note: HTILayer.deep_recursive_research doesn't return the raw research_data list yet, 
        # it returns a summary. I should probably have it return the data too or fetch it.
        # For now, I'll assume the browser cache has it or I'll just use the summary for synthesis.
        all_findings.append(results)
    
    # Store results for synthesis
    with open("data/ml_research_summary.json", "w", encoding="utf-8") as f:
        json.dump(all_findings, f, indent=4)
    
    print("\n[Audit] Research summaries captured to data/ml_research_summary.json")

if __name__ == "__main__":
    run_ml_research()
