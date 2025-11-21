"""Planning system for agents to break down complex tasks."""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from craft.providers.base import Provider, Message, Role


class Plan(BaseModel):
    """Agent's execution plan."""

    steps: List[str]
    current_step_index: int = 0
    completed_steps: List[int] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    revision_count: int = 0
    revision_history: List[str] = Field(default_factory=list)


async def generate_plan(
    provider: Provider,
    task_input: str,
    context: Optional[str] = None,
) -> Plan:
    """
    Generate an initial plan for a task using the LLM.

    Args:
        provider: LLM provider for plan generation
        task_input: Task description
        context: Optional additional context

    Returns:
        Plan with numbered steps
    """
    # Build planning prompt
    planning_prompt = _build_planning_prompt(task_input, context)

    # Call LLM to generate plan
    messages = [
        Message(role=Role.SYSTEM, content="You are a planning assistant. Break down tasks into clear, numbered steps."),
        Message(role=Role.USER, content=planning_prompt),
    ]

    response = await provider.achat(messages=messages, stream=False)

    # Parse response into steps
    steps = _parse_plan_steps(response.content)

    # Create and return plan
    plan = Plan(
        steps=steps,
        current_step_index=0,
        completed_steps=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    return plan


def generate_plan_sync(
    provider: Provider,
    task_input: str,
    context: Optional[str] = None,
) -> Plan:
    """
    Synchronous version of generate_plan.

    Args:
        provider: LLM provider for plan generation
        task_input: Task description
        context: Optional additional context

    Returns:
        Plan with numbered steps
    """
    # Build planning prompt
    planning_prompt = _build_planning_prompt(task_input, context)

    # Call LLM to generate plan
    messages = [
        Message(role=Role.SYSTEM, content="You are a planning assistant. Break down tasks into clear, numbered steps."),
        Message(role=Role.USER, content=planning_prompt),
    ]

    response = provider.chat(messages=messages, stream=False)

    # Parse response into steps
    steps = _parse_plan_steps(response.content)

    # Create and return plan
    plan = Plan(
        steps=steps,
        current_step_index=0,
        completed_steps=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    return plan


async def revise_plan(
    provider: Provider,
    current_plan: Plan,
    task_input: str,
    new_information: str,
) -> Plan:
    """
    Revise an existing plan based on new information.

    Args:
        provider: LLM provider for plan revision
        current_plan: Current plan to revise
        task_input: Original task description
        new_information: New information that requires plan revision

    Returns:
        Revised plan
    """
    # Build revision prompt
    revision_prompt = _build_revision_prompt(current_plan, task_input, new_information)

    # Call LLM to revise plan
    messages = [
        Message(role=Role.SYSTEM, content="You are a planning assistant. Revise plans based on new information."),
        Message(role=Role.USER, content=revision_prompt),
    ]

    response = await provider.achat(messages=messages, stream=False)

    # Parse response into steps
    new_steps = _parse_plan_steps(response.content)

    # Save old plan to history
    old_plan_summary = f"Revision {current_plan.revision_count}: {len(current_plan.steps)} steps"
    current_plan.revision_history.append(old_plan_summary)

    # Update plan
    current_plan.steps = new_steps
    current_plan.updated_at = datetime.now()
    current_plan.revision_count += 1

    # Keep completed steps that are still valid
    # Reset current step index if needed
    if current_plan.current_step_index >= len(new_steps):
        current_plan.current_step_index = len(new_steps) - 1 if new_steps else 0

    return current_plan


def revise_plan_sync(
    provider: Provider,
    current_plan: Plan,
    task_input: str,
    new_information: str,
) -> Plan:
    """
    Synchronous version of revise_plan.

    Args:
        provider: LLM provider for plan revision
        current_plan: Current plan to revise
        task_input: Original task description
        new_information: New information that requires plan revision

    Returns:
        Revised plan
    """
    # Build revision prompt
    revision_prompt = _build_revision_prompt(current_plan, task_input, new_information)

    # Call LLM to revise plan
    messages = [
        Message(role=Role.SYSTEM, content="You are a planning assistant. Revise plans based on new information."),
        Message(role=Role.USER, content=revision_prompt),
    ]

    response = provider.chat(messages=messages, stream=False)

    # Parse response into steps
    new_steps = _parse_plan_steps(response.content)

    # Save old plan to history
    old_plan_summary = f"Revision {current_plan.revision_count}: {len(current_plan.steps)} steps"
    current_plan.revision_history.append(old_plan_summary)

    # Update plan
    current_plan.steps = new_steps
    current_plan.updated_at = datetime.now()
    current_plan.revision_count += 1

    # Keep completed steps that are still valid
    # Reset current step index if needed
    if current_plan.current_step_index >= len(new_steps):
        current_plan.current_step_index = len(new_steps) - 1 if new_steps else 0

    return current_plan


def _build_planning_prompt(task_input: str, context: Optional[str] = None) -> str:
    """
    Build prompt for plan generation.

    Args:
        task_input: Task description
        context: Optional context

    Returns:
        Planning prompt
    """
    prompt = f"""Break down the following task into clear, numbered steps:

Task: {task_input}
"""

    if context:
        prompt += f"\nContext: {context}\n"

    prompt += """
Please provide a step-by-step plan. Format your response as:
1. [First step]
2. [Second step]
3. [Third step]
...

Keep steps clear, actionable, and focused on the task goal."""

    return prompt


def _build_revision_prompt(
    current_plan: Plan,
    task_input: str,
    new_information: str,
) -> str:
    """
    Build prompt for plan revision.

    Args:
        current_plan: Current plan
        task_input: Original task
        new_information: New information

    Returns:
        Revision prompt
    """
    # Format current plan
    current_steps = "\n".join(
        f"{i+1}. {step}" for i, step in enumerate(current_plan.steps)
    )

    # Mark completed steps
    completed_markers = []
    for i in current_plan.completed_steps:
        if i < len(current_plan.steps):
            completed_markers.append(f"Step {i+1} is completed")

    completed_info = "\n".join(completed_markers) if completed_markers else "No steps completed yet"

    prompt = f"""Revise the following plan based on new information:

Original Task: {task_input}

Current Plan:
{current_steps}

Completed Steps:
{completed_info}

New Information: {new_information}

Please provide a revised step-by-step plan. Format your response as:
1. [First step]
2. [Second step]
3. [Third step]
...

Keep steps clear, actionable, and adapt to the new information."""

    return prompt


def _parse_plan_steps(response_text: str) -> List[str]:
    """
    Parse plan steps from LLM response.

    Args:
        response_text: LLM response containing numbered steps

    Returns:
        List of step descriptions
    """
    steps = []
    lines = response_text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Look for numbered steps (1., 2., etc.)
        # Handle various formats: "1.", "1)", "Step 1:", etc.
        import re
        match = re.match(r"^(?:\d+[\.\):]|\*|\-)\s*(.+)$", line)
        if match:
            step_text = match.group(1).strip()
            if step_text:
                steps.append(step_text)

    # If no numbered steps found, treat each non-empty line as a step
    if not steps:
        steps = [line.strip() for line in lines if line.strip()]

    return steps


def mark_step_complete(plan: Plan, step_index: int) -> None:
    """
    Mark a step as complete in the plan.

    Args:
        plan: Plan to update
        step_index: Index of step to mark complete
    """
    if step_index not in plan.completed_steps:
        plan.completed_steps.append(step_index)
        plan.updated_at = datetime.now()


def advance_to_next_step(plan: Plan) -> bool:
    """
    Advance to the next step in the plan.

    Args:
        plan: Plan to update

    Returns:
        True if advanced, False if at end of plan
    """
    if plan.current_step_index < len(plan.steps) - 1:
        plan.current_step_index += 1
        plan.updated_at = datetime.now()
        return True
    return False


def get_current_step(plan: Plan) -> Optional[str]:
    """
    Get the current step description.

    Args:
        plan: Plan to query

    Returns:
        Current step description or None if plan is empty
    """
    if 0 <= plan.current_step_index < len(plan.steps):
        return plan.steps[plan.current_step_index]
    return None


def format_plan_for_display(plan: Plan) -> str:
    """
    Format plan for human-readable display.

    Args:
        plan: Plan to format

    Returns:
        Formatted plan string
    """
    lines = ["Plan:"]

    for i, step in enumerate(plan.steps):
        # Mark current step
        marker = "→" if i == plan.current_step_index else " "

        # Mark completed steps
        status = "✓" if i in plan.completed_steps else " "

        lines.append(f"{marker} {i+1}. [{status}] {step}")

    if plan.revision_count > 0:
        lines.append(f"\nRevisions: {plan.revision_count}")

    return "\n".join(lines)
