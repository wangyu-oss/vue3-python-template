<template>
  <div class="page-shell">
    <div class="page-head">
      <h1 class="page-title">{{ title }}</h1>
      <div class="tools">
        <el-input v-model="keyword" clearable @input="load" />
        <el-button @click="keyword = ''; load()">重置</el-button>
        <el-button v-if="userStore.can('log:export')" @click="download">导出</el-button>
      </div>
    </div>
    <div class="panel-card table-wrap">
      <el-table :data="items" max-height="calc(100vh - 220px)">
        <el-table-column v-for="column in columns" :key="column" :prop="column" :label="labels[column] || column" :formatter="formatColumn" min-width="120" show-overflow-tooltip />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import http, { readToken } from '@/api/http'
import { formatDateTime } from '@/utils/datetime'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()
const pagePath = route.path
const items = ref([])
const keyword = ref('')
const labels = {
  id: '编号',
  username: '用户名',
  ip: '地址',
  user_agent: '设备',
  success: '结果',
  message: '说明',
  created_at: '时间',
  action: '动作',
  target: '对象',
  detail: '详情',
  trace_id: '追踪号',
  method: '方法',
  path: '路径',
  status_code: '状态',
  duration_ms: '耗时',
}
const kind = pagePath.split('/').filter(Boolean).pop()
const title = route.meta.title || ''
const columns = computed(() => Object.keys(items.value[0] || { id: '' }))

function formatColumn(_row, _column, value) {
  return formatDateTime(value)
}

async function load() {
  if (route.path !== pagePath || !kind || !['login', 'operation', 'api'].includes(kind)) return
  const result = await http.get(`/logs/${kind}`, { params: { keyword: keyword.value, page: 1, page_size: 50 }, cancelPrevious: true })
  items.value = result.items || []
}

function download() {
  window.open(`/api/v1/logs/export?kind=${kind}&token=${readToken()}`)
}

watch(() => route.path, (path) => {
  if (path === pagePath) load()
})
onMounted(load)
</script>

<style scoped>
.page-shell { display: flex; flex-direction: column; gap: 12px; }
</style>
