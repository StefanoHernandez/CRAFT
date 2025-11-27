/**
 * Agent Property Form
 */

import React from 'react';
import { useAgentDesigner } from '../store';
import { AgentNodeConfig } from '../types';

interface AgentPropertyFormProps {
    nodeId: string;
    config: AgentNodeConfig;
}

export function AgentPropertyForm({ nodeId, config }: AgentPropertyFormProps) {
    const { updateNode } = useAgentDesigner();

    const handleChange = (field: keyof AgentNodeConfig, value: any) => {
        updateNode(nodeId, {
            data: {
                label: 'Agent',
                config: { ...config, [field]: value },
            },
        });
    };

    return (
        <div className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name *
                </label>
                <input
                    type="text"
                    value={config.name || ''}
                    onChange={(e) => handleChange('name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="My Agent"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Role
                </label>
                <input
                    type="text"
                    value={config.role || ''}
                    onChange={(e) => handleChange('role', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Research Assistant"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Goal
                </label>
                <textarea
                    value={config.goal || ''}
                    onChange={(e) => handleChange('goal', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    rows={3}
                    placeholder="Find and summarize information"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Backstory
                </label>
                <textarea
                    value={config.backstory || ''}
                    onChange={(e) => handleChange('backstory', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    rows={3}
                    placeholder="You are an expert researcher..."
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Steps
                </label>
                <input
                    type="number"
                    value={config.max_steps || 10}
                    onChange={(e) => handleChange('max_steps', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min={1}
                    max={100}
                />
            </div>

            <div className="flex items-center">
                <input
                    type="checkbox"
                    id="verbose"
                    checked={config.verbose || false}
                    onChange={(e) => handleChange('verbose', e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="verbose" className="ml-2 text-sm text-gray-700">
                    Verbose output
                </label>
            </div>

            <div className="pt-4 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Connected Components</h4>
                <ConnectedComponentsList nodeId={nodeId} />
            </div>
        </div>
    );
}

function ConnectedComponentsList({ nodeId }: { nodeId: string }) {
    const { workflow } = useAgentDesigner();

    const incomingEdges = workflow.edges.filter(edge => edge.target === nodeId);
    const connectedNodes = incomingEdges.map(edge => workflow.nodes.find(n => n.id === edge.source)).filter(Boolean);

    if (connectedNodes.length === 0) {
        return <p className="text-xs text-gray-500 italic">No components connected. Drag connections from Provider, Tools, or Memory nodes.</p>;
    }

    return (
        <ul className="space-y-1">
            {connectedNodes.map((node, idx) => (
                <li key={idx} className="text-xs flex items-center gap-2 p-1.5 bg-gray-50 rounded border border-gray-100">
                    <span className={`w-2 h-2 rounded-full ${node!.type === 'provider' ? 'bg-green-500' :
                            node!.type === 'tool' ? 'bg-amber-500' :
                                node!.type === 'memory' ? 'bg-purple-500' : 'bg-gray-400'
                        }`} />
                    <span className="font-medium capitalize">{node!.type}:</span>
                    <span className="text-gray-600 truncate">{node!.data.config.name || node!.data.config.model || 'Unnamed'}</span>
                </li>
            ))}
        </ul>
    );
}
