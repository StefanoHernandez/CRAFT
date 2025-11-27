/**
 * Types for the Visual Agent Designer
 */

export interface AgentWorkflow {
    id: string;
    name: string;
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
    description?: string;
}

export interface WorkflowNode {
    id: string;
    type: NodeType;
    position: { x: number; y: number };
    data: NodeData;
}

export interface WorkflowEdge {
    id: string;
    source: string;
    target: string;
    sourceHandle?: string;
    targetHandle?: string;
}

export type NodeType =
    | 'agent'
    | 'provider'
    | 'tool'
    | 'memory'
    | 'output';

export interface NodeData {
    label: string;
    config: Record<string, any>;
}

export interface AgentNodeConfig {
    name: string;
    role?: string;
    goal?: string;
    backstory?: string;
    max_steps?: number;
    verbose?: boolean;
}

export interface ProviderNodeConfig {
    type: 'openai' | 'anthropic' | 'google' | 'ollama' | 'groq' | 'mistral';
    model: string;
    api_key?: string;
    temperature?: number;
    max_tokens?: number;
}

export interface ToolNodeConfig {
    name: string;
    description: string;
    type: 'builtin' | 'custom';
    function_name?: string;
}

export interface MemoryNodeConfig {
    enabled: boolean;
    max_messages?: number;
    max_tokens?: number;
    storage_type?: 'memory' | 'sqlite' | 'json';
    storage_path?: string;
}

export interface OutputNodeConfig {
    format: 'text' | 'json' | 'markdown';
    include_metadata?: boolean;
}
