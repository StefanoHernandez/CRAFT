/**
 * Node Palette - Sidebar for dragging new nodes onto canvas
 */

import React from 'react';
import { User, Cpu, Wrench, Database, FileOutput } from 'lucide-react';
import { useAgentDesigner } from './store';
import { WorkflowNode, NodeType } from './types';

interface NodeTemplate {
    type: NodeType;
    label: string;
    icon: React.ReactNode;
    description: string;
    defaultConfig: Record<string, any>;
}

const nodeTemplates: NodeTemplate[] = [
    {
        type: 'agent',
        label: 'Agent',
        icon: <User className="w-5 h-5" />,
        description: 'Main agent configuration',
        defaultConfig: { name: 'My Agent', role: '', goal: '', max_steps: 10 },
    },
    {
        type: 'provider',
        label: 'Provider',
        icon: <Cpu className="w-5 h-5" />,
        description: 'LLM provider (OpenAI, Anthropic, etc.)',
        defaultConfig: { type: 'openai', model: 'gpt-4o' },
    },
    {
        type: 'tool',
        label: 'Tool',
        icon: <Wrench className="w-5 h-5" />,
        description: 'Add tools to your agent',
        defaultConfig: { name: 'search_web', type: 'builtin', description: 'Search the web' },
    },
    {
        type: 'memory',
        label: 'Memory',
        icon: <Database className="w-5 h-5" />,
        description: 'Conversation memory',
        defaultConfig: { enabled: true, max_messages: 50, storage_type: 'memory' },
    },
    {
        type: 'output',
        label: 'Output',
        icon: <FileOutput className="w-5 h-5" />,
        description: 'Configure output format',
        defaultConfig: { format: 'text', include_metadata: false },
    },
];

export function NodePalette() {
    const { addNode, workflow } = useAgentDesigner();

    const handleAddNode = (template: NodeTemplate) => {
        // Calculate a somewhat random position to avoid stacking
        const randomOffset = Math.floor(Math.random() * 200);
        const nodeCount = workflow.nodes.filter(n => n.type === template.type).length;

        const newNode: WorkflowNode = {
            id: `${template.type}-${Date.now()}`,
            type: template.type,
            position: {
                x: 250 + randomOffset,
                y: 150 + (nodeCount * 120)
            },
            data: {
                label: template.label,
                config: template.defaultConfig,
            },
        };
        addNode(newNode);
    };

    return (
        <div className="w-64 bg-white border-r border-gray-200 p-4 overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4 text-gray-800">Components</h2>

            <div className="space-y-2">
                {nodeTemplates.map((template) => (
                    <button
                        key={template.type}
                        onClick={() => handleAddNode(template)}
                        className="w-full p-3 border-2 border-gray-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-colors text-left group"
                    >
                        <div className="flex items-center gap-2 mb-1">
                            <div className="text-gray-600 group-hover:text-blue-600">
                                {template.icon}
                            </div>
                            <span className="font-medium text-gray-800">{template.label}</span>
                        </div>
                        <p className="text-xs text-gray-500">{template.description}</p>
                    </button>
                ))}
            </div>

            <div className="mt-6 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-xs text-blue-800">
                    <strong>Tip:</strong> Click on a component to add it to the canvas. Connect nodes by dragging from one handle to another.
                </p>
            </div>
        </div>
    );
}
