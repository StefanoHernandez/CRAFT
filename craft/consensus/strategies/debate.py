"""
Debate Strategy Implementation.

Inspired by "Machine Theory of Mind" and Karpathy's "Council of LLMs".
"""

from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass

from craft.agents.agent import Agent
from craft.consensus.base import CouncilResult

logger = logging.getLogger(__name__)

@dataclass
class DebateRound:
    """A single round of debate."""
    round_number: int
    statements: Dict[str, str]  # Agent Name -> Statement
    synthesis: Optional[str] = None # Chairman's synthesis

class DebateStrategy:
    """
    Implements a multi-round debate strategy.
    
    Flow:
    1. Initial Round: All agents give their initial opinion.
    2. Debate Rounds: Agents critique each other's views and refine their own.
    3. Synthesis: Chairman synthesizes the views into a final decision.
    """
    
    def __init__(
        self,
        agents: List[Agent],
        chairman: Agent,
        max_rounds: int = 3,
        verbose: bool = False
    ):
        self.agents = agents
        self.chairman = chairman
        self.max_rounds = max_rounds
        self.verbose = verbose
        self.transcript: List[DebateRound] = []

    async def run(self, topic: str) -> CouncilResult:
        """Execute the debate."""
        
        # 1. Initial Opinions
        initial_statements = {}
        for agent in self.agents:
            prompt = (
                f"Topic: {topic}\n\n"
                "Please provide your initial analysis and opinion on this topic. "
                "Be concise but thorough."
            )
            response = await agent.arun(prompt)
            initial_statements[agent.name] = response.text
            
        self.transcript.append(DebateRound(1, initial_statements))
        
        # 2. Debate Rounds
        current_round = 1
        consensus_reached = False
        
        while current_round < self.max_rounds and not consensus_reached:
            current_round += 1
            
            # Chairman synthesizes current state
            synthesis = await self._synthesize_round(topic, self.transcript[-1])
            self.transcript[-1].synthesis = synthesis
            
            # Agents react to synthesis and others' opinions
            round_statements = {}
            for agent in self.agents:
                prompt = (
                    f"Topic: {topic}\n"
                    f"Current Synthesis: {synthesis}\n"
                    "Other opinions:\n" + 
                    "\n".join([f"- {name}: {stmt}" for name, stmt in self.transcript[-1].statements.items() if name != agent.name]) +
                    "\n\nPlease critique these views and refine your own position. "
                    "Do you agree with the synthesis? If not, why?"
                )
                response = await agent.arun(prompt)
                round_statements[agent.name] = response.text
            
            self.transcript.append(DebateRound(current_round, round_statements))
            
            # Check for consensus (simplified: Chairman decides if convergence is sufficient)
            consensus_reached = await self._check_consensus(topic, round_statements)

        # 3. Final Decision
        final_decision = await self._make_final_decision(topic)
        
        return CouncilResult(
            decision=final_decision,
            rationale=f"Reached after {current_round} rounds of debate.",
            debate_transcript=[
                {
                    "round": r.round_number,
                    "statements": r.statements,
                    "synthesis": r.synthesis
                }
                for r in self.transcript
            ],
            consensus_reached=consensus_reached,
            iterations=current_round
        )

    async def _synthesize_round(self, topic: str, round_data: DebateRound) -> str:
        """Chairman synthesizes the round."""
        prompt = (
            f"Topic: {topic}\n\n"
            "Here are the opinions from the council members:\n" +
            "\n".join([f"- {name}: {stmt}" for name, stmt in round_data.statements.items()]) +
            "\n\nPlease synthesize these views. Identify common ground and key disagreements. "
            "Be objective."
        )
        response = await self.chairman.arun(prompt)
        return response.text

    async def _check_consensus(self, topic: str, statements: Dict[str, str]) -> bool:
        """Chairman checks if consensus has been reached."""
        prompt = (
            f"Topic: {topic}\n\n"
            "Latest statements:\n" +
            "\n".join([f"- {name}: {stmt}" for name, stmt in statements.items()]) +
            "\n\nDo these statements represent a consensus? "
            "Reply with just 'YES' or 'NO' followed by a brief explanation."
        )
        response = await self.chairman.arun(prompt)
        return response.text.strip().upper().startswith("YES")

    async def _make_final_decision(self, topic: str) -> str:
        """Chairman makes the final decision."""
        prompt = (
            f"Topic: {topic}\n\n"
            "Based on the entire debate history, please provide the final decision and a comprehensive rationale. "
            "Address the key points raised by all council members."
        )
        response = await self.chairman.arun(prompt)
        return response.text
