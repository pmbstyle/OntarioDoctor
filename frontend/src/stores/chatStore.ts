/**
 * Chat store - manages conversation state
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Message, Citation, TriageLevel } from '@/types/chat'
import { apiClient } from '@/api/client'

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref<Message[]>([])
  const citations = ref<Citation[]>([])
  const currentTriage = ref<TriageLevel>('primary-care')
  const redFlags = ref<string[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const latency = ref<number | null>(null)

  // Computed
  const hasMessages = computed(() => messages.value.length > 0)
  const isEmergency = computed(() => currentTriage.value === 'ER' || currentTriage.value === '911')
  const lastMessage = computed(() => messages.value[messages.value.length - 1])

  // Actions
  async function sendMessage(content: string) {
    if (!content.trim()) return

    // Clear previous error
    error.value = null

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content: content.trim(),
    }
    messages.value.push(userMessage)

    // Set loading state
    loading.value = true

    try {
      // Call API
      const response = await apiClient.sendMessage(messages.value)

      // Add assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.answer,
      }
      messages.value.push(assistantMessage)

      // Update state
      citations.value = response.citations
      currentTriage.value = response.triage
      redFlags.value = response.red_flags
      latency.value = response.latency_ms || null

    } catch (err) {
      error.value = err instanceof Error ? err.message : 'An error occurred'
      console.error('Chat error:', err)
    } finally {
      loading.value = false
    }
  }

  function clearHistory() {
    messages.value = []
    citations.value = []
    currentTriage.value = 'primary-care'
    redFlags.value = []
    error.value = null
    latency.value = null
  }

  function removeLastMessage() {
    if (messages.value.length > 0) {
      messages.value.pop()
    }
  }

  return {
    // State
    messages,
    citations,
    currentTriage,
    redFlags,
    loading,
    error,
    latency,
    // Computed
    hasMessages,
    isEmergency,
    lastMessage,
    // Actions
    sendMessage,
    clearHistory,
    removeLastMessage,
  }
})
