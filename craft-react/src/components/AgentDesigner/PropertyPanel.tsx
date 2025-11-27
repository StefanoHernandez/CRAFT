/**
 * Property Panel - Edit selected node properties
 */

import React from 'react';
import { X } from 'lucide-react';
import { useAgentDesigner } from './store';
import {
    AgentNodeConfig,
    ProviderNodeConfig,
    ToolNodeConfig,
    MemoryNodeConfig,
    OutputNodeConfig,
} from './types';
import { AgentPropertyForm } from './forms/AgentPropertyForm';
import { ProviderPropertyForm } from './forms/ProviderPropertyForm';
import { ToolPropertyForm } from './forms/ToolPropertyForm';
import { MemoryPropertyForm } from './forms/MemoryPropertyForm';
import { OutputPropertyForm } from './forms/OutputPropertyForm';

export function PropertyPanel() {
    const { workflow, selectedNode, selectNode, deleteNode } = useAgentDesigner();

    const selectedNodeData = workflow.nodes.find((n) => n.id === selectedNode);

    if (!selectedNode || !selectedNodeData) {
        return (
            <div className="w-80 bg-white border-l border-gray-200 p-4">
                <div className="text-center text-gray-500 mt-8">
                    <p className="text-sm">Select a node to edit its properties</p>
                </div>
            </div>
        );
    }

    const handleDelete = () => {
        deleteNode(selectedNode);
    };

    return (
        <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="font-semibold text-gray-800 capitalize">{selectedNodeData.type} Properties</h3>
                <button
                    onClick={() => selectNode(null)}
                    className="p-1 hover:bg-gray-100 rounded"
                >
                    <X className="w-4 h-4 text-gray-500" />
                </button>
            </div>

            {/* Form */}
            <div className="flex-1 overflow-y-auto p-4">
                {selectedNodeData.type === 'agent' && (
                    <AgentPropertyForm nodeId={selectedNode} config={selectedNodeData.data.config as AgentNodeConfig} />
                )}
                {selectedNodeData.type === 'provider' && (
                    <ProviderPropertyForm nodeId={selectedNode} config={selectedNodeData.data.config as ProviderNodeConfig} />
                )}
                {selectedNodeData.type === 'tool' && (
                    <ToolPropertyForm nodeId={selectedNode} config={selectedNodeData.data.config as ToolNodeConfig} />
                )}
                {selectedNodeData.type === 'memory' && (
                    <MemoryPropertyForm nodeId={selectedNode} config={selectedNodeData.data.config as MemoryNodeConfig} />
                )}
                {selectedNodeData.type === 'output' && (
                    <OutputPropertyForm nodeId={selectedNode} config={selectedNodeData.data.config as OutputNodeConfig} />
                )}

                {/* Connections Section */}
                <div className="mt-6 pt-6 border-t border-gray-200">
                    <h4 className="font-medium text-gray-800 mb-3">Connections</h4>
                    <ConnectionManager nodeId={selectedNode} />
                </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-200">
                <button
                    onClick={handleDelete}
                    className="w-full px-4 py-2 bg-red-50 text-red-600 rounded hover:bg-red-100 font-medium text-sm"
                >
                    Delete Node
                </button>
            </div>
        </div>
    );
}

function ConnectionManager({ nodeId }: { nodeId: string }) {
    const { workflow, addEdge, deleteEdge } = useAgentDesigner();
    const [targetId, setTargetId] = React.useState('');

    const outgoingEdges = workflow.edges.filter((e) => e.source === nodeId);
    const incomingEdges = workflow.edges.filter((e) => e.target === nodeId);

    // Filter potential targets: not self, not already connected
    // Filter potential targets based on strict rules
    const availableTargets = workflow.nodes.filter((n) => {
        if (n.id === nodeId) return false; // Self

        // Check if already connected
        const isConnected = outgoingEdges.some((e) => e.target === n.id);
        if (isConnected) return false;

        const sourceNode = workflow.nodes.find((node) => node.id === nodeId);
        if (!sourceNode) {
            console.warn('Source node not found:', nodeId);
            return false;
        }

        console.log(`Checking connection: ${sourceNode.type} (${sourceNode.id}) -> ${n.type} (${n.id})`);

        // 1. Provider -> Agent (Max 1 Provider per Agent)
        if (sourceNode.type === 'provider') {
            if (n.type !== 'agent') {
                console.log('Rejected: Provider can only connect to Agent');
                return false;
            }

            // Check if target agent already has a provider
            const agentIncomingEdges = workflow.edges.filter((e) => e.target === n.id);
            const hasProvider = agentIncomingEdges.some((e) => {
                const s = workflow.nodes.find((node) => node.id === e.source);
                return s?.type === 'provider';
            });
            if (hasProvider) {
                console.log('Rejected: Agent already has a provider');
                return false;
            }

            return true;
        }

        // 2. Memory -> Agent (Max 1 Memory per Agent)
        if (sourceNode.type === 'memory') {
            if (n.type !== 'agent') return false;

            // Check if target agent already has a memory
            const agentIncomingEdges = workflow.edges.filter((e) => e.target === n.id);
            const hasMemory = agentIncomingEdges.some((e) => {
                const s = workflow.nodes.find((node) => node.id === e.source);
                return s?.type === 'memory';
            });
            if (hasMemory) return false;

            return true;
        }

        // 3. Tool -> Agent (Multiple Tools allowed)
        if (sourceNode.type === 'tool') {
            return n.type === 'agent';
        }

        // 4. Agent -> Output or Agent
        if (sourceNode.type === 'agent') {
            if (n.type !== 'output' && n.type !== 'agent') return false;

            // If connecting to Output, ensure we don't already have an Output
            if (n.type === 'output') {
                const alreadyHasOutput = outgoingEdges.some((e) => {
                    const t = workflow.nodes.find((node) => node.id === e.target);
                    return t?.type === 'output';
                });
                if (alreadyHasOutput) return false;
            }

            return true;
        }

        // Output cannot connect to anything
        if (sourceNode.type === 'output') {
            return false;
        }

        return false;
    });

    const handleAddConnection = () => {
        if (!targetId) return;

        const edge = {
            id: `edge-${nodeId}-${targetId}`,
            source: nodeId,
            target: targetId,
        };

        // Use the store's addEdge which now uses reactflow's addEdge helper
        addEdge(edge);
        setTargetId('');
    };

    return (
        <div className="space-y-4">
            {/* Outgoing Connections */}
            <div>
                <label className="text-xs font-medium text-gray-500 uppercase mb-2 block">Outgoing</label>
                {outgoingEdges.length === 0 ? (
                    <p className="text-sm text-gray-400 italic">No outgoing connections</p>
                ) : (
                    <div className="space-y-2">
                        {outgoingEdges.map((edge) => {
                            const targetNode = workflow.nodes.find((n) => n.id === edge.target);
                            return (
                                <div key={edge.id} className="flex items-center justify-between bg-gray-50 p-2 rounded text-sm">
                                    <span className="truncate flex-1" title={targetNode?.data.label}>
                                        → {targetNode?.data.label || edge.target}
                                    </span>
                                    <button
                                        onClick={() => deleteEdge(edge.id)}
                                        className="text-red-500 hover:text-red-700 p-1"
                                        title="Disconnect"
                                    >
                                        <X className="w-3 h-3" />
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Add New Connection */}
            <div className="flex gap-2">
                <select
                    value={targetId}
                    onChange={(e) => setTargetId(e.target.value)}
                    className="flex-1 text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                    <option value="">Connect to...</option>
                    {availableTargets.map((node) => (
                        <option key={node.id} value={node.id}>
                            {node.data.label} ({node.type})
                        </option>
                    ))}
                </select>
                <button
                    onClick={handleAddConnection}
                    disabled={!targetId}
                    className="px-3 py-1 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Add
                </button>
            </div>

            {/* Incoming Connections (Read-only) */}
            <div>
                <label className="text-xs font-medium text-gray-500 uppercase mb-2 block">Incoming</label>
                {incomingEdges.length === 0 ? (
                    <p className="text-sm text-gray-400 italic">No incoming connections</p>
                ) : (
                    <div className="space-y-2">
                        {incomingEdges.map((edge) => {
                            const sourceNode = workflow.nodes.find((n) => n.id === edge.source);
                            return (
                                <div key={edge.id} className="flex items-center justify-between bg-gray-50 p-2 rounded text-sm text-gray-600">
                                    <span className="truncate flex-1" title={sourceNode?.data.label}>
                                        ← {sourceNode?.data.label || edge.source}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
