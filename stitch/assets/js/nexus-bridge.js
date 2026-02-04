/**
 * CRAFT Nexus Bridge
 * Standardizes WebSocket communication and UI updates across all Stitch modules.
 */

class NexusBridge {
    constructor() {
        this.ws = null;
        this.connectionId = 'client_' + Math.random().toString(36).substr(2, 9);
        this.listeners = [];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.metricsInterval = null;

        console.log('🚀 Nexus Bridge Initialized:', this.connectionId);
        this.connect();
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const hostname = window.location.hostname;
        const port = 8000; // API Server port
        const url = `${protocol}//${hostname}:${port}/ws/${this.connectionId}`;

        console.log('📡 Connecting to Nexus Hub:', url);
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
            console.log('✅ Connected to Nexus Hub');
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
            this.notifyListeners({ type: 'status', status: 'connected' });
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.notifyListeners(data);
                this.handleGlobalEvents(data);
            } catch (e) {
                console.error('❌ Error parsing message:', e);
            }
        };

        this.ws.onclose = () => {
            console.log('❌ Disconnected from Nexus Hub');
            this.updateConnectionStatus(false);
            this.notifyListeners({ type: 'status', status: 'disconnected' });
            this.attemptReconnect();
        };

        this.ws.onerror = (err) => {
            console.error('⚠️ WebSocket Error:', err);
        };
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 Reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            setTimeout(() => this.connect(), 3000);
        }
    }

    updateConnectionStatus(connected) {
        const statusElements = document.querySelectorAll('.connection-status-dot');
        statusElements.forEach(el => {
            el.classList.toggle('bg-emerald-500', connected);
            el.classList.toggle('bg-red-500', !connected);
            el.classList.add('animate-pulse');
        });

        const statusText = document.querySelector('#system-status-text');
        if (statusText) {
            statusText.innerText = connected ? 'SYSTEMS ONLINE' : 'SYSTEMS OFFLINE';
            statusText.classList.toggle('text-emerald-400', connected);
            statusText.classList.toggle('text-red-400', !connected);
        }
    }

    handleGlobalEvents(data) {
        // Handle Agent lifecycle events for global UI updates
        if (data.event_type === 'agent_start') {
            this.showToast(`Agent ${data.agent_name} started execution`, 'info');
        } else if (data.event_type === 'agent_end') {
            this.showToast(`Agent ${data.agent_name} completed task`, 'success');
        } else if (data.event_type === 'agent_error') {
            this.showToast(`Agent ${data.agent_name} encountered an error`, 'error');
        }

        // Update metrics if present
        if (data.type === 'metrics') {
            this.updateUIMetrics(data.data);
        }
    }

    updateUIMetrics(metrics) {
        // Map backend metrics to common Stitch UI placeholders
        const mapping = {
            'tokens_per_sec': '#tps-value',
            'active_tools': '#tools-value',
            'cost': '#cost-value',
            'memory': '#memory-percent',
            'cpu': '#cpu-percent'
        };

        for (const [key, selector] of Object.entries(mapping)) {
            if (metrics[key] !== undefined) {
                const el = document.querySelector(selector);
                if (el) {
                    // Animate value change if possible
                    el.innerText = metrics[key];
                }
            }
        }
    }

    showToast(message, type = 'info') {
        // Simple console-based toast for now
        console.log(`[${type.toUpperCase()}] ${message}`);
    }

    subscribe(callback) {
        this.listeners.push(callback);
        return () => {
            this.listeners = this.listeners.filter(l => l !== callback);
        };
    }

    notifyListeners(data) {
        this.listeners.forEach(listener => listener(data));
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
}

// Global instance
window.nexus = new NexusBridge();

// Dashboard specific updates
document.addEventListener('DOMContentLoaded', () => {
    // Console output mapping
    const terminal = document.querySelector('.terminal-output, .event-stream');
    if (terminal) {
        window.nexus.subscribe((event) => {
            if (event.event_type === 'thought' || event.event_type === 'tool_result' || event.event_type === 'response_chunk') {
                const entry = document.createElement('div');
                entry.className = 'py-1 font-mono text-xs border-b border-white/5 opacity-0 transition-opacity duration-300';

                let icon = '●';
                let color = 'text-primary';
                let content = '';

                if (event.event_type === 'thought') {
                    icon = '🧠';
                    color = 'text-amber-400';
                    content = event.thought;
                } else if (event.event_type === 'tool_result') {
                    icon = '🛠️';
                    color = 'text-emerald-400';
                    content = `Tool Result: ${event.tool_name}`;
                } else if (event.event_type === 'response_chunk') {
                    icon = '💬';
                    color = 'text-white';
                    content = event.chunk;
                }

                entry.innerHTML = `<span class="${color} mr-2">${icon}</span> <span class="text-slate-500">[${new Date().toLocaleTimeString()}]</span> ${content}`;
                terminal.prepend(entry);
                setTimeout(() => entry.classList.replace('opacity-0', 'opacity-100'), 10);

                // Keep only last 50 entries
                if (terminal.children.length > 50) terminal.lastChild.remove();
            }
        });
    }
});
