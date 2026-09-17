<script setup lang="ts">
import { nextTick, reactive, ref } from 'vue'
import { streamChat } from '../api'
import type { ChatMessage } from '../types'
import MessageItem from './MessageItem.vue'

const messages = ref<ChatMessage[]>([])
const input = ref('')
const sending = ref(false)
const listEl = ref<HTMLElement | null>(null)

// 会话 id 存 localStorage，刷新页面不丢上下文（后端记忆按 session_id 隔离）
const sessionId =
  localStorage.getItem('session_id') || crypto.randomUUID()
localStorage.setItem('session_id', sessionId)

function scrollToBottom() {
  nextTick(() => listEl.value?.scrollTo({ top: listEl.value.scrollHeight }))
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: text })
  // 用 reactive() 包装：直接修改其属性才会触发界面逐 token 刷新
  const reply = reactive<ChatMessage>({ role: 'assistant', content: '', tools: [] })
  messages.value.push(reply)
  sending.value = true
  scrollToBottom()

  try {
    await streamChat(sessionId, text, (evt) => {
      if (evt.event === 'token') {
        reply.content += evt.data.content
      } else if (evt.event === 'tool_start') {
        reply.tools!.push({ name: evt.data.name, done: false })
      } else if (evt.event === 'tool_end') {
        const pending = reply.tools!.filter((t) => !t.done).pop()
        if (pending) pending.done = true
      } else if (evt.event === 'error') {
        reply.error = true
        reply.content += `\n[出错] ${evt.data.message}`
      }
      scrollToBottom()
    })
  } catch {
    reply.error = true
    reply.content += '\n[连接失败] 请确认后端已启动（uvicorn app.main:app --reload）'
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}
</script>

<template>
  <div class="chat-panel">
    <div ref="listEl" class="message-list">
      <div v-if="messages.length === 0" class="empty">
        <p>试着问我：</p>
        <ul>
          <li>「查一下这个月卖得最好的商品是什么」（Agent 会调 SQL 工具）</li>
          <li>「最近 AI Agent 领域有什么新进展？」（Agent 会联网搜索）</li>
          <li>先去「知识库」页上传一份文档，再来问文档里的内容（RAG 检索）</li>
        </ul>
      </div>
      <MessageItem v-for="(m, i) in messages" :key="i" :message="m" />
    </div>
    <div class="composer">
      <textarea
        v-model="input"
        :disabled="sending"
        rows="2"
        placeholder="输入问题，Enter 发送，Shift+Enter 换行"
        @keydown="onKeydown"
      ></textarea>
      <button :disabled="sending || !input.trim()" @click="send">
        {{ sending ? '回答中…' : '发送' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.empty {
  color: var(--text-2);
  line-height: 1.9;
  padding: 40px 12px;
}
.empty ul {
  padding-left: 18px;
}
.composer {
  display: flex;
  gap: 10px;
  padding: 12px;
  border-top: 1px solid var(--border);
}
.composer textarea {
  flex: 1;
  resize: none;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  font: inherit;
  outline: none;
}
.composer textarea:focus {
  border-color: var(--primary);
}
.composer button {
  border: none;
  background: var(--primary);
  color: #fff;
  border-radius: 8px;
  padding: 0 20px;
  cursor: pointer;
}
.composer button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
