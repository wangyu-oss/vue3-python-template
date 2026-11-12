<template>
  <div class="page-shell">
    <div class="page-head">
      <h1 class="page-title">消息</h1>
      <el-button @click="readAll">全部已读</el-button>
    </div>
    <div class="panel-card list">
      <article v-for="item in items" :key="item.id" :class="{ unread: !item.is_read }" @click="readOne(item)">
        <strong>{{ item.title }}</strong>
        <p>{{ item.content }}</p>
      </article>
      <el-empty v-if="!items.length" description="暂无数据" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'

const items = ref([])

async function load() {
  const result = await http.get('/messages', { params: { page: 1, page_size: 50 } })
  items.value = result.items || []
}

async function readOne(item) {
  await http.post('/messages/read', { ids: [item.id] })
  item.is_read = true
}

async function readAll() {
  await http.post('/messages/read', {})
  items.value.forEach((item) => { item.is_read = true })
}

onMounted(load)
</script>

<style scoped>
.page-shell { display: flex; flex-direction: column; gap: 12px; }
.list { padding: 8px 16px; overflow: auto; }
article { padding: 12px 0; border-bottom: 1px solid var(--app-border-light); cursor: pointer; }
.unread strong { color: var(--app-primary); }
p { margin: 4px 0 0; color: var(--app-muted); }
</style>
