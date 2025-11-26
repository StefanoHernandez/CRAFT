"""
Main Council implementation.
"""

from typing import List, Optional, Dict, Any
import logging

from craft.agents.agent import Agent
from craft.consensus.base import (
    CouncilConfig,
    CouncilResult,
    ConsensusStrategy
)
from craft.consensus.strategies.debate import DebateStrategy

logger = logging.getLogger(__name__)

class Council:
    """
    A Council of Agents that can deliberate and reach consensus.
    
    The Council coordinates the interaction between multiple agents according
    to a specified strategy (Debate, Voting, etc.).
    """
    
    def __init__(self, config: CouncilConfig):
        """
        Initialize the Council.
        
        Args:
            config: Council configuration
        """
        self.config = config
        self._validate_config()
        
    def _validate_config(self) -> None:
        """Validate configuration."""
        if not self.config.agents:
            raise ValueError("Council must have at least one agent.")
            
        if self.config.strategy in [ConsensusStrategy.DEBATE, ConsensusStrategy.HIERARCHICAL]:
            if not self.config.chairman:
                raise ValueError(f"Strategy {self.config.strategy} requires a Chairman agent.")

    async def deliberate(self, topic: str) -> CouncilResult:
        """
        Conduct a deliberation on a topic.
        
        Args:
            topic: The topic or question to deliberate on.
            
        Returns:
            CouncilResult containing the decision and rationale.
        """
        logger.info(f"Council '{self.config.name}' deliberating on: {topic}")
        
        if self.config.strategy == ConsensusStrategy.DEBATE:
            return await self._run_debate(topic)
        elif self.config.strategy == ConsensusStrategy.VOTING:
            return await self._run_voting(topic)
        else:
            raise NotImplementedError(f"Strategy {self.config.strategy} not yet implemented.")

    async def _run_debate(self, topic: str) -> CouncilResult:
        """Run a debate strategy."""
        strategy = DebateStrategy(
            agents=self.config.agents,
            chairman=self.config.chairman,  # type: ignore (validated in init)
            max_rounds=self.config.max_rounds,
            verbose=self.config.verbose
        )
        return await strategy.run(topic)

    async def _run_voting(self, topic: str) -> CouncilResult:
        """Run a simple voting strategy."""
        # TODO: Implement voting strategy
        raise NotImplementedError("Voting strategy not yet implemented")
