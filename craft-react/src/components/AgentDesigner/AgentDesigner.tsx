/**
 * Main AgentDesigner Component with React Flow Canvas
 */

import React, { useCallback } from 'react';
import ReactFlow, {
    MiniMap,
    Controls,
    Background,
    BackgroundVariant,
    Connection,
    NodeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { useAgentDesigner } from './store';
import { WorkflowEdge } from './types';
import { AgentNode, ProviderNode, ToolNode, MemoryNode, OutputNode } from './nodes';
import { NodePalette } from './NodePalette';
import { PropertyPanel } from './PropertyPanel';
import { Toolbar } from './Toolbar';



export function AgentDesigner() {
    const { workflow, addEdge: addEdgeToWorkflow, selectNode, onNodesChange, onEdgesChange } = useAgentDesigner();

    const nodeTypes = React.useMemo(() => ({
        agent: AgentNode,
        provider: ProviderNode,
        tool: ToolNode,
        memory: MemoryNode,
        output: OutputNode,
    }), []);

    console.log('AgentDesigner Rendered. Nodes:', workflow.nodes.length, 'Edges:', workflow.edges.length);

    const onConnect = useCallback(
        (params: Connection) => {
            console.log('onConnect triggered:', params);
            const edge: WorkflowEdge = {
                id: `edge-${params.source}-${params.target}`,
                source: params.source!,
                target: params.target!,
                sourceHandle: params.sourceHandle || undefined,
                targetHandle: params.targetHandle || undefined,
            };
            console.log('Adding edge:', edge);
            addEdgeToWorkflow(edge);
        },
        [addEdgeToWorkflow]
    );

    const isValidConnection = useCallback(
        (connection: Connection) => {
            console.log('isValidConnection called with:', connection);
            const sourceNode = workflow.nodes.find((n) => n.id === connection.source);
            const targetNode = workflow.nodes.find((n) => n.id === connection.target);

            console.log('Found nodes:', { source: sourceNode?.type, target: targetNode?.type });

            if (!sourceNode || !targetNode) return false;

            // Prevent self-connections
            if (sourceNode.id === targetNode.id) return false;

            // Define valid connections
            // Provider -> Agent
            if (sourceNode.type === 'provider' && targetNode.type === 'agent') return true;
            // Tool -> Agent
            if (sourceNode.type === 'tool' && targetNode.type === 'agent') return true;
            // Memory -> Agent
            if (sourceNode.type === 'memory' && targetNode.type === 'agent') return true;
            // Agent -> Output (future)
            if (sourceNode.type === 'agent' && targetNode.type === 'output') return true;
            // Agent -> Agent (for multi-agent workflows)
            if (sourceNode.type === 'agent' && targetNode.type === 'agent') return true;

            console.log('Invalid connection type pair');
            return false;
        },
        [workflow.nodes]
    );

    const onNodeClick = useCallback(
        (_event: React.MouseEvent, node: any) => {
            selectNode(node.id);
        },
        [selectNode]
    );

    const onPaneClick = useCallback(() => {
        selectNode(null);
    }, [selectNode]);

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Toolbar */}
            <Toolbar />

            <div className="flex flex-1 overflow-hidden">
                {/* Left Sidebar - Node Palette */}
                <NodePalette />

                {/* Main Canvas */}
                <div className="flex-1 relative">
                    <ReactFlow
                        nodes={workflow.nodes}
                        edges={workflow.edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onConnect={onConnect}
                        isValidConnection={isValidConnection}
                        onNodeClick={onNodeClick}
                        onPaneClick={onPaneClick}
                        nodeTypes={nodeTypes}
                        nodesDraggable={true}
                        nodesConnectable={true}
                        fitView
                        className="bg-white"
                    >
                        <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#ccc" />
                        <Controls />
                        <MiniMap
                            nodeColor={(node) => {
                                const colors: Record<string, string> = {
                                    agent: '#3b82f6',
                                    provider: '#10b981',
                                    tool: '#f59e0b',
                                    memory: '#8b5cf6',
                                    output: '#ef4444',
                                };
                                return colors[node.type!] || '#6b7280';
                            }}
                            className="bg-white border border-gray-300 rounded-lg"
                        />
                    </ReactFlow>
                </div>

                {/* Right Sidebar - Property Panel */}
                <PropertyPanel />
            </div>
        </div>
    );
}
