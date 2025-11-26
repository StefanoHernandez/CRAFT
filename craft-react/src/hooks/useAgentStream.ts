import { useState, useEffect, useRef, useCallback } from 'react';
import { AgentEvent, UseAgentStreamOptions } from '../types';

/**
 * Hook to manage WebSocket streaming connection with a CRAFT agent.
 * Handles connection, reconnection, and event parsing.
 */
export function useAgentStream({
    agentId,
    wsUrl = 'ws://localhost:8000/ws',
    onEvent,
    onError,
    onFinish
}: UseAgentStreamOptions) {
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState<Error | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

    const connect = useCallback(() => {
        try {
            // Close existing connection if any
            if (wsRef.current) {
                wsRef.current.close();
            }

            const url = `${wsUrl}/agents/${agentId}/stream`;
            console.log(`Connecting to CRAFT Agent Stream: ${url}`);

            const ws = new WebSocket(url);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log('CRAFT Agent Stream Connected');
                setIsConnected(true);
                setError(null);
            };

            ws.onmessage = (event) => {
                try {
                    const agentEvent: AgentEvent = JSON.parse(event.data);

                    // Dispatch event to callback
                    if (onEvent) {
                        onEvent(agentEvent);
                    }

                    // Handle specific event types
                    if (agentEvent.type === 'error') {
                        const err = new Error(agentEvent.data.error || 'Unknown agent error');
                        setError(err);
                        if (onError) onError(err);
                    }

                    if (agentEvent.type === 'agent_finish') {
                        if (onFinish) onFinish(agentEvent.data.result);
                    }

                } catch (e) {
                    console.error('Failed to parse agent event:', e);
                }
            };

            ws.onclose = () => {
                console.log('CRAFT Agent Stream Disconnected');
                setIsConnected(false);
                // Attempt reconnection after 3 seconds
                reconnectTimeoutRef.current = setTimeout(() => {
                    console.log('Attempting reconnection...');
                    connect();
                }, 3000);
            };

            ws.onerror = (e) => {
                console.error('WebSocket Error:', e);
                const err = new Error('WebSocket connection error');
                setError(err);
                if (onError) onError(err);
            };

        } catch (e) {
            console.error('Connection failed:', e);
            const err = e instanceof Error ? e : new Error('Connection failed');
            setError(err);
            if (onError) onError(err);
        }
    }, [agentId, wsUrl, onEvent, onError, onFinish]);

    // Initial connection
    useEffect(() => {
        connect();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, [connect]);

    const sendMessage = useCallback((message: string) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'user_message', content: message }));
        } else {
            console.warn('Cannot send message: WebSocket not connected');
        }
    }, []);

    return {
        isConnected,
        error,
        sendMessage,
        reconnect: connect
    };
}
