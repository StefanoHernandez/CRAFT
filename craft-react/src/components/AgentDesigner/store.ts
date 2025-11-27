/**
 * Zustand store for Agent Designer state management
 */

import { create } from 'zustand';
import { applyNodeChanges, applyEdgeChanges, addEdge } from 'reactflow';
import type { NodeChange, EdgeChange } from 'reactflow';
import { AgentWorkflow, WorkflowNode, WorkflowEdge } from './types';

interface AgentDesignerState {
    workflow: AgentWorkflow;
    selectedNode: string | null;

    // Actions
    setWorkflow: (workflow: AgentWorkflow) => void;
    addNode: (node: WorkflowNode) => void;
    updateNode: (id: string, data: Partial<WorkflowNode>) => void;
    deleteNode: (id: string) => void;
    addEdge: (edge: WorkflowEdge) => void;
    deleteEdge: (id: string) => void;
    selectNode: (id: string | null) => void;
    clearWorkflow: () => void;
    onNodesChange: (changes: NodeChange[]) => void;
    onEdgesChange: (changes: EdgeChange[]) => void;
}

const defaultWorkflow: AgentWorkflow = {
    id: 'new-workflow',
    name: 'New Agent',
    nodes: [],
    edges: [],
};

export const useAgentDesigner = create<AgentDesignerState>((set) => ({
    workflow: defaultWorkflow,
    selectedNode: null,

    setWorkflow: (workflow) => set({ workflow }),

    addNode: (node) =>
        set((state) => ({
            workflow: {
                ...state.workflow,
                nodes: [...state.workflow.nodes, node],
            },
        })),

    updateNode: (id, data) =>
        set((state) => ({
            workflow: {
                ...state.workflow,
                nodes: state.workflow.nodes.map((node) =>
                    node.id === id ? { ...node, ...data } : node
                ),
            },
        })),

    deleteNode: (id) =>
        set((state) => ({
            workflow: {
                ...state.workflow,
                nodes: state.workflow.nodes.filter((node) => node.id !== id),
                edges: state.workflow.edges.filter(
                    (edge) => edge.source !== id && edge.target !== id
                ),
            },
            selectedNode: state.selectedNode === id ? null : state.selectedNode,
        })),

    addEdge: (edge) =>
        set((state) => ({
            workflow: {
                ...state.workflow,
                edges: addEdge(edge, state.workflow.edges) as WorkflowEdge[],
            },
        })),

    deleteEdge: (id) =>
        set((state) => ({
            workflow: {
                ...state.workflow,
                edges: state.workflow.edges.filter((edge) => edge.id !== id),
            },
        })),

    selectNode: (id) => set({ selectedNode: id }),

    clearWorkflow: () => set({ workflow: defaultWorkflow, selectedNode: null }),

    onNodesChange: (changes) =>
        set((state) => ({
            workflow: {
                ...state.workflow,
                nodes: applyNodeChanges(changes, state.workflow.nodes) as WorkflowNode[],
            },
        })),

    onEdgesChange: (changes) =>
        set((state) => ({
            workflow: {
                ...state.workflow,
                edges: applyEdgeChanges(changes, state.workflow.edges) as WorkflowEdge[],
            },
        })),
}));
