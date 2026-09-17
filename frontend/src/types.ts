export interface ToolStatus {
  name: string
  done: boolean
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  tools?: ToolStatus[]
  error?: boolean
}

export interface DocInfo {
  doc_id: string
  filename: string
  chunks: number
  created_at: string
}

export type SseEvent =
  | { event: 'token'; data: { content: string } }
  | { event: 'tool_start'; data: { name: string; input: string } }
  | { event: 'tool_end'; data: { name: string } }
  | { event: 'done'; data: Record<string, never> }
  | { event: 'error'; data: { message: string } }
