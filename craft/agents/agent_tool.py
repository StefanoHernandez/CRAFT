"""AgentTool wrapper for agents-as-tools pattern.

Inspired by Datapizza AI's can_call() pattern, this allows one agent 
to delegate tasks to another agent as if it were a regular tool.
"""

from typing import Any, Dict
import time

from craft.tools.base import Tool, ToolMetadata, ToolParameter
from craft.agents.agent import Agent, AgentResult


class AgentTool(Tool):
    """
    Wraps an Agent as a Tool for multi-agent delegation.
    
    This enables the "agents-as-tools" pattern where one agent can call
    another agent to handle specialized sub-tasks. Inspired by Datapizza AI.
    
    Example:
        from craft.agents import Agent
        from craft.agents.agent_tool import AgentTool
        from craft.providers import OpenAIProvider
        
        provider = OpenAIProvider(api_key="...", model="gpt-4o")
        
        # Create specialist agent
        weather_expert = Agent(
            name="weather_expert",
            provider=provider,
            role="Weather Specialist",
            tools=[get_weather_tool]
        )
        
        # Create coordinator agent
        trip_planner = Agent(
            name="trip_planner",
            provider=provider,
            role="Trip Planner"
        )
        
        # Wrap specialist as tool
        weather_tool = AgentTool(weather_expert)
        trip_planner.tools.append(weather_tool)
        
        # Or use can_call() shortcut
        trip_planner.can_call(weather_expert)
    """
    
    def __init__(
        self,
        agent: Agent,
        name: str | None = None,
        description: str | None = None,
        max_delegation_depth: int = 3
    ):
        """
        Initialize AgentTool.
        
        Args:
            agent: The agent to wrap as a tool
            name: Optional tool name (defaults to "call_{agent.name}")
            description: Optional description (auto-generated if not provided)
            max_delegation_depth: Maximum delegation chain depth to prevent infinite recursion
        """
        self.agent = agent
        self.max_delegation_depth = max_delegation_depth
        
        # Auto-generate name and description
        tool_name = name or f"call_{agent.config.name}"
        tool_description = description or self._generate_description()
        
        # Create metadata
        metadata = ToolMetadata(
            name=tool_name,
            description=tool_description,
            parameters=[
                ToolParameter(
                    name="task",
                    type="string",
                    description=f"Task to delegate to {agent.config.name}",
                    required=True
                )
            ]
        )
        
        # Initialize base Tool
        super().__init__(
            func=self._execute_agent,
            metadata=metadata
        )
    
    def _generate_description(self) -> str:
        """Generate description from agent configuration."""
        parts = [f"Delegate a task to the {self.agent.config.name} agent."]
        
        if self.agent.config.role:
            parts.append(f"This agent is a {self.agent.config.role}.")
        
        if self.agent.config.goal:
            parts.append(f"Goal: {self.agent.config.goal}")
        
        return " ".join(parts)
    
    def _execute_agent(self, task: str, **kwargs: Any) -> str:
        """
        Execute the wrapped agent on the given task.
        
        Args:
            task: Task description to delegate
            **kwargs: Additional parameters for agent execution
        
        Returns:
            Agent's response text
        """
        # Check for infinite recursion
        if hasattr(self.agent, '_call_stack'):
            if len(self.agent._call_stack) >= self.max_delegation_depth:
                return (
                    f"Error: Maximum delegation depth ({self.max_delegation_depth}) reached. "
                    f"Call stack: {' → '.join(self.agent._call_stack)}"
                )
        
        # Track delegation for observability
        start_time = time.time()
        
        try:
            # Execute agent
            result: AgentResult = self.agent.run(task, **kwargs)
            
            # Track delegation metadata
            execution_time = time.time() - start_time
            
            # Return text result
            return result.text
            
        except Exception as e:
            return f"Error delegating to {self.agent.config.name}: {str(e)}"
    
    def execute(self, **kwargs: Any) -> str:
        """
        Execute method required by Tool base class.
        
        Args:
            **kwargs: Must include 'task' parameter
        
        Returns:
            Agent execution result
        """
        if 'task' not in kwargs:
            return f"Error: 'task' parameter is required for {self.name}"
        
        return self._execute_agent(**kwargs)


def create_agent_tool(
    agent: Agent,
    name: str | None = None,
    description: str | None = None
) -> AgentTool:
    """
    Helper function to create an AgentTool.
    
    Args:
        agent: Agent to wrap
        name: Optional tool name
        description: Optional description
    
    Returns:
        AgentTool instance
    """
    return AgentTool(agent=agent, name=name, description=description)
