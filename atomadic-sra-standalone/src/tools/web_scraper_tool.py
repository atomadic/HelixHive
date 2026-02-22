
import time
import re

class WebScraperTool:
    """
    Web Scraper Tool
    Specialized high-fidelity content extraction.
    Supports structured text, metadata, and link harvesting.
    """
    def __init__(self):
        self.user_agent = "SRA-IDE/3.2.0.0 (Sovereign Data Scraper)"

    def execute(self, url, mode="structured"):
        """
        Scrape content from a URL.
        Modes: 'text', 'metadata', 'structured', 'links'
        """
        print(f"[WebScraper] Scraping: {url} (mode={mode})")
        
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode("utf-8", errors="replace")
                
                if mode == "text":
                    return {"status": "SUCCESS", "content": self._extract_text(content)}
                elif mode == "metadata":
                    return {"status": "SUCCESS", "metadata": self._extract_metadata(content)}
                elif mode == "links":
                    return {"status": "SUCCESS", "links": self._extract_links(content)}
                else: # structured
                    return {
                        "status": "SUCCESS",
                        "url": url,
                        "metadata": self._extract_metadata(content),
                        "content": self._extract_text(content)[:5000],
                        "links": self._extract_links(content)
                    }
        except Exception as e:
            print(f"[WebScraper] Error: {e}")
            return {"status": "ERROR", "url": url, "error": str(e)}

    def _extract_text(self, html):
        """Clean HTML tags and return readable text."""
        # Simple regex cleaning for prototype
        text = re.sub(r'<(script|style|nav|footer)[^>]*>.*</\1>', '', html, flags=re.DOTALL|re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _extract_metadata(self, html):
        """Extract title and meta tags."""
        title_match = re.search(r'<title>(.*)</title>', html, re.IGNORECASE)
        title = title_match.group(1) if title_match else "No Title"
        
        # Meta description
        desc_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html, re.IGNORECASE)
        if not desc_match:
            desc_match = re.search(r'<meta[^>]+content="([^"]+)"[^>]+name="description"', html, re.IGNORECASE)
        description = desc_match.group(1) if desc_match else "No Description"
        
        return {"title": title, "description": description}

    def _extract_links(self, html):
        """Harvest all links."""
        links = re.findall(r'href=[\'"]([^\'" >]+)', html)
        return list(set([l for l in links if l.startswith("http")]))[:20]

if __name__ == "__main__":
    scraper = WebScraperTool()
    print(scraper.execute("https://en.wikipedia.org/wiki/Autopoiesis", mode="metadata"))
