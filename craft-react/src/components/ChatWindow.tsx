/**
 * ChatWindow Component
 */

import React, { useEffect, useRef } from 'react'
import { ChatMessage } from './ChatMessage'
import type { Message } from '../types'

interface ChatWindowProps {
  messages: Message[]
  isLoading?: boolean
  showTimestamp?: boolean
  enableMarkdown?: boolean
  welcomeMessage?: string
  maxHeight?: string
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isLoading = false,
  showTimestamp = false,
  enableMarkdown = false,
  welcomeMessage,
  maxHeight = '500px',
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="craft-chat-window" style={{ maxHeight }}>
      {messages.length === 0 && welcomeMessage && (
        <div className="craft-welcome-message">
          <p>{welcomeMessage}</p>
        </div>
      )}

      {messages.map((message) => (
        <ChatMessage
          key={message.id}
          message={message}
          showTimestamp={showTimestamp}
          enableMarkdown={enableMarkdown}
        />
      ))}

      {isLoading && (
        <div className="craft-loading">
          <div className="craft-loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}
