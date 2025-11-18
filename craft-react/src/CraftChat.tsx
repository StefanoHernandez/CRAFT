/**
 * CraftChat - Main React Component
 */

import React, { useEffect } from 'react'
import { useCraft } from './hooks/useCraft'
import { ChatWindow } from './components/ChatWindow'
import { ChatInput } from './components/ChatInput'
import type { CraftChatProps } from './types'
import './styles.css'

export const CraftChat: React.FC<CraftChatProps> = ({
  config,
  theme = 'light',
  className = '',
  placeholder = 'Type your message...',
  welcomeMessage = '👋 Hi! How can I help you today?',
  showTimestamp = false,
  enableMarkdown = true,
  maxHeight = '600px',
  onMessageSent,
  onResponseReceived: _onResponseReceived,
}) => {
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    cancelRequest,
  } = useCraft({
    ...config,
    onStreamStart: () => {
      // Optional: handle stream start
    },
    onStreamEnd: () => {
      // Optional: handle stream end
    },
    onError: (err) => {
      console.error('CRAFT Error:', err)
    },
  })

  // Apply theme
  useEffect(() => {
    const resolvedTheme =
      theme === 'auto'
        ? window.matchMedia('(prefers-color-scheme: dark)').matches
          ? 'dark'
          : 'light'
        : theme

    document.documentElement.setAttribute('data-craft-theme', resolvedTheme)
  }, [theme])

  const handleSend = async (message: string) => {
    onMessageSent?.(message)
    await sendMessage(message)
  }

  return (
    <div className={`craft-chat-container ${className}`} data-theme={theme}>
      <div className="craft-chat-header">
        <h3>CRAFT Chat</h3>
        <div className="craft-chat-actions">
          {isLoading && (
            <button
              onClick={cancelRequest}
              className="craft-action-button"
              title="Cancel"
            >
              ⏸
            </button>
          )}
          <button
            onClick={clearMessages}
            className="craft-action-button"
            title="Clear chat"
          >
            🗑️
          </button>
        </div>
      </div>

      {error && (
        <div className="craft-error-banner">
          <span>⚠️ {error.message}</span>
        </div>
      )}

      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        showTimestamp={showTimestamp}
        enableMarkdown={enableMarkdown}
        welcomeMessage={welcomeMessage}
        maxHeight={maxHeight}
      />

      <ChatInput
        onSend={handleSend}
        disabled={isLoading}
        placeholder={placeholder}
      />
    </div>
  )
}
