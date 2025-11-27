import React from 'react';
import { useNexusStore, NexusLog } from '../../stores/nexusStore';
import { Activity, Cpu, Database, Zap } from 'lucide-react';

export function NexusHUD() {
    const logs = useNexusStore((state) => state.logs);
    const nodes = useNexusStore((state) => state.nodes);

    const agentStatus = nodes.find(n => n.id === 'agent')?.status || 'idle';

    return (
        <div className="absolute inset-0 pointer-events-none p-6 flex flex-col justify-between">
            {/* Top Bar */}
            <div className="flex justify-between items-start">
                {/* Stats Panel */}
                <div className="bg-slate-900/80 backdrop-blur border border-slate-700 p-4 rounded-lg w-64 text-slate-200 font-mono text-sm">
                    <div className="flex items-center gap-2 mb-2 text-blue-400">
                        <Activity className="w-4 h-4" />
                        <span className="font-bold">SYSTEM STATUS</span>
                    </div>
                    <div className="space-y-2">
                        <div className="flex justify-between">
                            <span>CORE:</span>
                            <span className={getStatusColor(agentStatus)}>{agentStatus.toUpperCase()}</span>
                        </div>
                        <div className="flex justify-between">
                            <span>FPS:</span>
                            <span>60</span>
                        </div>
                        <div className="flex justify-between">
                            <span>LATENCY:</span>
                            <span>24ms</span>
                        </div>
                    </div>
                </div>

                {/* Title */}
                <div className="text-center">
                    <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 tracking-widest">
                        CRAFT NEXUS
                    </h1>
                    <div className="text-xs text-slate-500 tracking-[0.5em]">VISUALIZER V1.0</div>
                </div>

                {/* Active Modules */}
                <div className="bg-slate-900/80 backdrop-blur border border-slate-700 p-4 rounded-lg w-64 text-slate-200">
                    <div className="flex items-center gap-2 mb-2 text-purple-400">
                        <Cpu className="w-4 h-4" />
                        <span className="font-bold font-mono text-sm">ACTIVE MODULES</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                        <ModuleIcon icon={Zap} label="LLM" active={nodes.find(n => n.id === 'provider')?.status === 'active'} />
                        <ModuleIcon icon={Database} label="MEM" active={nodes.find(n => n.id === 'memory')?.status === 'active'} />
                        <ModuleIcon icon={Activity} label="TOOL" active={nodes.find(n => n.id === 'tools')?.status === 'active'} />
                    </div>
                </div>
            </div>

            {/* Bottom Bar */}
            <div className="flex justify-between items-end">
                {/* Logs Console */}
                <div className="bg-slate-900/80 backdrop-blur border border-slate-700 rounded-lg w-96 h-48 overflow-hidden flex flex-col">
                    <div className="bg-slate-800/50 px-3 py-1 text-xs text-slate-400 border-b border-slate-700 flex justify-between">
                        <span>EVENT LOG</span>
                        <span>LIVE</span>
                    </div>
                    <div className="p-2 overflow-y-auto font-mono text-xs space-y-1 flex-1">
                        {logs.map((log) => (
                            <div key={log.id} className="flex gap-2">
                                <span className="text-slate-500">[{new Date(log.timestamp).toLocaleTimeString().split(' ')[0]}]</span>
                                <span className={getLogColor(log.type)}>{log.message}</span>
                            </div>
                        ))}
                        {logs.length === 0 && (
                            <div className="text-slate-600 italic text-center mt-10">Waiting for events...</div>
                        )}
                    </div>
                </div>

                {/* Controls Hint */}
                <div className="text-slate-500 text-xs font-mono">
                    ORBIT: LEFT CLICK | ZOOM: SCROLL
                </div>
            </div>
        </div>
    );
}

function ModuleIcon({ icon: Icon, label, active }: { icon: any, label: string, active: boolean }) {
    return (
        <div className={`flex flex-col items-center p-2 rounded border ${active ? 'bg-blue-500/20 border-blue-500 text-blue-400' : 'bg-slate-800/50 border-slate-700 text-slate-600'}`}>
            <Icon className="w-5 h-5 mb-1" />
            <span className="text-[10px] font-bold">{label}</span>
        </div>
    );
}

function getStatusColor(status: string) {
    switch (status) {
        case 'active': return 'text-purple-400';
        case 'success': return 'text-green-400';
        case 'error': return 'text-red-400';
        default: return 'text-slate-400';
    }
}

function getLogColor(type: NexusLog['type']) {
    switch (type) {
        case 'success': return 'text-green-400';
        case 'error': return 'text-red-400';
        case 'warning': return 'text-yellow-400';
        default: return 'text-blue-300';
    }
}
