import React, { useEffect } from 'react';
import { NexusScene } from '../components/Nexus/NexusScene';
import { NexusHUD } from '../components/Nexus/NexusHUD';
import { useNexusStore } from '../stores/nexusStore';

export function NexusPage() {
    const addLog = useNexusStore((state) => state.addLog);
    const setNodeStatus = useNexusStore((state) => state.setNodeStatus);
    const spawnPacket = useNexusStore((state) => state.spawnPacket);

    // Simulation Loop (Demo Mode)
    useEffect(() => {
        let step = 0;
        const interval = setInterval(() => {
            step++;

            // Reset statuses occasionally
            if (step % 20 === 0) {
                setNodeStatus('agent', 'idle');
                setNodeStatus('provider', 'idle');
                setNodeStatus('tools', 'idle');
                setNodeStatus('memory', 'idle');
            }

            // Simulate Agent Thinking
            if (step % 10 === 0) {
                setNodeStatus('agent', 'active');
                addLog('Agent received input: "Analyze Q3 sales"', 'info');
            }

            // Simulate LLM Call
            if (step % 10 === 2) {
                setNodeStatus('provider', 'active');
                spawnPacket('agent', 'provider', '#ec4899');
                addLog('Querying GPT-4o...', 'info');
            }

            // Simulate Tool Call
            if (step % 10 === 5) {
                setNodeStatus('provider', 'idle');
                setNodeStatus('tools', 'active');
                spawnPacket('provider', 'agent', '#ec4899');
                setTimeout(() => spawnPacket('agent', 'tools', '#f59e0b'), 500);
                addLog('Calling tool: database_search', 'warning');
            }

            // Simulate Memory Access
            if (step % 10 === 7) {
                setNodeStatus('memory', 'active');
                spawnPacket('agent', 'memory', '#06b6d4');
                addLog('Retrieving context from vector DB', 'info');
            }

            // Simulate Response
            if (step % 10 === 9) {
                setNodeStatus('agent', 'success');
                setNodeStatus('tools', 'idle');
                setNodeStatus('memory', 'idle');
                spawnPacket('tools', 'agent', '#f59e0b');
                spawnPacket('memory', 'agent', '#06b6d4');
                addLog('Task completed successfully', 'success');
            }

        }, 1000);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="w-full h-screen relative bg-slate-950 overflow-hidden">
            <NexusScene />
            <NexusHUD />
        </div>
    );
}
