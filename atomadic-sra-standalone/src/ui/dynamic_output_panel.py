
import time
import json

class DynamicOutputPanel:
    """
    Dynamic Output & UX Panel
    Relevance filtering, formatting, archiving, and UX optimization.
    Formats all SRA outputs for optimal readability.
    """
    def __init__(self):
        self.archive = []
        self.format_config = {
            "use_markdown": True,
            "max_width": 120,
            "show_timestamps": True,
            "show_metrics": True
        }

    def format_output(self, content, output_type="general", metrics=None):
        """Format content for display based on type with helical audit header."""
        formatted = ""
        
        # Implementation 10: Structured Output τ-Annotation
        if metrics:
            header = self.generate_helical_header(
                metrics.get("tau", 1.0), 
                metrics.get("j", 1.0), 
                metrics.get("delta_m", 0)
            )
            formatted = f"{header}\n\n"
        
        if output_type == "code":
            formatted += f"```python\n{content}\n```"
        elif output_type == "table":
            formatted = self._format_table(content)
        elif output_type == "alert":
            formatted = f" **Alert**: {content}"
        elif output_type == "metric":
            formatted = self._format_metrics(content)
        else:
            formatted = f"**SRA Output**:\n{content}"
        
        if self.format_config["show_timestamps"]:
            formatted = f"[{time.strftime('%H:%M:%S')}] {formatted}"
        
        self.archive.append({
            "content": content[:500],
            "type": output_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        })
        
        return formatted

    def generate_helical_header(self, tau, j, delta_m):
        """Generates a standardized Helical Audit Header."""
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        return (
            f"--- HELICAL AUDIT: {timestamp} ---\n"
            f"τ: {tau:.4f} | J: {j:.2f} | ΔM: +{delta_m}\n"
            f"Status: SOVEREIGN | Coherence: {(tau * j):.4f}\n"
            f"--------------------------------------"
        )

    def update_agent_thoughts(self, agent_name, thoughts):
        """Update a dedicated window/view for agent thought streams."""
        # In a real UI, this would push specifically to the 'Thought Stream' UI component
        print(f"[UI:ThoughtStream] {agent_name}: {thoughts[:100]}...")
        return {"agent": agent_name, "type": "thought_stream", "content": thoughts}

    def update_panel_discussion(self, discussion_topic, participants, dialogue):
        """Update a dedicated window for cross-agent panel discussions."""
        # Dedicated 'Discuss Window' for Governance side
        print(f"[UI:DiscussWindow] {discussion_topic} ({', '.join(participants)})")
        return {
            "topic": discussion_topic,
            "type": "panel_discussion",
            "dialogue": dialogue
        }

    def _format_table(self, data):
        """Format dict/list as aligned table."""
        if isinstance(data, dict):
            max_key = max(len(str(k)) for k in data.keys()) if data else 0
            lines = []
            for k, v in data.items():
                lines.append(f"  {str(k).ljust(max_key)} | {v}")
            header = f"  {'Key'.ljust(max_key)} | Value"
            separator = f"  {'-' * max_key}--{'-' * 40}"
            return "\n".join([header, separator] + lines)
        elif isinstance(data, list) and data:
            if isinstance(data[0], dict):
                keys = list(data[0].keys())
                header = " | ".join(keys)
                rows = [" | ".join(str(row.get(k, "")) for k in keys) for row in data]
                return header + "\n" + "-" * len(header) + "\n" + "\n".join(rows)
        return str(data)

    def _format_metrics(self, metrics):
        """Format metrics with visual indicators."""
        lines = [" **Metrics**:"]
        if isinstance(metrics, dict):
            for k, v in metrics.items():
                if isinstance(v, float):
                    bar_len = int(v * 20) if v <= 1 else int(min(v, 100) / 5)
                    bar = "" * bar_len + "" * (20 - bar_len)
                    lines.append(f"  {k}: [{bar}] {v}")
                else:
                    lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    def filter_relevance(self, items, query, threshold=0.3):
        """Filter items by relevance to query."""
        query_words = set(query.lower().split())
        results = []
        for item in items:
            text = str(item).lower()
            matches = sum(1 for w in query_words if w in text)
            score = matches / len(query_words) if query_words else 0
            if score >= threshold:
                results.append({"item": item, "relevance": round(score, 2)})
        return sorted(results, key=lambda x: x["relevance"], reverse=True)

    def get_archive(self):
        return self.archive
