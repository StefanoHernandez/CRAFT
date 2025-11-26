"""
Council Consensus System.

This module implements multi-agent consensus mechanisms inspired by:
1. "Machine Theory of Mind" (ToM)
2. Andrej Karpathy's "Council of LLMs" concept
3. Democratic voting systems

It allows multiple agents to debate, vote, and reach a consensus on complex problems.
"""

from typing import List, Optional, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

from craft.agents.agent import Agent

class ConsensusStrategy(str, Enum):
    """Available consensus strategies."""
    DEBATE = "debate"           # Multi-round debate with chairman synthesis
    VOTING = "voting"           # Simple majority/weighted voting
    PEER_REVIEW = "peer_review" # Blind peer review
    HIERARCHICAL = "hierarchical" # Chairman decides after hearing opinions

class CouncilConfig(BaseModel):
    """Configuration for the Council."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = "The Council"
    strategy: ConsensusStrategy = ConsensusStrategy.DEBATE
    agents: List[Agent]
    chairman: Optional[Agent] = None  # Required for DEBATE and HIERARCHICAL
    max_rounds: int = 3
    require_unanimity: bool = False
    verbose: bool = False

class CouncilResult(BaseModel):
    """Result of a council session."""
    decision: str
    rationale: str
    vote_counts: Optional[Dict[str, int]] = None
    debate_transcript: Optional[List[Dict[str, Any]]] = None
    consensus_reached: bool
    iterations: int
