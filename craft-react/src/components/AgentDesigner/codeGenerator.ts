
/**
 * Python code generator for CRAFT agents
 */

import { AgentWorkflow, WorkflowNode, NodeType } from './types';

export function generatePythonCode(workflow: AgentWorkflow): string {
    const imports = generateImports(workflow);

    // Generate definitions for all components and map them by ID
    const { code: providerCode, map: providerMap } = generateProviders(workflow);
    const { code: toolsCode, map: toolsMap } = generateTools(workflow);
    const { code: memoryCode, map: memoryMap } = generateMemories(workflow);

    // Generate agents linking to specific components
    const { code: agentCode, agents } = generateAgents(workflow, providerMap, toolsMap, memoryMap);

    const executionCode = generateExecutionCode(agents);

    return `"""
Generated CRAFT Agent: ${workflow.name}
${workflow.description || ''}
"""

${imports}

# --- Providers ---
${providerCode}

# --- Tools ---
${toolsCode}

# --- Memory ---
${memoryCode}

# --- Agents ---
${agentCode}

# --- Execution ---
${executionCode}
`.trim();
}

function generateImports(workflow: AgentWorkflow): string {
    const imports: Set<string> = new Set([
        'from craft.agents import Agent',
    ]);

    workflow.nodes.forEach((node) => {
        switch (node.type) {
            case 'provider':
                const providerType = node.data.config.type;
                const providerMap: Record<string, string> = {
                    openai: 'OpenAIProvider',
                    anthropic: 'AnthropicProvider',
                    google: 'GoogleProvider',
                    ollama: 'OllamaProvider',
                    groq: 'GroqProvider',
                    mistral: 'MistralProvider',
                };
                if (providerMap[providerType]) {
                    imports.add(`from craft.providers import ${providerMap[providerType]}`);
                }
                break;
            case 'tool':
                if (node.data.config.type === 'builtin') {
                    imports.add(`from craft.tools.builtin import ${node.data.config.name}`);
                } else if (node.data.config.type === 'custom') {
                    imports.add('from craft.tools import Tool');
                }
                break;
            case 'memory':
                if (node.data.config.enabled) {
                    imports.add('from craft.core.memory import Memory');
                    if (node.data.config.storage_type === 'sqlite') {
                        imports.add('from craft.storage import SQLiteStorage');
                    } else if (node.data.config.storage_type === 'json') {
                        imports.add('from craft.storage import JSONFileStorage');
                    }
                }
                break;
        }
    });

    return Array.from(imports).join('\n');
}

function sanitizeName(name: string): string {
    return name.replace(/[^a-zA-Z0-9_]/g, '_').toLowerCase();
}

function generateProviders(workflow: AgentWorkflow): { code: string, map: Map<string, string> } {
    const providerNodes = workflow.nodes.filter(n => n.type === 'provider');
    const map = new Map<string, string>();
    const codeLines: string[] = [];

    providerNodes.forEach((node, index) => {
        const config = node.data.config;
        const varName = `provider_${config.type}_${index + 1}`;
        map.set(node.id, varName);

        const providerMap: Record<string, string> = {
            openai: 'OpenAIProvider',
            anthropic: 'AnthropicProvider',
            google: 'GoogleProvider',
            ollama: 'OllamaProvider',
            groq: 'GroqProvider',
            mistral: 'MistralProvider',
        };
        const className = providerMap[config.type] || 'OpenAIProvider';

        const params: string[] = [];
        if (config.api_key) params.push(`api_key="${config.api_key}"`);
        params.push(`model="${config.model}"`);
        if (config.temperature !== undefined) params.push(`temperature=${config.temperature}`);
        if (config.max_tokens) params.push(`max_tokens=${config.max_tokens}`);

        codeLines.push(`${varName} = ${className}(`);
        codeLines.push(`    ${params.join(',\n    ')}`);
        codeLines.push(`)`);
        codeLines.push('');
    });

    return { code: codeLines.join('\n'), map };
}

function generateTools(workflow: AgentWorkflow): { code: string, map: Map<string, string> } {
    const toolNodes = workflow.nodes.filter(n => n.type === 'tool');
    const map = new Map<string, string>();
    const codeLines: string[] = [];

    toolNodes.forEach(node => {
        if (node.data.config.type === 'builtin') {
            // Alias the imported tool so it appears in the Tools section
            const toolVar = `tool_${sanitizeName(node.data.config.name)}`;
            codeLines.push(`${toolVar} = ${node.data.config.name}`);
            map.set(node.id, toolVar);
        } else {
            // Custom tools need a class definition
            const safeName = sanitizeName(node.data.config.name);
            const className = `CustomTool_${safeName}`; // e.g. CustomTool_my_tool
            const instanceName = `tool_${safeName}`; // e.g. tool_my_tool

            codeLines.push(`class ${className}(Tool):`);
            codeLines.push(`    name = "${node.data.config.name}"`);
            codeLines.push(`    description = "${node.data.config.description || 'Custom tool description'}"`);
            codeLines.push(``);
            codeLines.push(`    def _run(self, query: str):`);
            codeLines.push(`        return "Not implemented"`);
            codeLines.push(``);
            codeLines.push(`${instanceName} = ${className}()`);
            codeLines.push(``);

            map.set(node.id, instanceName);
        }
    });

    return { code: codeLines.join('\n'), map };
}

function generateMemories(workflow: AgentWorkflow): { code: string, map: Map<string, string> } {
    const memoryNodes = workflow.nodes.filter(n => n.type === 'memory' && n.data.config.enabled);
    const map = new Map<string, string>();
    const codeLines: string[] = [];

    memoryNodes.forEach((node, index) => {
        const config = node.data.config;
        const varName = `memory_${index + 1}`;
        map.set(node.id, varName);

        const params: string[] = [];
        if (config.storage_type === 'sqlite') {
            params.push(`storage=SQLiteStorage(db_path="${config.storage_path || 'agent.db'}")`);
        } else if (config.storage_type === 'json') {
            params.push(`storage=JSONFileStorage(file_path="${config.storage_path || 'agent.json'}")`);
        }

        if (config.max_messages) params.push(`max_messages=${config.max_messages}`);
        if (config.max_tokens) params.push(`max_tokens=${config.max_tokens}`);

        codeLines.push(`${varName} = Memory(`);
        codeLines.push(`    ${params.join(',\n    ')}`);
        codeLines.push(`)`);
        codeLines.push('');
    });

    return { code: codeLines.join('\n'), map };
}

function generateAgents(
    workflow: AgentWorkflow,
    providerMap: Map<string, string>,
    toolsMap: Map<string, string>,
    memoryMap: Map<string, string>
): { code: string, agents: string[] } {
    const agentNodes = workflow.nodes.filter(n => n.type === 'agent');
    const agentVars: string[] = [];
    const codeLines: string[] = [];

    agentNodes.forEach((node, index) => {
        const config = node.data.config;
        const varName = `agent_${sanitizeName(config.name || `agent_${index + 1}`)}`;
        agentVars.push(varName);

        // Find connected components
        const incomingEdges = workflow.edges.filter(e => e.target === node.id);
        const sourceIds = incomingEdges.map(e => e.source);

        // Resolve Provider
        const providerId = sourceIds.find(id => providerMap.has(id));
        const providerVar = providerId ? providerMap.get(providerId) : 'None # No provider connected';

        // Resolve Memory
        const memoryId = sourceIds.find(id => memoryMap.has(id));
        const memoryVar = memoryId ? memoryMap.get(memoryId) : null;

        // Resolve Tools
        const toolVars = sourceIds
            .filter(id => toolsMap.has(id))
            .map(id => toolsMap.get(id));

        const params: string[] = [
            `name="${config.name || varName}"`,
            `provider=${providerVar}`,
        ];

        if (toolVars.length > 0) {
            params.push(`tools=[${toolVars.join(', ')}]`);
        } else {
            params.push(`tools=[]`);
        }

        if (config.role) params.push(`role="${config.role}"`);
        if (config.goal) params.push(`goal="${config.goal}"`);
        if (config.backstory) params.push(`backstory="${config.backstory}"`);
        if (config.max_steps) params.push(`max_steps=${config.max_steps}`);
        if (config.verbose) params.push(`verbose=${config.verbose}`);

        if (memoryVar) {
            params.push(`memory=${memoryVar}`);
        }

        codeLines.push(`${varName} = Agent(`);
        codeLines.push(`    ${params.join(',\n    ')}`);
        codeLines.push(`)`);
        codeLines.push('');
    });

    return { code: codeLines.join('\n'), agents: agentVars };
}

function generateExecutionCode(agents: string[]): string {
    if (agents.length === 0) return '# No agents defined';

    // If multiple agents, maybe run the last one or just show how to run the first
    const mainAgent = agents[0];

    return `if __name__ == "__main__":
    # Run the agent
    result = ${mainAgent}.run("Hello! Who are you and what can you do?")
    print(result.text)`;
}
