<script setup lang="ts">
import type { ChatMessage } from '../types'

const props = defineProps<{ message: ChatMessage }>()

const TOOL_LABELS: Record<string, string> = {
  knowledge_base_search: '检索知识库',
  web_search: '联网搜索',
  query_structured_data: '查询数据库',
}
</script>

<template>
  <div class="msg" :class="props.message.role">
    <div class="bubble" :class="{ error: props.message.error }">
      <div v-if="props.message.tools?.length" class="tools">
        <span
          v-for="(t, i) in props.message.tools"
          :key="i"
          class="chip"
          :class="t.done ? 'done' : 'running'"
        >
          {{ TOOL_LABELS[t.name] ?? t.name }}{{ t.done ? ' · 完成' : '…' }}
        </span>
      </div>
      <p class="content">{{ props.message.content || (props.message.role === 'assistant' ? '…' : '') }}</p>
    </div>
  </div>
</template>

<style scoped>
.msg {
  display: flex;
  margin-bottom: 14px;
}
.msg.user {
  justify-content: flex-end;
}
.bubble {
  max-width: 76%;
  border-radius: 12px;
  padding: 10px 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
.msg.user .bubble {
  background: var(--primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.msg.assistant .bubble {
  background: var(--bg);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
}
.bubble.error {
  border-color: #e0a0a0;
  color: #a03030;
}
.tools {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}
.chip {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 999px;
}
.chip.running {
  background: #fff4e2;
  color: var(--warn);
}
.chip.done {
  background: #e2f4ec;
  color: var(--ok);
}
.content {
  margin: 0;
}
</style>
