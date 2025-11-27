import { create } from 'zustand';

export type NexusNodeStatus = 'idle' | 'active' | 'success' | 'error';

export interface NexusNode {
    id: string;
    type: 'agent' | 'provider' | 'tool' | 'memory';
    label: string;
    status: NexusNodeStatus;
    position: [number, number, number];
}

export interface NexusPacket {
    id: string;
    from: string;
    to: string;
    color: string;
    progress: number; // 0 to 1
}

export interface NexusLog {
    id: string;
    timestamp: number;
    message: string;
    type: 'info' | 'success' | 'warning' | 'error';
}

interface NexusState {
    nodes: NexusNode[];
    packets: NexusPacket[];
    logs: NexusLog[];

    // Actions
    addLog: (message: string, type?: NexusLog['type']) => void;
    setNodeStatus: (id: string, status: NexusNodeStatus) => void;
    spawnPacket: (from: string, to: string, color?: string) => void;
    updatePackets: (delta: number) => void;
    reset: () => void;
}

export const useNexusStore = create<NexusState>((set, get) => ({
    nodes: [
        { id: 'agent', type: 'agent', label: 'Agent Core', status: 'idle', position: [0, 0, 0] },
        { id: 'provider', type: 'provider', label: 'LLM Provider', status: 'idle', position: [0, 2, -2] },
        { id: 'memory', type: 'memory', label: 'Memory', status: 'idle', position: [-2, 1, 1] },
        { id: 'tools', type: 'tool', label: 'Tools', status: 'idle', position: [2, 1, 1] },
    ],
    packets: [],
    logs: [],

    addLog: (message, type = 'info') => {
        set((state) => ({
            logs: [
                { id: Math.random().toString(36).substr(2, 9), timestamp: Date.now(), message, type },
                ...state.logs,
            ].slice(0, 50), // Keep last 50 logs
        }));
    },

    setNodeStatus: (id, status) => {
        set((state) => ({
            nodes: state.nodes.map((n) => (n.id === id ? { ...n, status } : n)),
        }));
    },

    spawnPacket: (from, to, color = '#4f46e5') => {
        set((state) => ({
            packets: [
                ...state.packets,
                {
                    id: Math.random().toString(36).substr(2, 9),
                    from,
                    to,
                    color,
                    progress: 0,
                },
            ],
        }));
    },

    updatePackets: (delta) => {
        set((state) => ({
            packets: state.packets
                .map((p) => ({ ...p, progress: p.progress + delta }))
                .filter((p) => p.progress < 1),
        }));
    },

    reset: () => {
        set({ packets: [], logs: [] });
    },
}));
