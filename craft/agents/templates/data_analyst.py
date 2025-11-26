"""Data Analyst Agent Template."""

from typing import Any, Dict, List, Optional

from craft.agents.templates.base import TemplateAgent
from craft.providers.base import Provider
from craft.tools.base import Tool


class DataAnalystAgent(TemplateAgent):
    """
    Pre-configured Data Analyst Agent.
    
    Specialized in analyzing data sets, generating insights, and creating visualizations.
    """
    
    def __init__(
        self,
        name: str = "DataAnalyst",
        provider: Optional[Provider] = None,
        tools: Optional[List[Tool]] = None,
        expertise: str = "general data analysis",
        **kwargs: Any
    ):
        """
        Initialize Data Analyst Agent.
        
        Args:
            name: Agent name (default: DataAnalyst)
            provider: LLM provider
            tools: List of tools
            expertise: Specific area of expertise (e.g., financial, marketing)
            **kwargs: Additional config
        """
        self.expertise = expertise
        super().__init__(name, provider, tools, **kwargs)
        
    def get_template_config(self) -> Dict[str, Any]:
        """Get template configuration."""
        return {
            "role": "Senior Data Analyst",
            "goal": f"Analyze data to extract meaningful insights related to {self.expertise}.",
            "backstory": (
                "You are a meticulous data analyst who loves finding patterns in numbers. "
                f"Your expertise lies in {self.expertise}. "
                "You communicate complex data findings in clear, actionable terms. "
                "You always verify your assumptions and cite your data sources."
            ),
            "tools": []  # Add specific data tools here if available
        }
