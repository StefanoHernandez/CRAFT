/**
 * Custom Provider Node for React Flow
 */

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Cpu } from 'lucide-react';

export function ProviderNode({ data, selected }: NodeProps) {
    const providerColors: Record<string, string> = {
        openai: 'bg-green-100 text-green-700',
        anthropic: 'bg-orange-100 text-orange-700',
        google: 'bg-blue-100 text-blue-700',
        ollama: 'bg-purple-100 text-purple-700',
        groq: 'bg-pink-100 text-pink-700',
        mistral: 'bg-indigo-100 text-indigo-700',
    };

    const colorClass = providerColors[data.config?.type] || 'bg-gray-100 text-gray-700';

    return (
        <div
            className={`px-4 py-3 rounded-lg border-2 bg-white shadow-md min-w-[200px] ${selected ? 'border-blue-500' : 'border-gray-300'
                }`}
        >
            <Handle type="target" position={Position.Left} className="w-3 h-3" />

            <div className="flex items-center gap-2 mb-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${colorClass}`}>
                    <Cpu className="w-4 h-4" />
                </div>
                <div>
                    <div className="font-semibold text-sm">Provider</div>
                    <div className="text-xs text-gray-500 capitalize">{data.config?.type || 'None'}</div>
                </div>
            </div>

            {data.config?.model && (
                <div className="text-xs text-gray-600 mt-1">
                    <span className="font-medium">Model:</span> {data.config.model}
                </div>
            )}

            <Handle type="source" position={Position.Right} className="w-3 h-3" />
        </div>
    );
}
