# @craft-ai/react

React components for [CRAFT](https://github.com/StefanoHernandez/CRAFT) - Chatbot & RAG Framework Toolkit.

[![npm version](https://img.shields.io/npm/v/@craft-ai/react.svg)](https://www.npmjs.com/package/@craft-ai/react)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🎨 **Beautiful UI** - Pre-styled, customizable chat interface
- 🌓 **Dark Mode** - Automatic theme detection and manual control
- ⚡ **Real-time Streaming** - Support for streaming responses
- 🎣 **Custom Hooks** - `useCraft` hook for custom integrations
- 📱 **Responsive** - Mobile-friendly design
- 🔒 **TypeScript** - Full TypeScript support
- 🎯 **Zero Dependencies** - No UI library dependencies (except React)

## Installation

```bash
npm install @craft-ai/react
# or
yarn add @craft-ai/react
# or
pnpm add @craft-ai/react
```

### Peer Dependencies

```bash
npm install react react-dom
```

## Quick Start

### Basic Usage

```tsx
import { CraftChat } from '@craft-ai/react'
import '@craft-ai/react/styles.css'

function App() {
  return (
    <CraftChat
      config={{
        apiUrl: 'http://localhost:8000',
        apiKey: 'your-api-key',  // Optional
        stream: true,
      }}
      theme="light"
      welcomeMessage="👋 Hi! How can I help you today?"
      placeholder="Type your message..."
    />
  )
}
```

### With Custom Hooks

```tsx
import { useCraft } from '@craft-ai/react'

function CustomChat() {
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
  } = useCraft({
    apiUrl: 'http://localhost:8000',
    stream: true,
  })

  return (
    <div>
      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id}>
            <strong>{msg.role}:</strong> {msg.content}
          </div>
        ))}
      </div>

      <button onClick={() => sendMessage('Hello!')}>
        Send Hello
      </button>

      <button onClick={clearMessages}>Clear</button>

      {isLoading && <div>Loading...</div>}
      {error && <div>Error: {error.message}</div>}
    </div>
  )
}
```

## Components

### CraftChat

The main chat component with full UI.

```tsx
<CraftChat
  config={{
    apiUrl: string
    apiKey?: string
    conversationId?: string
    stream?: boolean
    headers?: Record<string, string>
  }}
  theme?: 'light' | 'dark' | 'auto'
  className?: string
  placeholder?: string
  welcomeMessage?: string
  showTimestamp?: boolean
  enableMarkdown?: boolean
  maxHeight?: string
  onMessageSent?: (message: string) => void
  onResponseReceived?: (response: ChatResponse) => void
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `config` | `CraftConfig` | required | API configuration |
| `theme` | `'light' \| 'dark' \| 'auto'` | `'light'` | Theme mode |
| `className` | `string` | `''` | Additional CSS class |
| `placeholder` | `string` | `'Type your message...'` | Input placeholder |
| `welcomeMessage` | `string` | `'👋 Hi! How can I help you today?'` | Initial message |
| `showTimestamp` | `boolean` | `false` | Show message timestamps |
| `enableMarkdown` | `boolean` | `true` | Enable markdown formatting |
| `maxHeight` | `string` | `'600px'` | Maximum height |
| `onMessageSent` | `function` | - | Callback when message is sent |
| `onResponseReceived` | `function` | - | Callback when response received |

### useCraft Hook

Custom hook for building your own chat UI.

```tsx
const {
  messages,
  isLoading,
  error,
  conversationId,
  sendMessage,
  clearMessages,
  cancelRequest,
} = useCraft(options)
```

#### Options

```tsx
interface UseCraftOptions {
  apiUrl: string
  apiKey?: string
  conversationId?: string
  stream?: boolean
  headers?: Record<string, string>
  onError?: (error: Error) => void
  onStreamStart?: () => void
  onStreamEnd?: () => void
}
```

#### Returns

| Property | Type | Description |
|----------|------|-------------|
| `messages` | `Message[]` | Array of messages |
| `isLoading` | `boolean` | Loading state |
| `error` | `Error \| null` | Error state |
| `conversationId` | `string \| null` | Current conversation ID |
| `sendMessage` | `(content: string) => Promise<void>` | Send a message |
| `clearMessages` | `() => void` | Clear all messages |
| `cancelRequest` | `() => void` | Cancel ongoing request |

## Examples

### Dark Mode

```tsx
<CraftChat
  config={{ apiUrl: 'http://localhost:8000' }}
  theme="dark"
/>
```

### Auto Theme (System Preference)

```tsx
<CraftChat
  config={{ apiUrl: 'http://localhost:8000' }}
  theme="auto"  // Automatically detects system preference
/>
```

### With Authentication

```tsx
<CraftChat
  config={{
    apiUrl: 'https://api.example.com',
    apiKey: 'your-api-key',
    headers: {
      'X-Custom-Header': 'value'
    }
  }}
/>
```

### Streaming

```tsx
<CraftChat
  config={{
    apiUrl: 'http://localhost:8000',
    stream: true,  // Enable streaming responses
  }}
/>
```

### With Callbacks

```tsx
<CraftChat
  config={{ apiUrl: 'http://localhost:8000' }}
  onMessageSent={(message) => {
    console.log('User sent:', message)
  }}
  onResponseReceived={(response) => {
    console.log('Assistant responded:', response.content)
  }}
/>
```

### Custom Styling

```tsx
<CraftChat
  config={{ apiUrl: 'http://localhost:8000' }}
  className="my-custom-chat"
  maxHeight="400px"
/>
```

```css
.my-custom-chat {
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}
```

### Building Custom UI

```tsx
import { useCraft, ChatWindow, ChatInput } from '@craft-ai/react'

function MyCustomChat() {
  const {
    messages,
    isLoading,
    sendMessage,
    clearMessages,
  } = useCraft({
    apiUrl: 'http://localhost:8000',
    stream: true,
  })

  return (
    <div className="my-chat">
      <header>
        <h1>My Custom Chat</h1>
        <button onClick={clearMessages}>Clear</button>
      </header>

      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        showTimestamp={true}
        enableMarkdown={true}
      />

      <ChatInput
        onSend={sendMessage}
        disabled={isLoading}
        placeholder="Ask me anything..."
      />
    </div>
  )
}
```

## TypeScript

Full TypeScript support with exported types:

```tsx
import type {
  Message,
  ChatResponse,
  StreamChunk,
  CraftConfig,
  UseCraftOptions,
  ChatState,
  Theme,
  CraftChatProps,
} from '@craft-ai/react'
```

## Styling

### Using the Default Styles

```tsx
import '@craft-ai/react/styles.css'
```

### CSS Variables

Customize the appearance using CSS variables:

```css
:root {
  --craft-primary: #3b82f6;
  --craft-bg-light: #ffffff;
  --craft-bg-dark: #1f2937;
  --craft-text-light: #111827;
  --craft-text-dark: #f9fafb;
  --craft-border-light: #e5e7eb;
  --craft-border-dark: #374151;
  --craft-user-bg-light: #3b82f6;
  --craft-user-bg-dark: #2563eb;
  --craft-assistant-bg-light: #f3f4f6;
  --craft-assistant-bg-dark: #374151;
}
```

## API Server Setup

Make sure you have a CRAFT API server running:

```python
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.integrations.api import CRAFTServer

chatbot = Chatbot(
    provider=AnthropicProvider(api_key="your-key"),
    memory=True
)

server = CRAFTServer(chatbot=chatbot, enable_cors=True)
server.run(port=8000)
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](../CONTRIBUTING.md).

## License

MIT © [CRAFT Contributors](https://github.com/StefanoHernandez/CRAFT)

## Links

- [CRAFT Main Repository](https://github.com/StefanoHernandez/CRAFT)
- [Documentation](https://github.com/StefanoHernandez/CRAFT#readme)
- [npm Package](https://www.npmjs.com/package/@craft-ai/react)
- [Issues](https://github.com/StefanoHernandez/CRAFT/issues)

## Support

For questions and support, please open an issue in the [main repository](https://github.com/StefanoHernandez/CRAFT/issues).
