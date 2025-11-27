/**
 * Memory Property Form
 */

import React from 'react';
import { useAgentDesigner } from '../store';
import { MemoryNodeConfig } from '../types';

interface MemoryPropertyFormProps {
    nodeId: string;
    config: MemoryNodeConfig;
}

export function MemoryPropertyForm({ nodeId, config }: MemoryPropertyFormProps) {
    const { updateNode } = useAgentDesigner();

    const handleChange = (field: keyof MemoryNodeConfig, value: any) => {
        updateNode(nodeId, {
            data: {
                label: 'Memory',
                config: { ...config, [field]: value },
            },
        });
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center">
                <input
                    type="checkbox"
                    id="enabled"
                    checked={config.enabled ?? true}
                    onChange={(e) => handleChange('enabled', e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="enabled" className="ml-2 text-sm font-medium text-gray-700">
                    Enable Memory
                </label>
            </div>

            {config.enabled && (
                <>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Storage Type
                        </label>
                        <select
                            value={config.storage_type || 'memory'}
                            onChange={(e) => handleChange('storage_type', e.target.value as any)}
                            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value="memory">In-Memory</option>
                            <option value="sqlite">SQLite</option>
                            <option value="json">JSON File</option>
                        </select>
                    </div>

                    {(config.storage_type === 'sqlite' || config.storage_type === 'json') && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Storage Path
                            </label>
                            <input
                                type="text"
                                value={config.storage_path || ''}
                                onChange={(e) => handleChange('storage_path', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                placeholder={config.storage_type === 'sqlite' ? 'agent.db' : 'agent.json'}
                            />
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Max Messages
                        </label>
                        <input
                            type="number"
                            value={config.max_messages || ''}
                            onChange={(e) => handleChange('max_messages', parseInt(e.target.value) || undefined)}
                            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="50"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            Maximum number of messages to keep
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Max Tokens
                        </label>
                        <input
                            type="number"
                            value={config.max_tokens || ''}
                            onChange={(e) => handleChange('max_tokens', parseInt(e.target.value) || undefined)}
                            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="2000"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            Maximum tokens to keep in context
                        </p>
                    </div>
                </>
            )}
        </div>
    );
}
