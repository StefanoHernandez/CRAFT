/**
 * CRAFT Workflow Engine
 * Handles visual node editing, dragging, and connection logic.
 */

class WorkflowEngine {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.svg = this.canvas.querySelector('svg');
        this.nodes = [];
        this.connections = [];
        this.selectedNode = null;
        this.draggingNode = null;
        this.dragOffset = { x: 0, y: 0 };
        this.isConnecting = false;

        this.initEventListeners();
        this.initNexusSubscription();
        console.log('🏗️ Workflow Engine Initialized');
    }

    initNexusSubscription() {
        if (window.nexus) {
            window.nexus.subscribe((event) => {
                if (event.type === 'node_status') {
                    this.updateNodeStatus(event.node_id, event.status);
                } else if (event.type === 'save_status') {
                    this.showToast(event.message, event.success ? 'success' : 'error');
                }
            });
        }
    }

    updateNodeStatus(nodeId, status) {
        const nodeEl = document.getElementById(nodeId);
        if (!nodeEl) return;

        const card = nodeEl.querySelector('.node-card');
        const statusDot = nodeEl.querySelector('.status-dot') || this.createStatusDot(nodeEl);

        if (status === 'executing') {
            card.classList.add('ring-4', 'ring-primary', 'animate-pulse');
            statusDot.className = 'status-dot absolute top-2 right-2 size-2 rounded-full bg-primary animate-ping';
        } else if (status === 'completed') {
            card.classList.remove('ring-4', 'ring-primary', 'animate-pulse');
            card.classList.add('ring-2', 'ring-emerald-500');
            statusDot.className = 'status-dot absolute top-2 right-2 size-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]';
        }
    }

    createStatusDot(nodeEl) {
        const dot = document.createElement('div');
        dot.className = 'status-dot absolute top-2 right-2 size-2 rounded-full bg-slate-500';
        nodeEl.querySelector('.relative').appendChild(dot);
        return dot;
    }

    showToast(message, type) {
        console.log(`[${type.toUpperCase()}] ${message}`);
        // Visual toast would be better here
        const toast = document.createElement('div');
        toast.className = `fixed bottom-20 right-6 px-6 py-3 rounded-xl border backdrop-blur-md z-50 transform transition-all translate-y-20 opacity-0`;
        if (type === 'success') toast.classList.add('bg-emerald-500/10', 'border-emerald-500/50', 'text-emerald-400');
        else toast.classList.add('bg-red-500/10', 'border-red-500/50', 'text-red-400');

        toast.innerHTML = `
            <div class="flex items-center gap-2">
                <span class="material-symbols-outlined">${type === 'success' ? 'check_circle' : 'error'}</span>
                <span class="text-sm font-medium">${message}</span>
            </div>
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.classList.replace('translate-y-20', 'translate-y-0'), 100);
        setTimeout(() => toast.classList.replace('opacity-0', 'opacity-100'), 100);
        setTimeout(() => {
            toast.classList.replace('opacity-100', 'opacity-0');
            setTimeout(() => toast.remove(), 500);
        }, 3000);
    }

    runWorkflow() {
        const state = {
            nodes: this.nodes,
            connections: this.connections
        };
        console.log('🚀 Running Workflow Execution:', state);
        if (window.nexus) {
            window.nexus.send({ type: 'run_workflow', data: state });
        }
    }

    initEventListeners() {
        // Canvas Drag & Drop
        this.canvas.addEventListener('dragover', (e) => e.preventDefault());
        this.canvas.addEventListener('drop', (e) => this.handlePaletteDrop(e));

        // Node Movement
        window.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        window.addEventListener('mouseup', () => this.handleMouseUp());

        // Zoom/Pan (simulated for now)
    }

    handlePaletteDrop(e) {
        e.preventDefault();
        const nodeType = e.dataTransfer.getData('node-type');
        const nodeName = e.dataTransfer.getData('node-name');

        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left - 100; // Center offset
        const y = e.clientY - rect.top - 20;

        if (nodeType) {
            this.addNode({
                id: 'node_' + Math.random().toString(36).substr(2, 5),
                type: nodeType,
                name: nodeName || 'New Node',
                x: x,
                y: y,
                data: {}
            });
        }
    }

    addNode(config) {
        const node = config;
        this.nodes.push(node);
        this.renderNode(node);
        this.renderConnections();
    }

    renderNode(node) {
        const div = document.createElement('div');
        div.id = node.id;
        div.className = 'absolute w-72 group z-10 cursor-grab active:cursor-grabbing';
        div.style.left = `${node.x}px`;
        div.style.top = `${node.y}px`;
        div.style.transform = 'translate3d(0,0,0)';

        // Node Template based on type
        const color = node.type === 'agent' ? 'primary' : (node.type === 'knowledge' ? 'emerald-500' : 'purple-500');
        const icon = node.type === 'agent' ? 'psychology' : (node.type === 'knowledge' ? 'description' : 'input');

        div.innerHTML = `
            <div class="relative bg-surface-dark/95 backdrop-blur-md border border-${color}/40 hover:border-${color} rounded-xl shadow-xl transition-all node-card">
                <div class="px-4 py-3 border-b border-white/5 flex items-center justify-between bg-white/5 rounded-t-xl">
                    <div class="flex items-center gap-2">
                        <div class="bg-${color}/20 p-1 rounded text-${color}">
                            <span class="material-symbols-outlined text-[16px]">${icon}</span>
                        </div>
                        <span class="text-sm font-medium text-white">${node.name}</span>
                    </div>
                </div>
                <div class="p-4">
                    <div class="text-[10px] text-slate-500 font-mono mb-1">ID: ${node.id.toUpperCase()}</div>
                    <p class="text-[11px] text-slate-400 line-clamp-2">Configure settings in Inspector...</p>
                </div>
                <!-- Handles -->
                <div class="port input-port absolute -left-1.5 top-1/2 -translate-y-1/2 w-3 h-3 bg-slate-600 rounded-full border-2 border-surface-dark cursor-crosshair hover:bg-white transition-colors"></div>
                <div class="port output-port absolute -right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 bg-${color} rounded-full border-2 border-surface-dark cursor-crosshair hover:scale-125 transition-transform"></div>
            </div>
        `;

        div.onmousedown = (e) => {
            if (e.target.classList.contains('port')) {
                this.startConnection(node, e.target);
            } else {
                this.startDrag(node, div, e);
                this.selectNode(node);
            }
        };

        this.canvas.appendChild(div);
    }

    startDrag(node, element, e) {
        this.draggingNode = { node, element };
        const rect = element.getBoundingClientRect();
        this.dragOffset = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
        element.classList.add('z-50');
    }

    handleMouseMove(e) {
        if (this.draggingNode) {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left - this.dragOffset.x;
            const y = e.clientY - rect.top - this.dragOffset.y;

            this.draggingNode.node.x = x;
            this.draggingNode.node.y = y;
            this.draggingNode.element.style.left = `${x}px`;
            this.draggingNode.element.style.top = `${y}px`;

            this.renderConnections();
        }
    }

    handleMouseUp() {
        if (this.draggingNode) {
            this.draggingNode.element.classList.remove('z-50');
            this.draggingNode = null;
        }
    }

    selectNode(node) {
        this.selectedNode = node;
        // Update Inspector
        const inspectorTitle = document.querySelector('aside h2 + p');
        const inspectorHeader = document.querySelector('aside h2');
        if (inspectorTitle) inspectorTitle.innerText = `${node.name} (${node.type.toUpperCase()})`;

        // Highlight in UI
        document.querySelectorAll('.node-card').forEach(c => c.classList.remove('ring-2', 'ring-primary'));
        const el = document.getElementById(node.id).querySelector('.node-card');
        el.classList.add('ring-2', 'ring-primary');
    }

    renderConnections() {
        // Clear SVG except defs
        const defs = this.svg.querySelector('defs');
        this.svg.innerHTML = '';
        this.svg.appendChild(defs);

        this.connections.forEach(conn => {
            const fromNode = this.nodes.find(n => n.id === conn.from);
            const toNode = this.nodes.find(n => n.id === conn.to);
            if (fromNode && toNode) {
                const path = this.createPath(fromNode, toNode);
                this.svg.appendChild(path);
            }
        });
    }

    createPath(from, to) {
        const x1 = from.x + 288; // Node width
        const y1 = from.y + 60;  // Half height approx
        const x2 = to.x;
        const y2 = to.y + 60;

        const cp1x = x1 + (x2 - x1) / 2;
        const cp2x = cp1x;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', `M${x1},${y1} C${cp1x},${y1} ${cp2x},${y2} ${x2},${y2}`);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', '#0da6f2');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('class', 'animate-dash');
        return path;
    }

    saveState() {
        const state = {
            nodes: this.nodes,
            connections: this.connections
        };
        console.log('💾 Saving Workflow State:', state);
        if (window.nexus) {
            window.nexus.send({ type: 'save_workflow', data: state });
        }
        return state;
    }
}
