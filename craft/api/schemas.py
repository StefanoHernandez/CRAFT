from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class NodeData(BaseModel):
    id: str
    type: str
    name: str
    data: Dict[str, Any] = Field(default_factory=dict)

class RunNodeRequest(BaseModel):
    node: NodeData
    input: str = ""

class WorkflowData(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]] = Field(default_factory=list)

class ExportWorkflowRequest(BaseModel):
    workflow: WorkflowData
