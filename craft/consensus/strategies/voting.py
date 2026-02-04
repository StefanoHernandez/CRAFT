"""
Voting Strategy Implementation.

Implements democratic decision-making for the Council.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from craft.agents.agent import Agent
from craft.consensus.base import CouncilResult

logger = logging.getLogger(__name__)

class VoteType(Enum):
    MAJORITY = "majority"
    CONSENSUS = "consensus"
    WEIGHTED = "weighted"

@dataclass
class VoteResult:
    """A single vote result."""
    agent_name: str
    choice: str
    rationale: str
    weight: float = 1.0

class VotingStrategy:
    """
    Implements a voting-based consensus strategy.
    
    Modes:
    1. Majority: The option with the most votes wins.
    2. Consensus: All agents must agree (unanimous).
    3. Weighted: Agents have different voting weights.
    """
    
    def __init__(
        self,
        agents: List[Agent],
        type: VoteType = VoteType.MAJORITY,
        weights: Optional[Dict[str, float]] = None
    ):
        self.agents = agents
        self.type = type
        self.weights = weights or {agent.name: 1.0 for agent in agents}

    async def run(self, topic: str, options: List[str]) -> CouncilResult:
        """Execute the voting process."""
        
        votes: List[VoteResult] = []
        options_str = ", ".join(options)
        
        # 1. Collect Votes
        for agent in self.agents:
            prompt = (
                f"Topic: {topic}\n"
                f"Options: {options_str}\n\n"
                "Please cast your vote. You must choose exactly one of the options above. "
                "Provide your decision in the format:\n"
                "VOTE: [Option]\n"
                "RATIONALE: [Brief explanation]"
            )
            
            response = await agent.arun(prompt)
            # Basic parsing logic (can be made more robust with structure)
            content = response.text
            choice = self._parse_vote(content, options)
            rationale = self._parse_rationale(content)
            
            votes.append(VoteResult(
                agent_name=agent.name,
                choice=choice,
                rationale=rationale,
                weight=self.weights.get(agent.name, 1.0)
            ))

        # 2. Tally Votes
        tally = self._tally_votes(votes)
        
        # 3. Determine Outcome
        winner, success = self._determine_winner(tally, len(self.agents))
        
        decision_text = f"Winner: {winner}" if success else "No consensus reached."
        if self.type == VoteType.CONSENSUS and not success:
             decision_text = "Consensus (Unanimous) not reached."

        return CouncilResult(
            decision=decision_text,
            rationale=f"Voting Tally: {tally}",
            debate_transcript=[
                {
                    "agent": v.agent_name,
                    "vote": v.choice,
                    "rationale": v.rationale
                } for v in votes
            ],
            consensus_reached=success,
            iterations=1 
        )

    def _parse_vote(self, content: str, options: List[str]) -> str:
        """Extract vote choice from response."""
        for line in content.split('\n'):
            if line.upper().startswith("VOTE:"):
                vote = line.split(":", 1)[1].strip()
                # Fuzzy match against options could go here
                return vote
        return "ABSTAIN"

    def _parse_rationale(self, content: str) -> str:
        """Extract rationale from response."""
        for line in content.split('\n'):
            if line.upper().startswith("RATIONALE:"):
                return line.split(":", 1)[1].strip()
        return "No rationale provided."

    def _tally_votes(self, votes: List[VoteResult]) -> Dict[str, float]:
        """Tally votes based on weights."""
        tally = {}
        for vote in votes:
            if vote.choice == "ABSTAIN":
                continue
            tally[vote.choice] = tally.get(vote.choice, 0) + vote.weight
        return tally

    def _determine_winner(self, tally: Dict[str, float], total_agents: int) -> tuple[Optional[str], bool]:
        """Determine if there is a winner based on strategy."""
        if not tally:
            return None, False

        sorted_results = sorted(tally.items(), key=lambda x: x[1], reverse=True)
        top_choice, top_score = sorted_results[0]

        if self.type == VoteType.MAJORITY or self.type == VoteType.WEIGHTED:
            # Simple plurality (or absolute majority check could be added)
            return top_choice, True

        elif self.type == VoteType.CONSENSUS:
            # All agents must vote for the same thing
            # Use total weight instead of assuming weight=1.0 for all agents
            total_weight = sum(self.weights.values())
            if len(tally) == 1 and top_score >= total_weight:
                return top_choice, True
            return None, False

        return None, False
