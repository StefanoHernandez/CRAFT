/**
 * CRAFT Chat Widget - Vanilla JavaScript
 *
 * Easily integrate CRAFT chatbot into any website.
 * No dependencies required!
 *
 * Usage:
 * <script src="craft-widget.js"></script>
 * <script>
 *   CRAFT.init({
 *     apiUrl: 'http://localhost:8000',
 *     apiKey: 'your-api-key', // optional
 *     theme: 'light' // or 'dark'
 *   });
 * </script>
 */

(function(window) {
    'use strict';

    const CRAFT = {
        config: {
            apiUrl: 'http://localhost:8000',
            apiKey: null,
            theme: 'light',
            position: 'bottom-right', // bottom-right, bottom-left, top-right, top-left
            title: 'CRAFT Assistant',
            placeholder: 'Type your message...',
            useRAG: true,
            enableStreaming: true,
        },

        state: {
            isOpen: false,
            conversationId: null,
            messages: [],
            isTyping: false,
        },

        elements: {},

        /**
         * Initialize the widget
         */
        init: function(options = {}) {
            this.config = { ...this.config, ...options };
            this.createWidget();
            this.attachEventListeners();
            console.log('CRAFT widget initialized');
        },

        /**
         * Create widget HTML
         */
        createWidget: function() {
            // Create container
            const container = document.createElement('div');
            container.id = 'craft-widget-container';
            container.className = `craft-widget ${this.config.theme} ${this.config.position}`;

            container.innerHTML = `
                <div id="craft-widget-button" class="craft-toggle-btn">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                </div>

                <div id="craft-widget-window" class="craft-window" style="display: none;">
                    <div class="craft-header">
                        <span class="craft-title">${this.config.title}</span>
                        <button id="craft-close-btn" class="craft-close-btn">×</button>
                    </div>

                    <div id="craft-messages" class="craft-messages"></div>

                    <div class="craft-input-container">
                        <input
                            type="text"
                            id="craft-input"
                            class="craft-input"
                            placeholder="${this.config.placeholder}"
                            autocomplete="off"
                        />
                        <button id="craft-send-btn" class="craft-send-btn">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="22" y1="2" x2="11" y2="13"></line>
                                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                            </svg>
                        </button>
                    </div>
                </div>
            `;

            // Add styles
            this.injectStyles();

            // Add to page
            document.body.appendChild(container);

            // Store element references
            this.elements = {
                container,
                button: document.getElementById('craft-widget-button'),
                window: document.getElementById('craft-widget-window'),
                messages: document.getElementById('craft-messages'),
                input: document.getElementById('craft-input'),
                sendBtn: document.getElementById('craft-send-btn'),
                closeBtn: document.getElementById('craft-close-btn'),
            };

            // Add welcome message
            this.addMessage('assistant', 'Hello! How can I help you today?');
        },

        /**
         * Inject CSS styles
         */
        injectStyles: function() {
            if (document.getElementById('craft-widget-styles')) return;

            const styles = document.createElement('style');
            styles.id = 'craft-widget-styles';
            styles.textContent = `
                .craft-widget { position: fixed; z-index: 9999; font-family: system-ui, -apple-system, sans-serif; }
                .craft-widget.bottom-right { bottom: 20px; right: 20px; }
                .craft-widget.bottom-left { bottom: 20px; left: 20px; }
                .craft-widget.top-right { top: 20px; right: 20px; }
                .craft-widget.top-left { top: 20px; left: 20px; }

                .craft-toggle-btn {
                    width: 60px; height: 60px; border-radius: 50%;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; border: none; cursor: pointer;
                    display: flex; align-items: center; justify-content: center;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    transition: transform 0.2s, box-shadow 0.2s;
                }
                .craft-toggle-btn:hover { transform: scale(1.05); box-shadow: 0 6px 16px rgba(0,0,0,0.2); }

                .craft-window {
                    width: 380px; height: 600px; max-height: 80vh;
                    background: white; border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.12);
                    display: flex; flex-direction: column;
                    position: absolute; bottom: 80px; right: 0;
                    overflow: hidden;
                }

                .craft-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 16px 20px;
                    display: flex; justify-content: space-between; align-items: center;
                }

                .craft-title { font-weight: 600; font-size: 16px; }

                .craft-close-btn {
                    background: none; border: none; color: white;
                    font-size: 28px; cursor: pointer; line-height: 1;
                    padding: 0; width: 24px; height: 24px;
                }

                .craft-messages {
                    flex: 1; overflow-y: auto; padding: 20px;
                    background: #f7f9fc;
                }

                .craft-message {
                    margin-bottom: 16px; animation: slideIn 0.3s ease-out;
                }

                @keyframes slideIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                .craft-message.user { text-align: right; }

                .craft-message-content {
                    display: inline-block; padding: 10px 14px;
                    border-radius: 12px; max-width: 75%;
                    word-wrap: break-word; line-height: 1.5;
                }

                .craft-message.user .craft-message-content {
                    background: #667eea; color: white;
                }

                .craft-message.assistant .craft-message-content {
                    background: white; color: #333;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                }

                .craft-typing {
                    display: inline-flex; gap: 4px; padding: 12px;
                }

                .craft-typing span {
                    width: 8px; height: 8px; border-radius: 50%;
                    background: #999; animation: typing 1.4s infinite;
                }

                .craft-typing span:nth-child(2) { animation-delay: 0.2s; }
                .craft-typing span:nth-child(3) { animation-delay: 0.4s; }

                @keyframes typing {
                    0%, 60%, 100% { transform: translateY(0); }
                    30% { transform: translateY(-10px); }
                }

                .craft-input-container {
                    display: flex; padding: 16px;
                    border-top: 1px solid #e0e0e0;
                    background: white;
                }

                .craft-input {
                    flex: 1; border: 1px solid #ddd;
                    border-radius: 24px; padding: 10px 16px;
                    font-size: 14px; outline: none;
                    transition: border-color 0.2s;
                }

                .craft-input:focus { border-color: #667eea; }

                .craft-send-btn {
                    background: #667eea; color: white;
                    border: none; border-radius: 50%;
                    width: 40px; height: 40px; margin-left: 8px;
                    cursor: pointer; display: flex;
                    align-items: center; justify-content: center;
                    transition: background 0.2s;
                }

                .craft-send-btn:hover { background: #5568d3; }
                .craft-send-btn:disabled { background: #ccc; cursor: not-allowed; }

                /* Dark theme */
                .craft-widget.dark .craft-window { background: #1e1e1e; }
                .craft-widget.dark .craft-messages { background: #121212; }
                .craft-widget.dark .craft-message.assistant .craft-message-content {
                    background: #2d2d2d; color: #e0e0e0;
                }
                .craft-widget.dark .craft-input-container { background: #1e1e1e; border-color: #333; }
                .craft-widget.dark .craft-input { background: #2d2d2d; border-color: #444; color: #e0e0e0; }
            `;
            document.head.appendChild(styles);
        },

        /**
         * Attach event listeners
         */
        attachEventListeners: function() {
            this.elements.button.addEventListener('click', () => this.toggleWidget());
            this.elements.closeBtn.addEventListener('click', () => this.toggleWidget());
            this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
            this.elements.input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendMessage();
            });
        },

        /**
         * Toggle widget visibility
         */
        toggleWidget: function() {
            this.state.isOpen = !this.state.isOpen;
            this.elements.window.style.display = this.state.isOpen ? 'flex' : 'none';
            if (this.state.isOpen) {
                this.elements.input.focus();
            }
        },

        /**
         * Add message to chat
         */
        addMessage: function(role, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `craft-message ${role}`;
            messageDiv.innerHTML = `
                <div class="craft-message-content">${this.escapeHtml(content)}</div>
            `;
            this.elements.messages.appendChild(messageDiv);
            this.scrollToBottom();

            this.state.messages.push({ role, content });
        },

        /**
         * Show typing indicator
         */
        showTyping: function() {
            const typingDiv = document.createElement('div');
            typingDiv.id = 'craft-typing-indicator';
            typingDiv.className = 'craft-message assistant';
            typingDiv.innerHTML = `
                <div class="craft-message-content">
                    <div class="craft-typing">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            `;
            this.elements.messages.appendChild(typingDiv);
            this.scrollToBottom();
            this.state.isTyping = true;
        },

        /**
         * Hide typing indicator
         */
        hideTyping: function() {
            const typingIndicator = document.getElementById('craft-typing-indicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
            this.state.isTyping = false;
        },

        /**
         * Send message to API
         */
        async sendMessage() {
            const message = this.elements.input.value.trim();
            if (!message || this.state.isTyping) return;

            // Add user message
            this.addMessage('user', message);
            this.elements.input.value = '';
            this.elements.sendBtn.disabled = true;

            // Show typing
            this.showTyping();

            try {
                if (this.config.enableStreaming) {
                    await this.sendStreamingMessage(message);
                } else {
                    await this.sendNormalMessage(message);
                }
            } catch (error) {
                this.hideTyping();
                this.addMessage('assistant', 'Sorry, an error occurred. Please try again.');
                console.error('CRAFT Error:', error);
            } finally {
                this.elements.sendBtn.disabled = false;
            }
        },

        /**
         * Send normal (non-streaming) message
         */
        async sendNormalMessage(message) {
            const headers = { 'Content-Type': 'application/json' };
            if (this.config.apiKey) {
                headers['Authorization'] = `Bearer ${this.config.apiKey}`;
            }

            const response = await fetch(`${this.config.apiUrl}/chat`, {
                method: 'POST',
                headers,
                body: JSON.stringify({
                    message,
                    conversation_id: this.state.conversationId,
                    use_rag: this.config.useRAG,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            this.hideTyping();
            this.addMessage('assistant', data.content);
            this.state.conversationId = data.conversation_id;
        },

        /**
         * Send streaming message
         */
        async sendStreamingMessage(message) {
            const headers = { 'Content-Type': 'application/json' };
            if (this.config.apiKey) {
                headers['Authorization'] = `Bearer ${this.config.apiKey}`;
            }

            const response = await fetch(`${this.config.apiUrl}/chat/stream`, {
                method: 'POST',
                headers,
                body: JSON.stringify({
                    message,
                    conversation_id: this.state.conversationId,
                    use_rag: this.config.useRAG,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.hideTyping();

            // Create message container for streaming
            const messageDiv = document.createElement('div');
            messageDiv.className = 'craft-message assistant';
            const contentDiv = document.createElement('div');
            contentDiv.className = 'craft-message-content';
            messageDiv.appendChild(contentDiv);
            this.elements.messages.appendChild(messageDiv);

            // Read stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullContent = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonStr = line.slice(6);
                        try {
                            const data = JSON.parse(jsonStr);
                            if (data.content) {
                                fullContent += data.content;
                                contentDiv.textContent = fullContent;
                                this.scrollToBottom();
                            }
                            if (data.conversation_id) {
                                this.state.conversationId = data.conversation_id;
                            }
                        } catch (e) {
                            // Ignore parse errors
                        }
                    }
                }
            }

            this.state.messages.push({ role: 'assistant', content: fullContent });
        },

        /**
         * Scroll to bottom of messages
         */
        scrollToBottom: function() {
            this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
        },

        /**
         * Escape HTML to prevent XSS
         */
        escapeHtml: function(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },
    };

    // Export to window
    window.CRAFT = CRAFT;

})(window);
