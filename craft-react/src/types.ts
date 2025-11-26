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

// Agent Streaming Types

export type AgentEventType =
  | 'agent_start'
  | 'agent_thought'
  | 'tool_call'
  | 'tool_result'
  | 'agent_response'
  | 'agent_finish'
  | 'error'

export interface AgentEvent {
  type: AgentEventType
  agent_name: string
  timestamp: string
  data: any
  metadata?: Record<string, any>
}

export interface AgentToolCall {
  tool_name: string
  arguments: Record<string, any>
  id?: string
}

export interface AgentToolResult {
  tool_name: string
  result: any
  success: boolean
  error?: string
}

export interface UseAgentStreamOptions {
  agentId: string
  wsUrl?: string // Defaults to ws://localhost:8000/ws
  onEvent?: (event: AgentEvent) => void
  onError?: (error: Error) => void
  onFinish?: (result: string) => void
}

export interface AgentStreamState {
  isConnected: boolean
  isThinking: boolean
  currentStep: number
  toolCalls: AgentToolCall[]
  messages: Message[]
  error: Error | null
}
