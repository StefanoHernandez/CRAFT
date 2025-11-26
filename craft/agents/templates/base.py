"""Base class for Agent Templates."""

from typing import Any, Dict, List, Optional, Union
from pydantic import Field, ConfigDict

from craft.agents.agent import Agent, AgentConfig
from craft.providers.base import Provider
from craft.tools.base import Tool


class TemplateAgent(Agent):
    """
    Base class for pre-configured Agent Templates.
    
    Templates provide a simplified interface for creating specialized agents
    with pre-defined roles, goals, and tools.
    """
    
    def __init__(
        self,
        name: str,
        provider: Optional[Provider] = None,
        tools: Optional[List[Tool]] = None,
        **kwargs: Any
    ):
        """
        Initialize a Template Agent.
        
        Args:
            name: Agent name
            provider: LLM provider (optional, can use default)
            tools: List of tools (optional, will be merged with template tools)
            **kwargs: Additional configuration overrides
        """
        # Get template-specific defaults
        template_config = self.get_template_config()
        
        # Merge tools
        template_tools = template_config.pop("tools", [])
        if tools:
            template_tools.extend(tools)
            
        # Merge configuration
        config_data = {
            "name": name,
            "role": template_config.get("role", "Assistant"),
            "goal": template_config.get("goal", "Help the user"),
            "backstory": template_config.get("backstory", ""),
            "provider": provider,
            "tools": template_tools,
            **kwargs
        }
        
        # Initialize base Agent
        super().__init__(**config_data)
        
    def get_template_config(self) -> Dict[str, Any]:
        """
        Get template-specific configuration.
        
        Returns:
            Dictionary with 'role', 'goal', 'backstory', and 'tools'.
        """
        raise NotImplementedError("Subclasses must implement get_template_config")
