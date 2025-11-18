/**
 * CRAFT React Types
 */

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

export interface ChatResponse {
  content: string
  role: 'assistant'
  model?: string
  finish_reason?: string
  usage?: {
    input_tokens?: number
    output_tokens?: number
  }
}

export interface StreamChunk {
  content: string
  role: 'assistant'
  model?: string
  finish_reason?: string | null
}

export interface CraftConfig {
  apiUrl: string
  apiKey?: string
  conversationId?: string
  stream?: boolean
  headers?: Record<string, string>
}

export interface UseCraftOptions extends CraftConfig {
  onError?: (error: Error) => void
  onStreamStart?: () => void
  onStreamEnd?: () => void
}

export interface ChatState {
  messages: Message[]
  isLoading: boolean
  error: Error | null
  conversationId: string | null
}

export type Theme = 'light' | 'dark' | 'auto'

export interface CraftChatProps {
  config: CraftConfig
  theme?: Theme
  className?: string
  placeholder?: string
  welcomeMessage?: string
  showTimestamp?: boolean
  enableMarkdown?: boolean
  maxHeight?: string
  onMessageSent?: (message: string) => void
  onResponseReceived?: (response: ChatResponse) => void
}
