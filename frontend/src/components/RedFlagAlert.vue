<template>
  <Card
    v-if="redFlags.length > 0"
    class="mb-4 border-destructive/20 bg-destructive/5"
    role="alert"
  >
    <CardContent class="pt-4">
      <div class="flex items-start gap-3">
        <div class="shrink-0">
          <svg
            class="h-6 w-6 text-destructive"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <div class="flex-1">
          <h3 class="text-lg font-semibold text-destructive">Urgent: Immediate Medical Attention Required</h3>
          <div class="mt-2 space-y-2">
            <p v-for="(flag, index) in redFlags" :key="index" class="text-sm text-destructive/80">
              {{ flag }}
            </p>
          </div>
          <div class="mt-3 border-t border-destructive/20 pt-3">
            <p class="text-sm font-semibold text-destructive">
              {{ actionText }}
            </p>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TriageLevel } from '@/types/chat'
import { Card, CardContent } from '@/components/ui/card'

const props = defineProps<{
  redFlags: string[]
  triage: TriageLevel
}>()

const actionText = computed(() => {
  if (props.triage === '911') {
    return '🚨 Call 911 immediately'
  } else if (props.triage === 'ER') {
    return '🏥 Go to the Emergency Room immediately or call 911'
  }
  return 'Seek immediate medical attention'
})
</script>
