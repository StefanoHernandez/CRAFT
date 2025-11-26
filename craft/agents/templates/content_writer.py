"""Content Writer Agent Template."""

from typing import Any, Dict, List, Optional

from craft.agents.templates.base import TemplateAgent
from craft.providers.base import Provider
from craft.tools.base import Tool


class ContentWriterAgent(TemplateAgent):
    """
    Pre-configured Content Writer Agent.
    
    Specialized in creating engaging content, blog posts, articles, and marketing copy.
    """
    
    def __init__(
        self,
        name: str = "Writer",
        provider: Optional[Provider] = None,
        tools: Optional[List[Tool]] = None,
        style: str = "engaging and informative",
        audience: str = "general audience",
        **kwargs: Any
    ):
        """
        Initialize Content Writer Agent.
        
        Args:
            name: Agent name (default: Writer)
            provider: LLM provider
            tools: List of tools
            style: Writing style
            audience: Target audience
            **kwargs: Additional config
        """
        self.style = style
        self.audience = audience
        super().__init__(name, provider, tools, **kwargs)
        
    def get_template_config(self) -> Dict[str, Any]:
        """Get template configuration."""
        return {
            "role": "Professional Content Writer",
            "goal": f"Write {self.style} content tailored for a {self.audience}.",
            "backstory": (
                "You are a creative writer with a talent for storytelling. "
                f"You adapt your style to be {self.style} to best engage your readers. "
                f"You understand the needs and interests of a {self.audience}. "
                "You prioritize clarity, originality, and correct grammar."
            ),
            "tools": []  # Add specific writing tools here if available
        }
