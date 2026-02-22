
import time

class BrowserTool:
    """
    Browser Tool
    Web research and automation with URL fetching and content extraction.
    Uses urllib for lightweight operation (no Playwright dependency required).
    """
    def __init__(self):
        self.history = []
        self.cache = {}

    def navigate(self, url, extract_text=True):
        """Fetch a URL and return content."""
        print(f"[Browser] Navigating to {url}")
        
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "SRA-IDE/3.2.0.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode("utf-8", errors="replace")
                
                result = {
                    "status": response.status,
                    "url": url,
                    "content_length": len(content),
                    "content": content[:5000] if extract_text else "[binary]",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                }
                
                self.cache[url] = result
                self.history.append({"url": url, "status": "SUCCESS"})
                print(f"[Browser] Fetched {len(content)} bytes from {url}")
                return result
        except Exception as e:
            result = {"status": "ERROR", "url": url, "error": str(e)}
            self.history.append({"url": url, "status": "ERROR", "error": str(e)})
            print(f"[Browser] Error: {e}")
            return result

    def search(self, query):
        """Perform a web search (via DuckDuckGo lite)."""
        url = f"https://lite.duckduckgo.com/lite/q={query.replace(' ', '+')}"
        return self.navigate(url)

    def get_cached(self, url):
        """Return cached page if available."""
        return self.cache.get(url)

    def get_history(self):
        return self.history

    def navigate_sequence(self, urls):
        """Navigate through a sequence of URLs and return the final state."""
        results = []
        for url in urls:
            res = self.navigate(url)
            results.append(res)
            time.sleep(1) # Human-like delay
        return results

    def extract_links(self, url):
        """Extract all links from a cached or fetched page."""
        page = self.get_cached(url) or self.navigate(url)
        content = page.get("content", "")
        
        # Simple regex-based link extraction for prototype
        import re
        links = re.findall(r'href=[\'"]([^\'" >]+)', content)
        # Filter and normalize (simplified)
        valid_links = [l for l in links if l.startswith("http")]
        return valid_links[:10] # Return top 10 for efficiency

    def perform_agent_research(self, start_url, depth=2):
        """
        Perform recursive research starting from a URL.
        Simulates a human researcher clicking through pages.
        """
        print(f"[Browser] SRA Research depth={depth} on {start_url}")
        results = []
        queue = [(start_url, 0)]
        visited = set()
        
        while queue:
            url, current_depth = queue.pop(0)
            if url in visited or current_depth > depth:
                continue
            
            res = self.navigate(url)
            visited.add(url)
            results.append(res)
            
            if current_depth < depth:
                links = self.extract_links(url)
                for link in links:
                    if link not in visited:
                        queue.append((link, current_depth + 1))
        
        return results
