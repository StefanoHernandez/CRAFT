/**
 * Demo Example - Visual Agent Designer
 */

import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import { AgentDesigner } from '../../src/components/AgentDesigner';
import { NexusPage } from '../../src/pages/NexusPage';
import { ArchitectureScene } from '../../src/components/Nexus/Architecture/ArchitectureScene';
import { DashboardScene } from '../../src/components/Nexus/Dashboard/DashboardScene';
import '../../src/styles.css';
import { LayoutGrid, Activity, Building2, BarChart3 } from 'lucide-react';

function App() {
    const [view, setView] = useState<'designer' | 'nexus' | 'architecture' | 'dashboard'>('designer');

    return (
        <div className="min-h-screen relative bg-slate-950">
            {/* Navigation Toggle - Floating Dock */}
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-50 flex bg-slate-900/90 backdrop-blur-md rounded-full p-1.5 border border-slate-700 shadow-2xl">
                <NavButton
                    active={view === 'designer'}
                    onClick={() => setView('designer')}
                    icon={LayoutGrid}
                    label="Designer"
                    color="blue"
                />
                <Divider />
                <NavButton
                    active={view === 'nexus'}
                    onClick={() => setView('nexus')}
                    icon={Activity}
                    label="Nexus Live"
                    color="purple"
                />
                <Divider />
                <NavButton
                    active={view === 'architecture'}
                    onClick={() => setView('architecture')}
                    icon={Building2}
                    label="Architecture"
                    color="cyan"
                />
                <Divider />
                <NavButton
                    active={view === 'dashboard'}
                    onClick={() => setView('dashboard')}
                    icon={BarChart3}
                    label="Dashboard"
                    color="emerald"
                />
            </div>

            {view === 'designer' && <AgentDesigner />}
            {view === 'nexus' && <NexusPage />}
            {view === 'architecture' && <ArchitectureScene />}
            {view === 'dashboard' && <DashboardScene />}
        </div>
    );
}

function NavButton({ active, onClick, icon: Icon, label, color }: any) {
    const colorClasses = {
        blue: 'bg-blue-600 shadow-blue-500/25',
        purple: 'bg-purple-600 shadow-purple-500/25',
        cyan: 'bg-cyan-600 shadow-cyan-500/25',
        emerald: 'bg-emerald-600 shadow-emerald-500/25',
    };

    return (
        <button
            onClick={onClick}
            className={`px-4 py-2 rounded-full flex items-center gap-2 text-sm font-medium transition-all duration-200 ${active
                    ? `${colorClasses[color as keyof typeof colorClasses]} text-white shadow-lg`
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
        >
            <Icon size={18} />
            {label}
        </button>
    );
}

function Divider() {
    return <div className="w-px bg-slate-700 mx-1 my-2" />;
}

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
