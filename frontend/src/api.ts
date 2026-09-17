import type { DocInfo, SseEvent } from './types'

/** 用 fetch 消费 SSE（EventSource 不支持 POST），
 *  手动解析 "event: xxx\ndata: {...}\n\n" 帧 */
export async function streamChat(
  sessionId: string,
  message: string,
  onEvent: (evt: SseEvent) => void,
): Promise<void> {
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  })
  if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const frames = buffer.split('\n\n')
    buffer = frames.pop() ?? ''
    for (const frame of frames) {
      let eventName = 'message'
      let dataStr = ''
      for (const line of frame.split('\n')) {
        if (line.startsWith('event:')) eventName = line.slice(6).trim()
        else if (line.startsWith('data:')) dataStr += line.slice(5).trim()
      }
      if (dataStr) {
        try {
          onEvent({ event: eventName, data: JSON.parse(dataStr) } as SseEvent)
        } catch {
          /* 忽略不完整帧 */
        }
      }
    }
  }
}

export async function fetchDocuments(): Promise<DocInfo[]> {
  const res = await fetch('/api/documents')
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function uploadDocument(file: File): Promise<DocInfo> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/documents/upload', { method: 'POST', body: form })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export async function deleteDocument(docId: string): Promise<void> {
  const res = await fetch(`/api/documents/${docId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
}
