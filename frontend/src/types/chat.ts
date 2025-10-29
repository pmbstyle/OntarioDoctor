export interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface Citation {
  id: number
  title: string
  url: string
  source: string
}

export type TriageLevel = 'primary-care' | 'ER' | '911'

export interface ChatRequest {
  messages: Message[]
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
  triage: TriageLevel
  red_flags: string[]
  latency_ms?: number
}
