"""Research Agent Template."""

from typing import Any, Dict, List, Optional

from craft.agents.templates.base import TemplateAgent
from craft.providers.base import Provider
from craft.tools.base import Tool


class ResearchAgent(TemplateAgent):
    """
    Pre-configured Research Agent.
    
    Specialized in conducting thorough research, synthesizing information, and providing comprehensive reports.
    """
    
    def __init__(
        self,
        name: str = "Researcher",
        provider: Optional[Provider] = None,
        tools: Optional[List[Tool]] = None,
        depth: str = "comprehensive",
        **kwargs: Any
    ):
        """
        Initialize Research Agent.
        
        Args:
            name: Agent name (default: Researcher)
            provider: LLM provider
            tools: List of tools
            depth: Depth of research (e.g., brief, comprehensive, academic)
            **kwargs: Additional config
        """
        self.depth = depth
        super().__init__(name, provider, tools, **kwargs)
        
    def get_template_config(self) -> Dict[str, Any]:
        """Get template configuration."""
        return {
            "role": "Lead Research Analyst",
            "goal": f"Conduct {self.depth} research on assigned topics and provide accurate summaries.",
            "backstory": (
                "You are a diligent researcher with a passion for learning. "
                "You are skilled at finding reliable sources and synthesizing information from multiple perspectives. "
                f"You prefer to provide {self.depth} reports. "
                "You always fact-check your information and avoid speculation."
            ),
            "tools": []  # Add specific search tools here if available
        }
