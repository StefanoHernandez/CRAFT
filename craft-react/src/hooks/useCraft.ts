/**
 * useCraft - Main hook for CRAFT integration
 */

import { useState, useCallback, useRef } from 'react'
import type {
  Message,
  ChatResponse,
  UseCraftOptions,
  ChatState,
  StreamChunk,
} from '../types'

export function useCraft(options: UseCraftOptions) {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
    conversationId: options.conversationId || null,
  })

  const abortControllerRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || state.isLoading) return

      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content,
        timestamp: new Date(),
      }

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isLoading: true,
        error: null,
      }))

      try {
        abortControllerRef.current = new AbortController()

        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
          ...options.headers,
        }

        if (options.apiKey) {
          headers['Authorization'] = `Bearer ${options.apiKey}`
        }

        if (options.stream) {
          // Streaming mode
          options.onStreamStart?.()

          const response = await fetch(`${options.apiUrl}/chat/stream`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
              message: content,
              conversation_id: state.conversationId,
            }),
            signal: abortControllerRef.current.signal,
          })

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }

          const reader = response.body?.getReader()
          const decoder = new TextDecoder()

          let assistantContent = ''
          const assistantMessageId = Date.now().toString()

          if (reader) {
            while (true) {
              const { done, value } = await reader.read()
              if (done) break

              const chunk = decoder.decode(value)
              const lines = chunk.split('\n')

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  const data = line.slice(6)
                  if (data === '[DONE]') continue

                  try {
                    const parsed: StreamChunk = JSON.parse(data)
                    assistantContent += parsed.content

                    setState((prev) => {
                      const existingIndex = prev.messages.findIndex(
                        (m) => m.id === assistantMessageId
                      )

                      if (existingIndex >= 0) {
                        const updated = [...prev.messages]
                        updated[existingIndex] = {
                          ...updated[existingIndex],
                          content: assistantContent,
                        }
                        return { ...prev, messages: updated }
                      } else {
                        return {
                          ...prev,
                          messages: [
                            ...prev.messages,
                            {
                              id: assistantMessageId,
                              role: 'assistant',
                              content: assistantContent,
                              timestamp: new Date(),
                            },
                          ],
                        }
                      }
                    })
                  } catch (e) {
                    // Invalid JSON, skip
                  }
                }
              }
            }
          }

          options.onStreamEnd?.()
        } else {
          // Non-streaming mode
          const response = await fetch(`${options.apiUrl}/chat`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
              message: content,
              conversation_id: state.conversationId,
            }),
            signal: abortControllerRef.current.signal,
          })

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }

          const data: ChatResponse & { conversation_id?: string } =
            await response.json()

          const assistantMessage: Message = {
            id: Date.now().toString(),
            role: 'assistant',
            content: data.content,
            timestamp: new Date(),
          }

          setState((prev) => ({
            ...prev,
            messages: [...prev.messages, assistantMessage],
            conversationId: data.conversation_id || prev.conversationId,
          }))
        }

        setState((prev) => ({ ...prev, isLoading: false }))
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          return // Ignore aborted requests
        }

        const err = error instanceof Error ? error : new Error('Unknown error')
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: err,
        }))
        options.onError?.(err)
      }
    },
    [
      options.apiUrl,
      options.apiKey,
      options.stream,
      options.headers,
      state.conversationId,
      state.isLoading,
    ]
  )

  const clearMessages = useCallback(() => {
    setState((prev) => ({
      ...prev,
      messages: [],
      conversationId: null,
    }))
  }, [])

  const cancelRequest = useCallback(() => {
    abortControllerRef.current?.abort()
    setState((prev) => ({ ...prev, isLoading: false }))
  }, [])

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    error: state.error,
    conversationId: state.conversationId,
    sendMessage,
    clearMessages,
    cancelRequest,
  }
}
