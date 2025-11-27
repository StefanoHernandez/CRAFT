/**
 * Toolbar - Top bar with actions (export, save, clear)
 */

import React, { useState } from 'react';
import { Download, Save, Trash2, Code } from 'lucide-react';
import { useAgentDesigner } from './store';
import { generatePythonCode } from './codeGenerator';
import { CodePreviewModal } from './CodePreviewModal';

export function Toolbar() {
    const { workflow, clearWorkflow } = useAgentDesigner();
    const [showCodePreview, setShowCodePreview] = useState(false);

    const handleExport = () => {
        setShowCodePreview(true);
    };

    const handleSave = () => {
        const json = JSON.stringify(workflow, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${workflow.name.toLowerCase().replace(/\s+/g, '-')}.json`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const handleClear = () => {
        if (confirm('Are you sure you want to clear the entire workflow?')) {
            clearWorkflow();
        }
    };

    return (
        <>
            <div className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4">
                <div className="flex items-center gap-2">
                    <h1 className="text-lg font-bold text-gray-800">CRAFT Agent Designer</h1>
                    <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full font-medium">
                        Beta
                    </span>
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={handleExport}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 font-medium text-sm"
                    >
                        <Code className="w-4 h-4" />
                        Export Code
                    </button>

                    <button
                        onClick={handleSave}
                        className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 font-medium text-sm"
                    >
                        <Download className="w-4 h-4" />
                        Save JSON
                    </button>

                    <button
                        onClick={handleClear}
                        className="flex items-center gap-2 px-4 py-2 border border-red-300 text-red-600 rounded hover:bg-red-50 font-medium text-sm"
                    >
                        <Trash2 className="w-4 h-4" />
                        Clear
                    </button>
                </div>
            </div>

            {showCodePreview && (
                <CodePreviewModal
                    code={generatePythonCode(workflow)}
                    onClose={() => setShowCodePreview(false)}
                />
            )}
        </>
    );
}
