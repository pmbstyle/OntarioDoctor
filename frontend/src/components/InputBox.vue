<template>
  <div class="bg-card p-4">
    <form @submit.prevent="handleSubmit" class="flex gap-3">
      <Textarea
        v-model="input"
        ref="textareaRef"
        :disabled="disabled"
        :placeholder="placeholder"
        rows="1"
        class="flex-1 h-16 resize-none"
        @keydown="handleKeyDown"
      />
      <Button
        type="submit"
        :disabled="disabled || !input.trim()"
        size="lg"
        class="h-16 px-6 cursor-pointer"
      >
        <span v-if="!loading">Send</span>
        <svg
          v-else
          class="h-5 w-5 animate-spin"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      </Button>
    </form>
    <p class="mt-2 text-xs text-muted-foreground">
      Press Enter to send, Shift+Enter for new line
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

const props = defineProps<{
  disabled?: boolean
  loading?: boolean
  placeholder?: string
}>()

const emit = defineEmits<{
  submit: [content: string]
}>()

const input = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

function handleSubmit() {
  const content = input.value.trim()
  if (!content || props.disabled) return

  emit('submit', content)
  input.value = ''
}

function handleKeyDown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSubmit()
  }
}
</script>
