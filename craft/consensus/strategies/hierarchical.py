"""
Hierarchical Strategy Implementation.

Inspired by CrewAI's hierarchical process.
A 'Manager' agent delegates tasks to 'Worker' agents and synthesizes their outputs.
"""

from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass

from craft.agents.agent import Agent
from craft.consensus.base import CouncilResult

logger = logging.getLogger(__name__)

class HierarchicalStrategy:
    """
    Implements a manager-worker delegation strategy.
    
    Structure:
    - Manager: Intelligent agent that plans and delegates.
    - Workers: Specialized agents that execute specific sub-tasks.
    
    Flow:
    1. Manager receives the high-level goal.
    2. Manager breaks it down and assigns sub-tasks to workers.
    3. Workers execute tasks (potentially in parallel).
    4. Manager receives results and synthesizes the final answer.
    """
    
    def __init__(
        self,
        manager: Agent,
        workers: List[Agent],
        verbose: bool = False
    ):
        self.manager = manager
        self.workers = workers # Workers are just Agents
        self.verbose = verbose
        # Map worker names to instances for easier lookup
        self.worker_map = {w.name: w for w in workers}

    async def run(self, goal: str) -> CouncilResult:
        """Execute the hierarchical process."""
        
        # 1. Manager Planning & Delegation
        delegation_plan = await self._manager_plan(goal)
        
        results = []
        
        # 2. Execution of Delegated Tasks
        # Note: This is a simplified sequential execution. 
        # Future: Use asyncio.gather for parallel worker execution found in plan.
        
        for task in delegation_plan.get('tasks', []):
            worker_name = task.get('assignee')
            instruction = task.get('instruction')
            
            worker = self.worker_map.get(worker_name)
            if worker:
                if self.verbose: 
                    print(f"Manager executing task via {worker_name}: {instruction}")
                    
                response = await worker.arun(instruction)
                results.append({
                    "worker": worker_name,
                    "task": instruction,
                    "output": response.text
                })
            else:
                 logger.warning(f"Manager assigned task to unknown worker: {worker_name}")

        # 3. Manager Synthesis
        final_output = await self._manager_synthesize(goal, results)
        
        return CouncilResult(
            decision=final_output,
            rationale="Hierarchical delegation and synthesis.",
            debate_transcript=results, # Reusing transcript field for results log
            consensus_reached=True, 
            iterations=1
        )

    async def _manager_plan(self, goal: str) -> Dict[str, Any]:
        """Manager decides how to split the work."""
        worker_list = ", ".join([f"{w.name} (Role: {w.role})" for w in self.workers])
        
        # We need structured output here. 
        # For now, we will ask for a specific format or usage of a 'delegate' tool if capable.
        # Simplified string parsing approach for this phase:
        
        prompt = (
            f"Goal: {goal}\n"
            f"Available Workers: {worker_list}\n\n"
            "You are the Project Manager. Break down this goal into sub-tasks for your workers.\n"
            "Respond with a generic plan format (JSON-like) or simple text instructions.\n"
            "Ideally, list exactly who does what."
        )
        
        # In a real impl, we'd enforce JSON schema or use a ToolCall for 'delegate'.
        # Here we mock the result to ensure the 'strategy' logic works, 
        # assuming the Manager is smart enough to use a tool if provided, 
        # or we parse the text.
        
        # For this prototype implementation, we'll assume a smart LLM and simple parsing,
        # or we instruct it to return a python dictionary.
        
        # Simple fix: Let's assume we implement a 'DelegateTool' later. 
        # For now, let's just use the workers in a round-robin or ask manager.
        
        # Mocking complex parsing for Prototype 1:
        # We will just ask the manager to SOLVE it, but giving it context of others.
        # Ideally, we want the manager to explicitly say: "Worker A, do X".
        pass 
        # REFACTOR: To make this robust without complex parsing, 
        # let's modify the Prompt to ask for a pipe-separated list: "WorkerName|TaskInstruction"
        
        prompt = (
            f"Goal: {goal}\n"
            f"Available Workers: {worker_list}\n\n"
            "Break this task down. Return a list of assignments, one per line, format: 'WORKER_NAME|INSTRUCTION'.\n"
            "Example:\n"
            "Researcher|Find data about X\n"
            "Writer|Write a summary"
        )
        
        response = await self.manager.arun(prompt)
        text = response.text
        
        tasks = []
        for line in text.split('\n'):
            if '|' in line:
                parts = line.split('|', 1)
                tasks.append({"assignee": parts[0].strip(), "instruction": parts[1].strip()})
                
        return {"tasks": tasks}

    async def _manager_synthesize(self, goal: str, results: List[Dict]) -> str:
        """Manager compiles the final answer."""
        results_text = "\n".join([f"[{r['worker']}]: {r['output']}" for r in results])
        
        prompt = (
            f"Original Goal: {goal}\n\n"
            f"Worker Results:\n{results_text}\n\n"
            "Synthesize these results into a final, coherent answer."
        )
        
        response = await self.manager.arun(prompt)
        return response.text
