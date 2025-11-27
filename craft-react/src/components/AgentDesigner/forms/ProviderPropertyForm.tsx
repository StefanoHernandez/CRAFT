/**
 * Provider Property Form
 */

import React from 'react';
import { useAgentDesigner } from '../store';
import { ProviderNodeConfig } from '../types';

interface ProviderPropertyFormProps {
    nodeId: string;
    config: ProviderNodeConfig;
}

export function ProviderPropertyForm({ nodeId, config }: ProviderPropertyFormProps) {
    const { updateNode } = useAgentDesigner();

    const handleChange = (field: keyof ProviderNodeConfig, value: any) => {
        updateNode(nodeId, {
            data: {
                label: 'Provider',
                config: { ...config, [field]: value },
            },
        });
    };

    const providers = [
        { value: 'openai', label: 'OpenAI' },
        { value: 'anthropic', label: 'Anthropic' },
        { value: 'google', label: 'Google' },
        { value: 'ollama', label: 'Ollama' },
        { value: 'groq', label: 'Groq' },
        { value: 'mistral', label: 'Mistral AI' },
    ];

    const models: Record<string, string[]> = {
        openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'],
        anthropic: ['claude-opus-4.5', 'claude-sonnet-4.5', 'claude-haiku-4.5'],
        google: ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-pro'],
        ollama: ['llama3.2', 'mistral', 'codellama', 'qwen2.5'],
        groq: ['llama-3.1-70b-versatile', 'mixtral-8x7b-32768', 'gemma2-9b-it'],
        mistral: ['mistral-large-latest', 'mistral-medium-latest', 'mistral-small-latest'],
    };

    return (
        <div className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Provider *
                </label>
                <select
                    value={config.type || 'openai'}
                    onChange={(e) => handleChange('type', e.target.value as any)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                    {providers.map((p) => (
                        <option key={p.value} value={p.value}>
                            {p.label}
                        </option>
                    ))}
                </select>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Model *
                </label>
                <select
                    value={config.model || ''}
                    onChange={(e) => handleChange('model', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                    {models[config.type]?.map((model) => (
                        <option key={model} value={model}>
                            {model}
                        </option>
                    ))}
                </select>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    API Key
                </label>
                <input
                    type="password"
                    value={config.api_key || ''}
                    onChange={(e) => handleChange('api_key', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="sk-..."
                />
                <p className="text-xs text-gray-500 mt-1">
                    Leave empty to use environment variable
                </p>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Temperature
                </label>
                <input
                    type="number"
                    value={config.temperature ?? 0.7}
                    onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min={0}
                    max={2}
                    step={0.1}
                />
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
                    placeholder="Optional"
                />
            </div>
        </div>
    );
}
