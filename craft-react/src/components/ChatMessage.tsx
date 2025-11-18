/**
 * ChatMessage Component
 */

import React from 'react'
import type { Message } from '../types'

interface ChatMessageProps {
  message: Message
  showTimestamp?: boolean
  enableMarkdown?: boolean
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  showTimestamp = false,
  enableMarkdown = false,
}) => {
  const isUser = message.role === 'user'

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('default', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  return (
    <div
      className={`craft-message ${isUser ? 'craft-message-user' : 'craft-message-assistant'}`}
    >
      <div className="craft-message-content">
        {enableMarkdown ? (
          <div dangerouslySetInnerHTML={{ __html: formatMarkdown(message.content) }} />
        ) : (
          <p>{message.content}</p>
        )}
      </div>
      {showTimestamp && (
        <div className="craft-message-timestamp">{formatTime(message.timestamp)}</div>
      )}
    </div>
  )
}

// Simple markdown formatter (can be replaced with a library like marked or remark)
function formatMarkdown(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br />')
}
