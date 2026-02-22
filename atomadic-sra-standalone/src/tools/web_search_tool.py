
import urllib.request
import re
import time

class WebSearchTool:
    """
    Web Search Tool
    Provides structured web search results (title, snippet, URL) 
    via public search engine scraping (DuckDuckGo Lite).
    """
    def __init__(self):
        self.user_agent = "SRA-IDE/3.2.0.0 (Sovereign Information Procurement)"

    def execute(self, query):
        """Perform a search and return list of results."""
        print(f"[WebSearch] Querying: {query}")
        url = f"https://lite.duckduckgo.com/lite/q={query.replace(' ', '+')}"
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode("utf-8", errors="replace")
                return self._parse_ddg_lite(content)
        except Exception as e:
            print(f"[WebSearch] Error: {e}")
            return {"status": "ERROR", "error": str(e)}

    def _parse_ddg_lite(self, html):
        """Simplified parsing for DuckDuckGo Lite results."""
        results = []
        # Find result containers (simplified regex for prototype)
        # DDG Lite uses tables; we'll hunt for result links and snippets
        
        # Pattern for title & link
        # <a rel="nofollow" href="...">Title</a>
        link_pattern = r'<a[^>]+rel="nofollow"[^>]+href="([^"]+)"[^>]*>(.*)</a>'
        matches = re.findall(link_pattern, html)
        
        # Pattern for snippets (usually in a sibling <td> or following text)
        snippet_pattern = r'<td class="result-snippet">(.*)</td>'
        snippets = re.findall(snippet_pattern, html, re.DOTALL)

        for i in range(min(len(matches), 5)):
            url, title = matches[i]
            # Clean HTML tags from title
            title = re.sub(r'<[^>]+>', '', title)
            snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else "No snippet available."
            
            results.append({
                "title": title,
                "url": url,
                "snippet": snippet
            })
            
        print(f"[WebSearch] Found {len(results)} results.")
        return {
            "status": "SUCCESS",
            "query": "Scraped from DDG Lite",
            "results": results,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

if __name__ == "__main__":
    search = WebSearchTool()
    print(search.execute("autopoietic systems"))
