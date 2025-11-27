/**
 * Tool Property Form
 */

import React from 'react';
import { useAgentDesigner } from '../store';
import { ToolNodeConfig } from '../types';

interface ToolPropertyFormProps {
    nodeId: string;
    config: ToolNodeConfig;
}

const builtinTools = [
    'search_web',
    'calculator',
    'read_file',
    'write_file',
    'send_email',
    'http_request',
];

export function ToolPropertyForm({ nodeId, config }: ToolPropertyFormProps) {
    const { updateNode } = useAgentDesigner();

    const handleChange = (field: keyof ToolNodeConfig, value: any) => {
        updateNode(nodeId, {
            data: {
                label: 'Tool',
                config: { ...config, [field]: value },
            },
        });
    };

    return (
        <div className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tool Type
                </label>
                <select
                    value={config.type || 'builtin'}
                    onChange={(e) => handleChange('type', e.target.value as 'builtin' | 'custom')}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                    <option value="builtin">Built-in</option>
                    <option value="custom">Custom</option>
                </select>
            </div>

            {config.type === 'builtin' ? (
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Tool Name *
                    </label>
                    <select
                        value={config.name || ''}
                        onChange={(e) => handleChange('name', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                        <option value="">Select a tool...</option>
                        {builtinTools.map((tool) => (
                            <option key={tool} value={tool}>
                                {tool}
                            </option>
                        ))}
                    </select>
                </div>
            ) : (
                <>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Function Name *
                        </label>
                        <input
                            type="text"
                            value={config.function_name || ''}
                            onChange={(e) => handleChange('function_name', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="my_custom_tool"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Tool Name *
                        </label>
                        <input
                            type="text"
                            value={config.name || ''}
                            onChange={(e) => handleChange('name', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="My Custom Tool"
                        />
                    </div>
                </>
            )}

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                </label>
                <textarea
                    value={config.description || ''}
                    onChange={(e) => handleChange('description', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    rows={3}
                    placeholder="What this tool does..."
                />
            </div>
        </div>
    );
}
