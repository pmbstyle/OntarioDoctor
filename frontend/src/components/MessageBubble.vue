<template>
  <div
    :class="[
      'flex',
      message.role === 'user' ? 'justify-end items-end' : 'justify-end items-end flex-row-reverse',
    ]"
  >
    <Card
      :class="[
        'max-w-[80%] py-0',
        message.role === 'user'
          ? 'bg-primary text-primary-foreground mr-4'
          : 'bg-muted/50 ml-4',
      ]"
    >
      <CardContent class="p-4">
        <!-- Message content -->
        <div class="whitespace-pre-wrap wrap-break-word" v-html="formattedContent" />

        <!-- Timestamp -->
        <div
          v-if="showTimestamp"
          :class="[
            'mt-2 text-xs',
            message.role === 'user' ? 'text-primary-foreground/70' : 'text-muted-foreground',
          ]"
        >
          {{ timestamp }}
        </div>
      </CardContent>
    </Card>
    <Avatar>
      <AvatarImage v-if="message.role === 'user'" :src="userAvatar" />
      <AvatarImage v-else :src="doctorAvatar" />
      <AvatarFallback v-if="message.role === 'user'">U</AvatarFallback>
      <AvatarFallback v-else>A</AvatarFallback>
    </Avatar>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Message } from '@/types/chat'
import { Card, CardContent } from '@/components/ui/card'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import doctorAvatar from '@/assets/doctor.png'
import userAvatar from '@/assets/user.png'

const props = defineProps<{
  message: Message
  showTimestamp?: boolean
}>()

const timestamp = computed(() => {
  return new Date().toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })
})

const formattedContent = computed(() => {
  let content = props.message.content

  // Escape HTML to prevent XSS
  content = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Convert citations [1], [2] to styled spans with inline styles
  content = content.replace(
    /\[(\d+)\]/g,
    '<span class="citation-ref" style="margin: 0 0.25rem; display: inline-block; border-radius: 0.25rem; background-color: rgb(59 130 246); padding: 0.125rem 0.375rem; font-size: 0.75rem; font-weight: 600; color: white;">[<strong>$1</strong>]</span>'
  )

  // Convert **bold** to <strong>
  content = content.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')

  // Convert *italic* to <em>
  content = content.replace(/\*(.+?)\*/g, '<em>$1</em>')

  // Convert newlines to <br>
  content = content.replace(/\n/g, '<br>')

  return content
})
</script>

<style scoped>
:deep(strong) {
  font-weight: 600;
}

:deep(em) {
  font-style: italic;
}
</style>
