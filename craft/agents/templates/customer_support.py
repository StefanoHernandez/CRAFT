"""Customer Support Agent Template."""

from typing import Any, Dict, List, Optional

from craft.agents.templates.base import TemplateAgent
from craft.providers.base import Provider
from craft.tools.base import Tool


class CustomerSupportAgent(TemplateAgent):
    """
    Pre-configured Customer Support Agent.
    
    Specialized in handling user inquiries, troubleshooting, and providing helpful responses.
    """
    
    def __init__(
        self,
        name: str = "SupportBot",
        provider: Optional[Provider] = None,
        tools: Optional[List[Tool]] = None,
        tone: str = "friendly and professional",
        company_name: str = "our company",
        **kwargs: Any
    ):
        """
        Initialize Customer Support Agent.
        
        Args:
            name: Agent name (default: SupportBot)
            provider: LLM provider
            tools: List of tools
            tone: Desired tone of voice
            company_name: Name of the company being supported
            **kwargs: Additional config
        """
        self.tone = tone
        self.company_name = company_name
        super().__init__(name, provider, tools, **kwargs)
        
    def get_template_config(self) -> Dict[str, Any]:
        """Get template configuration."""
        return {
            "role": "Customer Support Specialist",
            "goal": f"Assist users with their inquiries about {self.company_name} efficiently and politely.",
            "backstory": (
                f"You are a helpful and patient support agent for {self.company_name}. "
                f"Your tone is always {self.tone}. "
                "You strive to resolve issues in the first interaction whenever possible. "
                "If you don't know the answer, you admit it and offer to escalate."
            ),
            "tools": []  # Add specific support tools here if available
        }
