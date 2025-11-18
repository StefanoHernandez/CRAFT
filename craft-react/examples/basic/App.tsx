/**
 * Basic Example - CraftChat Component
 */

import React from 'react'
import { CraftChat } from '@craft-ai/react'
import '@craft-ai/react/styles.css'

export default function App() {
  return (
    <div style={{ maxWidth: '600px', margin: '2rem auto' }}>
      <h1>CRAFT React - Basic Example</h1>

      <CraftChat
        config={{
          apiUrl: 'http://localhost:8000',
          stream: true,
        }}
        theme="light"
        welcomeMessage="👋 Hi! I'm your AI assistant. How can I help you today?"
        placeholder="Type your message..."
        showTimestamp={false}
        enableMarkdown={true}
        maxHeight="500px"
        onMessageSent={(message) => {
          console.log('User sent:', message)
        }}
        onResponseReceived={(response) => {
          console.log('Assistant responded:', response.content)
        }}
      />
    </div>
  )
}
