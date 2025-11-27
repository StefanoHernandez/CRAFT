/**
 * Custom Output Node for React Flow
 */

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { FileOutput } from 'lucide-react';

export function OutputNode({ data, selected }: NodeProps) {
    return (
        <div
            className={`px-4 py-3 rounded-lg border-2 bg-white shadow-md min-w-[180px] ${selected ? 'border-blue-500' : 'border-gray-300'
                }`}
        >
            <Handle type="target" position={Position.Left} className="w-3 h-3" />

            <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                    <FileOutput className="w-4 h-4 text-green-600" />
                </div>
                <div>
                    <div className="font-semibold text-sm">Output</div>
                    <div className="text-xs text-gray-500 uppercase">{data.config?.format || 'text'}</div>
                </div>
            </div>

            {data.config?.include_metadata && (
                <div className="text-xs text-gray-600 mt-1">
                    <span className="text-green-600">✓</span> Include metadata
                </div>
            )}
        </div>
    );
}
