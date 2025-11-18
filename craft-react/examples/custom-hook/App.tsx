/**
 * Custom Hook Example - useCraft
 */

import React from 'react'
import { useCraft } from '@craft-ai/react'

export default function App() {
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    cancelRequest,
  } = useCraft({
    apiUrl: 'http://localhost:8000',
    stream: true,
    onError: (err) => {
      console.error('Chat error:', err)
    },
  })

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const message = formData.get('message') as string
    if (message.trim()) {
      sendMessage(message)
      e.currentTarget.reset()
    }
  }

  return (
    <div style={{ maxWidth: '800px', margin: '2rem auto', padding: '1rem' }}>
      <h1>CRAFT React - Custom Hook Example</h1>

      <div style={{ marginBottom: '1rem' }}>
        <button onClick={clearMessages}>Clear Chat</button>
        {isLoading && (
          <button onClick={cancelRequest} style={{ marginLeft: '0.5rem' }}>
            Cancel
          </button>
        )}
      </div>

      {error && (
        <div
          style={{
            background: '#fee',
            color: '#c00',
            padding: '1rem',
            borderRadius: '4px',
            marginBottom: '1rem',
          }}
        >
          Error: {error.message}
        </div>
      )}

      <div
        style={{
          border: '1px solid #ccc',
          borderRadius: '8px',
          padding: '1rem',
          minHeight: '400px',
          maxHeight: '500px',
          overflowY: 'auto',
          marginBottom: '1rem',
        }}
      >
        {messages.length === 0 && (
          <p style={{ textAlign: 'center', color: '#999' }}>
            No messages yet. Start a conversation!
          </p>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              marginBottom: '1rem',
              padding: '0.75rem',
              borderRadius: '8px',
              background: msg.role === 'user' ? '#3b82f6' : '#f3f4f6',
              color: msg.role === 'user' ? 'white' : 'black',
              maxWidth: '80%',
              marginLeft: msg.role === 'user' ? 'auto' : '0',
              marginRight: msg.role === 'user' ? '0' : 'auto',
            }}
          >
            <div style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>
              {msg.role === 'user' ? 'You' : 'Assistant'}
            </div>
            <div>{msg.content}</div>
            <div style={{ fontSize: '0.75rem', marginTop: '0.25rem', opacity: 0.7 }}>
              {msg.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}

        {isLoading && (
          <div style={{ textAlign: 'center', color: '#999' }}>
            <div>Assistant is typing...</div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
        <input
          type="text"
          name="message"
          placeholder="Type your message..."
          disabled={isLoading}
          style={{
            flex: 1,
            padding: '0.75rem',
            border: '1px solid #ccc',
            borderRadius: '8px',
            fontSize: '1rem',
          }}
        />
        <button
          type="submit"
          disabled={isLoading}
          style={{
            padding: '0.75rem 1.5rem',
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '1rem',
          }}
        >
          Send
        </button>
      </form>
    </div>
  )
}
