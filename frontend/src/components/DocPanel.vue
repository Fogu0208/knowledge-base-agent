<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { deleteDocument, fetchDocuments, uploadDocument } from '../api'
import type { DocInfo } from '../types'

const docs = ref<DocInfo[]>([])
const uploading = ref(false)
const error = ref('')

async function refresh() {
  try {
    docs.value = await fetchDocuments()
  } catch {
    error.value = '无法连接后端，请确认服务已启动'
  }
}

async function onUpload(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files?.length) return
  uploading.value = true
  error.value = ''
  try {
    for (const file of Array.from(files)) {
      await uploadDocument(file)
    }
    await refresh()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    uploading.value = false
    ;(e.target as HTMLInputElement).value = ''
  }
}

async function onDelete(doc: DocInfo) {
  if (!confirm(`删除「${doc.filename}」？该文档将从知识库中移除。`)) return
  await deleteDocument(doc.doc_id)
  await refresh()
}

onMounted(refresh)
</script>

<template>
  <div class="doc-panel">
    <div class="toolbar">
      <label class="upload-btn" :class="{ disabled: uploading }">
        {{ uploading ? '入库中（切分 + 向量化）…' : '上传文档（pdf / txt / md）' }}
        <input type="file" multiple accept=".pdf,.txt,.md" :disabled="uploading" @change="onUpload" />
      </label>
      <span class="hint">上传后会自动切分并向量化，之后在对话中直接问文档内容即可</span>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <table v-if="docs.length">
      <thead>
        <tr>
          <th>文件名</th>
          <th>切片数</th>
          <th>上传时间</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="d in docs" :key="d.doc_id">
          <td>{{ d.filename }}</td>
          <td>{{ d.chunks }}</td>
          <td>{{ d.created_at }}</td>
          <td><button class="del" @click="onDelete(d)">删除</button></td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!error" class="empty">还没有文档。上传一份试试，比如一份产品说明或你的学习笔记。</p>
  </div>
</template>

<style scoped>
.doc-panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}
.upload-btn {
  display: inline-block;
  background: var(--primary);
  color: #fff;
  border-radius: 8px;
  padding: 8px 18px;
  cursor: pointer;
}
.upload-btn.disabled {
  opacity: 0.6;
  cursor: wait;
}
.upload-btn input {
  display: none;
}
.hint {
  color: var(--text-2);
  font-size: 12px;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 18px;
}
th,
td {
  text-align: left;
  padding: 10px 8px;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
}
th {
  color: var(--text-2);
  font-weight: 500;
}
.del {
  border: 1px solid var(--border);
  background: none;
  border-radius: 6px;
  padding: 3px 12px;
  cursor: pointer;
  color: #a03030;
}
.empty {
  color: var(--text-2);
  padding: 30px 0;
}
.error {
  color: #a03030;
}
</style>
