/**
 * Output Property Form
 */

import React from 'react';
import { useAgentDesigner } from '../store';
import { OutputNodeConfig } from '../types';

interface OutputPropertyFormProps {
    nodeId: string;
    config: OutputNodeConfig;
}

export function OutputPropertyForm({ nodeId, config }: OutputPropertyFormProps) {
    const { updateNode } = useAgentDesigner();

    const handleChange = (field: keyof OutputNodeConfig, value: any) => {
        updateNode(nodeId, {
            data: {
                label: 'Output',
                config: { ...config, [field]: value },
            },
        });
    };

    return (
        <div className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Output Format
                </label>
                <select
                    value={config.format || 'text'}
                    onChange={(e) => handleChange('format', e.target.value as any)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                    <option value="text">Plain Text</option>
                    <option value="json">JSON</option>
                    <option value="markdown">Markdown</option>
                </select>
            </div>

            <div className="flex items-center">
                <input
                    type="checkbox"
                    id="include_metadata"
                    checked={config.include_metadata || false}
                    onChange={(e) => handleChange('include_metadata', e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="include_metadata" className="ml-2 text-sm text-gray-700">
                    Include metadata in output
                </label>
            </div>

            <div className="p-3 bg-gray-50 rounded border border-gray-200">
                <p className="text-xs text-gray-600">
                    <strong>Note:</strong> Output configuration affects how the agent's response is formatted and returned.
                </p>
            </div>
        </div>
    );
}
