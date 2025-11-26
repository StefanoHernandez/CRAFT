import { useState, useCallback } from 'react';
import { useAgentStream } from './useAgentStream';
import {
    AgentEvent,
    AgentStreamState,
    Message,
    AgentToolCall,
    UseAgentStreamOptions
} from '../types';

/**
 * Hook to manage the full state of an agent interaction.
 * Uses useAgentStream for connection and maintains messages/tools state.
 */
export function useAgentState(options: Omit<UseAgentStreamOptions, 'onEvent'>) {
    const [state, setState] = useState<AgentStreamState>({
        isConnected: false,
        isThinking: false,
        currentStep: 0,
        toolCalls: [],
        messages: [],
        error: null
    });

    const handleEvent = useCallback((event: AgentEvent) => {
        setState(prev => {
            const newState = { ...prev };

            switch (event.type) {
                case 'agent_start':
                    newState.isThinking = true;
                    newState.error = null;
                    break;

                case 'agent_thought':
                    // Optional: Display thoughts if needed
                    break;

                case 'tool_call':
                    const toolCall: AgentToolCall = {
                        tool_name: event.data.tool_name,
                        arguments: event.data.arguments,
                        id: event.data.id
                    };
                    newState.toolCalls = [...prev.toolCalls, toolCall];
                    break;

                case 'tool_result':
                    // Update existing tool call with result if needed
                    // or just log it. For now we just track calls.
                    break;

                case 'agent_response':
                    // Append assistant message
                    const newMessage: Message = {
                        id: Date.now().toString(),
                        role: 'assistant',
                        content: event.data.content,
                        timestamp: new Date()
                    };
                    newState.messages = [...prev.messages, newMessage];
                    newState.isThinking = false;
                    break;

                case 'agent_finish':
                    newState.isThinking = false;
                    break;

                case 'error':
                    newState.error = new Error(event.data.error || 'Unknown error');
                    newState.isThinking = false;
                    break;
            }

            return newState;
        });
    }, []);

    const { isConnected, error, sendMessage, reconnect } = useAgentStream({
        ...options,
        onEvent: handleEvent
    });

    // Sync connection state
    if (state.isConnected !== isConnected) {
        setState(prev => ({ ...prev, isConnected }));
    }

    // Sync error state from hook if not already set
    if (error && !state.error) {
        setState(prev => ({ ...prev, error }));
    }

    const sendUserMessage = useCallback((content: string) => {
        // Optimistically add user message
        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content,
            timestamp: new Date()
        };
        setState(prev => ({
            ...prev,
            messages: [...prev.messages, userMsg],
            isThinking: true
        }));

        sendMessage(content);
    }, [sendMessage]);

    return {
        ...state,
        sendMessage: sendUserMessage,
        reconnect
    };
}
