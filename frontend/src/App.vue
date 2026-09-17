<script setup lang="ts">
import { ref } from 'vue'
import ChatPanel from './components/ChatPanel.vue'
import DocPanel from './components/DocPanel.vue'

const tab = ref<'chat' | 'docs'>('chat')
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="brand">
        <span class="logo"></span>
        <span>知识库 Agent 助手</span>
      </div>
      <nav class="tabs">
        <button :class="{ active: tab === 'chat' }" @click="tab = 'chat'">对话</button>
        <button :class="{ active: tab === 'docs' }" @click="tab = 'docs'">知识库</button>
      </nav>
    </header>
    <main class="app-main">
      <ChatPanel v-if="tab === 'chat'" />
      <DocPanel v-else />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  max-width: 920px;
  margin: 0 auto;
  height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 0 16px;
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 4px;
  border-bottom: 1px solid var(--border);
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}
.logo {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  background: var(--primary);
}
.tabs button {
  border: none;
  background: none;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-2);
  font-size: 14px;
}
.tabs button.active {
  background: var(--primary-weak);
  color: var(--primary);
}
.app-main {
  flex: 1;
  min-height: 0;
  padding: 16px 0;
}
</style>
