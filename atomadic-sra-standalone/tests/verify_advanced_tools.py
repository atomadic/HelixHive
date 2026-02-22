
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_advanced_tools():
    print("=== SRA Advanced Tool Acquisition Verification (Phase 7) ===")
    
    from src.tools.hti_layer import HTILayer
    hti = HTILayer()
    
    # 1. Test WebSearchTool
    print("\n[Test 1] WebSearchTool Functional Check")
    search_res = hti.search_tool.execute("autopoietic systems")
    if search_res["status"] == "SUCCESS" and len(search_res["results"]) > 0:
        print(f"  [PASS] Found {len(search_res['results'])} results.")
        print(f"  Top Result: {search_res['results'][0]['title']}")
    else:
        print(f"  [FAIL] Search failed or no results. Status: {search_res.get('status')}")

    # 2. Test WebScraperTool
    print("\n[Test 2] WebScraperTool Functional Check")
    test_url = "https://lite.duckduckgo.com/lite/"
    scrape_res = hti.scraper_tool.execute(test_url, mode="metadata")
    if scrape_res["status"] == "SUCCESS" and "metadata" in scrape_res:
        print(f"  [PASS] Successfully scraped metadata from {test_url}")
        print(f"  Title: {scrape_res['metadata'].get('title')}")
    else:
        print(f"  [FAIL] Scraper failed. Status: {scrape_res.get('status')}")

    # 3. Test HTI Integration (Sovereign Procurement)
    print("\n[Test 3] HTI Sovereign Procurement Orchestration")
    # For speed in testing, we use a simple query
    proc_res = hti.perform_sovereign_procurement("SRA Autonomous Agent")
    if proc_res["status"] == "SUCCESS":
        print(f"  [PASS] HTI Procurement successful.")
        print(f"  Source: {proc_res['top_source']}")
        print(f"  Intel Digest: {proc_res['intel_summary'][:200]}...")
    else:
        print(f"  [FAIL] HTI Procurement failed. Reason: {proc_res.get('reason')}")

    print("\n=== Phase 7 Verification Complete ===")

if __name__ == "__main__":
    test_advanced_tools()
