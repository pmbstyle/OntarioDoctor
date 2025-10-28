<template>
  <Card v-if="citations.length > 0" class="mt-3">
    <CardContent class="pt-4">
      <h4 class="mb-3 text-sm font-semibold text-foreground">Sources:</h4>
      <div class="space-y-2">
        <a
          v-for="citation in citations"
          :key="citation.id"
          :href="citation.url"
          target="_blank"
          rel="noopener noreferrer"
          class="flex items-start gap-3 rounded-md border bg-muted/50 p-3 text-sm transition-colors hover:bg-muted"
        >
          <span class="font-mono text-xs font-semibold text-primary">[{{ citation.id }}]</span>
          <div class="flex-1">
            <p class="font-medium text-foreground">{{ citation.title }}</p>
            <p class="text-xs text-muted-foreground">{{ citation.source }}</p>
          </div>
          <svg
            class="h-4 w-4 shrink-0 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
        </a>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import type { Citation } from '@/types/chat'
import { Card, CardContent } from '@/components/ui/card'

defineProps<{
  citations: Citation[]
}>()
</script>
