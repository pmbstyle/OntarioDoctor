<template>
  <Card class="w-full max-w-6xl mb-4">
    <div class="w-full flex items-center justify-between px-6 py-4">
      <div class="flex items-center gap-2">
        <img :src="Logo" alt="OntarioDoctor Logo" class="h-10" />
        <div class="flex flex-col">
          <h1 class="text-2xl font-bold text-foreground">OntarioDoctor</h1>
          <p class="text-sm text-muted-foreground">Ontario Medical Assistant</p>
        </div>
      </div>
      <Button
        @click="handleClearHistory"
        variant="outline"
        size="sm"
        class="cursor-pointer"
      >
        Clear History
      </Button>
    </div>
  </Card>

  <Card
    class="flex flex-1 w-full max-w-6xl flex-col p-0 overflow-hidden"
    :class="{'flex-col items-center justify-center': !chatStore.hasMessages}"
  >
    <Card v-if="!chatStore.hasMessages" class="text-center">
      <CardContent class="pt-6">
        <div class="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
          <svg
            class="h-8 w-8 text-primary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        </div>
        <h2 class="mb-2 text-xl font-semibold text-foreground">Welcome to OntarioDoctor</h2>
        <p class="mb-4 text-muted-foreground">
          I'm here to help you understand your symptoms with information grounded in medical sources.
        </p>
        <Card class="mx-auto max-w-2xl border-primary/20 bg-primary/5 text-left">
          <CardContent class="pt-4">
            <h3 class="mb-2 font-semibold text-primary">Ontario Resources:</h3>
            <ul class="space-y-1 text-sm text-primary/80">
              <li>📞 <strong>Telehealth Ontario:</strong> <a href="tel:1-866-797-0000" class="underline">1-866-797-0000</a> (24/7)</li>
              <li>🏥 <strong>Emergency:</strong> <a href="tel:911" class="underline">911</a></li>
              <li>👨‍⚕️ <strong>Non-urgent:</strong> See your family doctor or visit a walk-in clinic</li>
            </ul>
          </CardContent>
        </Card>
        <p class="mt-4 text-xs text-muted-foreground">
          This is not medical advice. For emergencies, call 911.
        </p>
      </CardContent>
    </Card>
    <ScrollArea v-else ref="messagesContainer" class="flex-1 px-6 py-6 h-full">
      <div class="w-full space-y-6">
        <!-- Red Flag Alert -->
        <RedFlagAlert
          v-if="chatStore.isEmergency"
          :red-flags="chatStore.redFlags"
          :triage="chatStore.currentTriage"
        />

        <!-- Messages -->
        <div v-for="(message, index) in chatStore.messages" :key="index" class="space-y-4">
          <MessageBubble :message="message" :show-timestamp="false" />

          <!-- Citations (show after assistant messages) -->
          <CitationCard
            v-if="message.role === 'assistant' && index === chatStore.messages.length - 1"
            :citations="chatStore.citations"
          />
        </div>

        <!-- Loading Indicator -->
        <div v-if="chatStore.loading" class="flex justify-start">
          <Card class="bg-muted/50">
            <CardContent class="pt-4">
              <div class="flex items-center gap-2">
                <div class="flex gap-1">
                  <Skeleton class="h-2 w-2 rounded-full" />
                  <Skeleton class="h-2 w-2 rounded-full" />
                  <Skeleton class="h-2 w-2 rounded-full" />
                </div>
                <span class="text-sm text-muted-foreground">Analyzing your symptoms...</span>
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- Error Message -->
        <Card v-if="chatStore.error" class="border-destructive/20 bg-destructive/5">
          <CardContent>
            <p class="font-semibold text-destructive">Error:</p>
            <p class="text-sm text-destructive/80">{{ chatStore.error }}</p>
          </CardContent>
        </Card>
      </div>
    </ScrollArea>
  </Card>
  <Card class="w-full max-w-6xl mt-4">
    <InputBox
      :disabled="chatStore.loading"
      :loading="chatStore.loading"
      placeholder="Describe your symptoms (e.g., 'I have a fever of 38.5°C for 2 days and sore throat')"
      @submit="handleSendMessage"
    />
  </Card>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chatStore'
import MessageBubble from './MessageBubble.vue'
import CitationCard from './CitationCard.vue'
import RedFlagAlert from './RedFlagAlert.vue'
import InputBox from './InputBox.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import Logo from '@/assets/logo.png'

const chatStore = useChatStore()
const messagesContainer = ref<HTMLElement | null>(null)

async function handleSendMessage(content: string) {
  await chatStore.sendMessage(content)
  scrollToBottom()
}

function handleClearHistory() {
  if (confirm('Are you sure you want to clear your chat history?')) {
    chatStore.clearHistory()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// Auto-scroll when new messages arrive
watch(
  () => chatStore.messages.length,
  () => {
    scrollToBottom()
  }
)
</script>
