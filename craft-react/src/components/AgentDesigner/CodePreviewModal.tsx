/**
 * Code Preview Modal - Display generated Python code
 */

import React from 'react';
import Editor from '@monaco-editor/react';
import { X, Copy, Download } from 'lucide-react';

interface CodePreviewModalProps {
    code: string;
    onClose: () => void;
}

export function CodePreviewModal({ code, onClose }: CodePreviewModalProps) {
    const handleCopy = () => {
        navigator.clipboard.writeText(code);
        alert('Code copied to clipboard!');
    };

    const handleDownload = () => {
        const blob = new Blob([code], { type: 'text/x-python' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'agent.py';
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl h-[80vh] flex flex-col">
                {/* Header */}
                <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                    <h2 className="text-lg font-semibold">Generated Python Code</h2>
                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-gray-100 rounded"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Editor */}
                <div className="flex-1 overflow-hidden">
                    <Editor
                        height="100%"
                        defaultLanguage="python"
                        value={code}
                        theme="vs-light"
                        options={{
                            readOnly: true,
                            minimap: { enabled: false },
                            fontSize: 14,
                            lineNumbers: 'on',
                            scrollBeyondLastLine: false,
                        }}
                    />
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-gray-200 flex gap-2 justify-end">
                    <button
                        onClick={handleCopy}
                        className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 font-medium text-sm"
                    >
                        <Copy className="w-4 h-4" />
                        Copy
                    </button>
                    <button
                        onClick={handleDownload}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 font-medium text-sm"
                    >
                        <Download className="w-4 h-4" />
                        Download .py
                    </button>
                </div>
            </div>
        </div>
    );
}
