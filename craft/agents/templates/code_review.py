"""Code Review Agent Template."""

from typing import Any, Dict, List, Optional

from craft.agents.templates.base import TemplateAgent
from craft.providers.base import Provider
from craft.tools.base import Tool


class CodeReviewAgent(TemplateAgent):
    """
    Pre-configured Code Review Agent.
    
    Specialized in analyzing code, finding bugs, suggesting improvements, and enforcing style guides.
    """
    
    def __init__(
        self,
        name: str = "CodeReviewer",
        provider: Optional[Provider] = None,
        tools: Optional[List[Tool]] = None,
        language: str = "Python",
        focus: str = "readability and performance",
        **kwargs: Any
    ):
        """
        Initialize Code Review Agent.
        
        Args:
            name: Agent name (default: CodeReviewer)
            provider: LLM provider
            tools: List of tools
            language: Primary programming language to review
            focus: Main focus area (e.g., security, performance)
            **kwargs: Additional config
        """
        self.language = language
        self.focus = focus
        super().__init__(name, provider, tools, **kwargs)
        
    def get_template_config(self) -> Dict[str, Any]:
        """Get template configuration."""
        return {
            "role": f"Senior {self.language} Software Engineer",
            "goal": f"Review {self.language} code to ensure high quality, focusing on {self.focus}.",
            "backstory": (
                f"You are an expert {self.language} developer with years of experience. "
                "You have a keen eye for detail and a deep understanding of software architecture. "
                "You provide constructive feedback, explaining 'why' behind your suggestions. "
                "You prioritize clean, maintainable, and efficient code."
            ),
            "tools": []  # Add specific code analysis tools here if available
        }
