
import time

class UIDesignTeam:
    """
    UI Design & Development Team
    Generates prototypes, design specs, and frontend artifacts.
    """
    def __init__(self):
        self.prototypes = []

    def create_prototype(self, specs):
        """Create a UI prototype specification."""
        print(f"[UI] Creating prototype for: {specs}")
        
        prototype = {
            "name": specs if isinstance(specs, str) else specs.get("name", "Prototype"),
            "components": self._generate_components(specs),
            "color_scheme": self._suggest_colors(),
            "layout": "glassmorphism_dark",
            "typography": {"heading": "Inter 700", "body": "Inter 400", "mono": "JetBrains Mono 400"},
            "animations": ["fade-in", "slide-up", "hover-glow"],
            "created": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        self.prototypes.append(prototype)
        return prototype

    def _generate_components(self, specs):
        """Generate component list based on specs."""
        base_components = [
            {"name": "Sidebar", "type": "navigation", "responsive": True},
            {"name": "Header", "type": "layout", "responsive": True},
            {"name": "Content Area", "type": "layout", "responsive": True},
        ]
        
        if isinstance(specs, dict):
            if "dashboard" in str(specs).lower():
                base_components.extend([
                    {"name": "Stat Card", "type": "display", "responsive": True},
                    {"name": "Data Table", "type": "data", "responsive": True},
                    {"name": "Chart Widget", "type": "visualization", "responsive": True},
                ])
            if "chat" in str(specs).lower():
                base_components.extend([
                    {"name": "Message Bubble", "type": "chat", "responsive": True},
                    {"name": "Input Bar", "type": "input", "responsive": True},
                ])
        
        return base_components

    def _suggest_colors(self):
        """Suggest a premium Neon Glass color scheme."""
        return {
            "bg_primary": "rgba(10, 10, 15, 0.95)",
            "bg_secondary": "rgba(18, 18, 26, 0.8)",
            "accent_primary": "#8b5cf6",  # Vibrant Violet
            "accent_secondary": "#ec4899", # Neon Pink
            "bg_glass": "rgba(255, 255, 255, 0.03)",
            "border_glass": "rgba(255, 255, 255, 0.1)",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "text_primary": "#f8fafc",
            "text_secondary": "#94a3b8",
        }

    def generate_css(self, prototype):
        """Generate Neon Glass CSS for a prototype."""
        colors = prototype.get("color_scheme", self._suggest_colors())
        return f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=JetBrains+Mono&display=swap');

:root {{
    --bg-primary: {colors['bg_primary']};
    --bg-secondary: {colors['bg_secondary']};
    --accent: {colors['accent_primary']};
    --accent-alt: {colors['accent_secondary']};
    --glass: {colors['bg_glass']};
    --border-glass: {colors['border_glass']};
    --text: {colors['text_primary']};
    --text-dim: {colors['text_secondary']};
}}

body {{
    background: radial-gradient(circle at top right, #1e1b4b, #000);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    margin: 0;
    overflow: hidden;
}}

.glass-panel {{
    background: var(--glass);
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    border: 1px solid var(--border-glass);
    border-radius: 12px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}}

.neon-glow {{
    text-shadow: 0 0 10px var(--accent);
}}
"""

    def get_prototypes(self):
        return self.prototypes
