"""Collaboration utilities for multi-agent delegation.

Questo modulo isola la logica di:
- registrare altri Agent come strumenti delegabili
- prevenire chiamate ricorsive tra agenti
- aggregare risultati e metadati delle chiamate delegate

In questo modo la classe `Agent` rimane focalizzata su:
- configurazione
- gestione dello stato locale
- orchestrazione dell'esecuzione
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from craft.core.errors import AgentExecutionError
from craft.tools.base import Tool, ToolMetadata, ToolParameter

if TYPE_CHECKING:
    from craft.agents.agent import Agent


class CollaborationManager:
    """Gestisce la collaborazione multi-agente per un Agent coordinatore."""

    def __init__(self, owner: "Agent") -> None:
        """
        Args:
            owner: l'agente che delega ad altri agenti.
        """
        self._owner = owner
        # Mappa nome-strumento -> Agent delegato
        self._callable_agents: Dict[str, "Agent"] = {}
        # Stack per rilevare chiamate ricorsive tra agenti
        self._call_stack: List[str] = []
        # Risultati aggregati di tutte le chiamate delegate
        self._aggregated_results: Dict[str, Any] = {
            "agent_calls": [],
            "total_steps": 0,
            "total_tools_used": set(),
            "total_execution_time": 0.0,
        }

    # ------------------------------------------------------------------
    # API pubblica usata da Agent
    # ------------------------------------------------------------------
    def register_agents(self, agents: List["Agent"]) -> List[Tool]:
        """Registra altri agenti come strumenti usando il loro `name` come nome tool."""
        new_tools: List[Tool] = []
        for agent in agents:
            tool_name = agent.config.name
            self._callable_agents[tool_name] = agent
            new_tools.append(self._create_agent_tool(agent, tool_name))
        return new_tools

    def register_agents_map(self, agents_map: Dict[str, "Agent"]) -> List[Tool]:
        """Registra agenti con nomi di tool personalizzati."""
        new_tools: List[Tool] = []
        for tool_name, agent in agents_map.items():
            self._callable_agents[tool_name] = agent
            new_tools.append(self._create_agent_tool(agent, tool_name))
        return new_tools

    def get_aggregated_results(self) -> Dict[str, Any]:
        """Restituisce una vista serializzabile dei risultati aggregati."""
        # Copia shallow per evitare modifiche esterne allo stato interno
        results = dict(self._aggregated_results)
        # Convertiamo il set in lista per compatibilità JSON
        if isinstance(results.get("total_tools_used"), set):
            results["total_tools_used"] = list(results["total_tools_used"])
        return results

    def reset(self) -> None:
        """Reimposta i risultati aggregati (da usare a inizio esecuzione)."""
        self._aggregated_results = {
            "agent_calls": [],
            "total_steps": 0,
            "total_tools_used": set(),
            "total_execution_time": 0.0,
        }

    # ------------------------------------------------------------------
    # Implementazione: creazione dei tool wrapper
    # ------------------------------------------------------------------
    def _create_agent_tool(self, agent: "Agent", tool_name: str) -> Tool:
        """
        Crea un Tool che, quando invocato, esegue l'agente delegato con un task.

        Il tool espone un'unica proprietà `task: str`.
        """
        description_parts = [f"Delegate to {agent.config.name}"]
        if agent.config.role:
            description_parts.append(f"(Role: {agent.config.role})")
        if agent.config.goal:
            description_parts.append(f"to {agent.config.goal}")
        description = " ".join(description_parts)

        metadata = ToolMetadata(
            name=tool_name,
            description=description,
            parameters=[
                ToolParameter(
                    name="task",
                    type="str",
                    description="The task or question to give to the delegated agent",
                    required=True,
                )
            ],
            return_type="str",
            json_schema={
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {
                                "type": "string",
                                "description": "The task or question to give to the delegated agent",
                            }
                        },
                        "required": ["task"],
                    },
                },
            },
        )

        def agent_wrapper(task: str) -> str:
            """Esegue l'agente delegato con il task specificato."""
            delegated_name = agent.config.name

            # Rileva cicli: A -> B -> A
            if delegated_name in self._call_stack:
                raise AgentExecutionError(
                    f"Circular agent call detected: "
                    f"{' -> '.join(self._call_stack)} -> {delegated_name}",
                    details={
                        "call_stack": list(self._call_stack),
                        "attempted_agent": delegated_name,
                    },
                )

            self._call_stack.append(delegated_name)
            try:
                # Esegui l'agente delegato
                result = agent.run(task)

                # Registra la chiamata
                self._aggregated_results["agent_calls"].append(
                    {
                        "agent_name": delegated_name,
                        "delegated_as": tool_name,
                        "task": task,
                        "result": result.text,
                        "steps": result.total_steps,
                        "tools_used": result.tools_used,
                        "metadata": result.metadata,
                    }
                )

                # Aggiorna aggregati
                self._aggregated_results["total_steps"] += result.total_steps
                self._aggregated_results["total_tools_used"].update(result.tools_used)
                self._aggregated_results["total_execution_time"] += result.metadata.get(
                    "execution_time_seconds", 0.0
                )

                return result.text
            finally:
                # Pop dallo stack anche in caso di errore
                self._call_stack.pop()

        return Tool(
            name=tool_name,
            description=description,
            func=agent_wrapper,
            metadata=metadata,
        )

