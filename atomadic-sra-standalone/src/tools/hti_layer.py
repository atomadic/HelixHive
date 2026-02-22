
import time
import os

class HTILayer:
    """
    Human-Task-Interface (HTI) Layer
    Provides high-level, human-level semantic abstractions for machine control.
    Wraps Shell, Browser, and Toolsmith into complex 'Sovereign Actions'.
    """
    def __init__(self):
        from src.tools.shell_tool import InteractiveShell
        from src.tools.browser_tool import BrowserTool
        from src.agents.toolsmith_agent import ToolsmithAgent
        from src.tools.web_search_tool import WebSearchTool
        from src.tools.web_scraper_tool import WebScraperTool
        
        self.shell = InteractiveShell()
        self.browser = BrowserTool()
        self.toolsmith = ToolsmithAgent()
        self.search_tool = WebSearchTool()
        self.scraper_tool = WebScraperTool()
        
        self.active_sessions = {}

    def start_developer_session(self, workspace_path):
        """
        Human-level task: Start a persistent developer session in a workspace.
        """
        print(f"[HTI] Starting dev session in {workspace_path}")
        res = self.shell.start_session(cwd=workspace_path)
        self.active_sessions["dev"] = {"path": workspace_path, "status": "ACTIVE"}
        return res

    def deep_recursive_research(self, topic, depth=2):
        """
        Human-level task: Perform a deep research deep dive.
        """
        print(f"[HTI] Deep research initiated for: {topic}")
        # Use simple search to find the best start URL
        search_res = self.browser.search(topic)
        # In a real system, we'd extract the top result and use it as start_url
        # For prototype, we'll use duckduckgo lite results page
        start_url = f"https://lite.duckduckgo.com/lite/q={topic.replace(' ', '+')}"
        
        research_data = self.browser.perform_agent_research(start_url, depth=depth)
        
        return {
            "topic": topic,
            "status": "COMPLETED",
            "findings_count": len(research_data),
            "summary": f"Explored {len(research_data)} pages related to {topic}."
        }

    def inspect_and_refactor(self, target_path, goal_description):
        """
        Human-level task: Inspect a file and perform targeted refactoring to meet a goal.
        """
        print(f"[HTI] Inspecting {target_path} for refactor: {goal_description}")
        
        if not os.path.exists(target_path):
            return {"status": "ERROR", "reason": f"Path {target_path} does not exist."}
            
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                code = f.read()
            
            # Use CodeCreationPanel for refactoring
            from src.panels.code_creation_panel import CodeCreationPanel
            ccp = CodeCreationPanel()
            
            # Perform Audit first
            audit = ccp.audit_code(code)
            print(f"[HTI] Audit Results: {audit['logic']}")
            
            # Refactor
            refactored = ccp.refactor(code, instruction=goal_description)
            
            # In a real environment, we'd write back or propose a diff
            # For this action, we'll return the result
            return {
                "status": "SUCCESS",
                "target": target_path,
                "audit": audit,
                "refactored_lines": refactored.count("\n") + 1
            }
        except Exception as e:
            return {"status": "ERROR", "reason": str(e)}

    def automate_workflow(self, workflow_description):
        """
        Human-level task: Automate a multi-step workflow.
        """
        print(f"[HTI] Automating workflow: {workflow_description}")
        # Placeholder for complex agent orchestration
        return {"status": "SUCCESS", "workflow": workflow_description}

    def perform_sovereign_procurement(self, query):
        """
        High-level action: Search and scrape the top result for structured intelligence.
        """
        print(f"[HTI] Procuring intelligence for: {query}")
        search_res = self.search_tool.execute(query)
        
        if search_res["status"] != "SUCCESS" or not search_res["results"]:
            return {"status": "ERROR", "reason": "No search results found."}
        
        top_url = search_res["results"][0]["url"]
        print(f"[HTI] Top result: {top_url}. Scraping...")
        
        scrape_res = self.scraper_tool.execute(top_url, mode="structured")
        
        return {
            "query": query,
            "status": "SUCCESS",
            "top_source": top_url,
            "metadata": scrape_res.get("metadata"),
            "intel_summary": scrape_res.get("content", "")[:2000]
        }

    def web_research_deep_dive(self, topic):
        """
        Human-level task: Perform deep research on a topic using the browser.
        """
        print(f"[HTI] Performing deep dive on: {topic}")
        search_res = self.browser.search(topic)
        # More complex logic would follow: following links, scraping, summarizing
        return {"status": "SUCCESS", "topic": topic, "summary": search_res.get("content", "")[:500]}
