
import time
from typing import List, Optional, Any, Callable
from pydantic import BaseModel, ConfigDict

from craft.core.errors import AgentExecutionError, ToolExecutionError
from craft.tracing import tracer
from craft.agents.types import StepResult, AgentResult

class ExecutionEngine:
    """
    Handles the execution loop for an agent, managing steps, max_steps, and termination.
    """

    def __init__(self, max_steps: int = 10):
        self.max_steps = max_steps
    
    def run_loop(
        self, 
        step_executor: Callable[[], StepResult],
        should_continue: Callable[[], bool],
        on_step_complete: Callable[[StepResult], None] = None
    ) -> List[StepResult]:
        """
        Execute the main agent loop.
        
        Args:
            step_executor: Function that executes a single step and returns StepResult
            should_continue: Function returning True if execution should continue
            on_step_complete: Optional callback after each step
            
        Returns:
            List of StepResult objects from the execution
        """
        step_results: List[StepResult] = []
        current_step = 0
        
        start_time = time.time()
        
        try:
            while current_step < self.max_steps and should_continue():
                
                with tracer.span(f"agent.step.{current_step + 1}"):
                    # Execute single step
                    step_result = step_executor()
                    step_results.append(step_result)
                    
                    if on_step_complete:
                        on_step_complete(step_result)
                
                if step_result.finished:
                    break
                    
                current_step += 1
                
        except Exception as e:
            # Re-raise or handle, for now we re-raise as AgentExecutionError is expected by caller
            raise e
            
        return step_results

