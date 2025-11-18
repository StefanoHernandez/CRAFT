/**
 * CRAFT React - Main Entry Point
 */

export { CraftChat } from './CraftChat'
export { useCraft } from './hooks/useCraft'
export { ChatMessage } from './components/ChatMessage'
export { ChatInput } from './components/ChatInput'
export { ChatWindow } from './components/ChatWindow'

export type {
  Message,
  ChatResponse,
  StreamChunk,
  CraftConfig,
  UseCraftOptions,
  ChatState,
  Theme,
  CraftChatProps,
} from './types'
