/**
 * Custom Tool Node for React Flow
 */

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Wrench } from 'lucide-react';

export function ToolNode({ data, selected }: NodeProps) {
    return (
        <div
            className={`px-4 py-3 rounded-lg border-2 bg-white shadow-md min-w-[180px] ${selected ? 'border-blue-500' : 'border-gray-300'
                }`}
        >
            <Handle type="target" position={Position.Left} className="w-3 h-3" />

            <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-full bg-yellow-100 flex items-center justify-center">
                    <Wrench className="w-4 h-4 text-yellow-600" />
                </div>
                <div>
                    <div className="font-semibold text-sm">Tool</div>
                    <div className="text-xs text-gray-500">{data.config?.name || 'Unnamed Tool'}</div>
                </div>
            </div>

            {data.config?.description && (
                <div className="text-xs text-gray-600 mt-1 line-clamp-2">
                    {data.config.description}
                </div>
            )}

            <Handle type="source" position={Position.Right} className="w-3 h-3" />
        </div>
    );
}
