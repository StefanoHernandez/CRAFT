/**
 * Custom Agent Node for React Flow
 */

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { User, Brain, Database, Wrench } from 'lucide-react';
import { useAgentDesigner } from '../store';

export function AgentNode({ id, data, selected }: NodeProps) {
    const { workflow } = useAgentDesigner();

    // Check for connected components
    const incomingEdges = workflow.edges.filter(edge => edge.target === id);
    const connectedNodes = incomingEdges.map(edge => workflow.nodes.find(n => n.id === edge.source));

    const hasProvider = connectedNodes.some(n => n?.type === 'provider');
    const hasMemory = connectedNodes.some(n => n?.type === 'memory');
    const toolCount = connectedNodes.filter(n => n?.type === 'tool').length;

    return (
        <div
            className={`px-4 py-3 rounded-lg border-2 bg-white shadow-md min-w-[200px] ${selected ? 'border-blue-500' : 'border-gray-300'
                }`}
        >
            <Handle type="target" position={Position.Left} className="w-3 h-3" />

            <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <User className="w-4 h-4 text-blue-600" />
                </div>
                <div>
                    <div className="font-semibold text-sm">Agent</div>
                    <div className="text-xs text-gray-500">{data.config?.name || 'Unnamed Agent'}</div>
                </div>
            </div>

            {/* Connection Indicators */}
            <div className="flex gap-2 mt-2 border-t pt-2">
                {hasProvider ? (
                    <div className="flex items-center gap-1 text-xs text-green-600 bg-green-50 px-1.5 py-0.5 rounded" title="Provider Connected">
                        <Brain className="w-3 h-3" />
                        <span>LLM</span>
                    </div>
                ) : (
                    <div className="flex items-center gap-1 text-xs text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded" title="No Provider">
                        <Brain className="w-3 h-3" />
                        <span>Missing</span>
                    </div>
                )}

                {hasMemory && (
                    <div className="flex items-center gap-1 text-xs text-purple-600 bg-purple-50 px-1.5 py-0.5 rounded" title="Memory Attached">
                        <Database className="w-3 h-3" />
                        <span>Mem</span>
                    </div>
                )}

                {toolCount > 0 && (
                    <div className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded" title={`${toolCount} Tools Connected`}>
                        <Wrench className="w-3 h-3" />
                        <span>{toolCount}</span>
                    </div>
                )}
            </div>

            {data.config?.role && (
                <div className="text-xs text-gray-600 mt-2">
                    <span className="font-medium">Role:</span> {data.config.role}
                </div>
            )}

            <Handle type="source" position={Position.Right} className="w-3 h-3" />
        </div>
    );
}
