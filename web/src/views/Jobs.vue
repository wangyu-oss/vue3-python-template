<template>
  <div class="page-shell">
    <div class="page-head">
      <h1 class="page-title">定时任务</h1>
      <el-button type="primary" @click="openCreate">新建</el-button>
    </div>
    <div class="panel-card table-wrap">
      <el-table :data="items" max-height="calc(100vh - 220px)">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="cron" label="Cron" />
        <el-table-column prop="handler" label="处理函数" />
        <el-table-column prop="enabled" label="启用">
          <template #default="{ row }">
            <span class="status-pill" :class="row.enabled ? 'is-success' : 'is-muted'">{{ row.enabled ? '启用' : '暂停' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_status" label="结果">
          <template #default="{ row }">
            <span v-if="row.last_status" class="status-pill" :class="statusTone(row.last_status)">{{ statusLabel(row.last_status) }}</span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_message" label="说明" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button link type="primary" @click="run(row)">执行</el-button>
            <el-button link @click="toggle(row)">{{ row.enabled ? '暂停' : '启用' }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <el-dialog v-model="open" title="任务" width="420px">
      <el-form label-position="top">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="Cron"><el-input v-model="form.cron" /></el-form-item>
        <el-form-item label="处理函数">
          <el-select v-model="form.handler"><el-option label="巡检" value="ping" /><el-option label="清理日志" value="cleanup_logs" /></el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="open = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'

const items = ref([])

function statusTone(value) {
  const text = String(value || '').toLowerCase()
  if (['success', 'ok', 'done'].includes(text)) return 'is-success'
  if (['failed', 'error'].includes(text)) return 'is-danger'
  if (['running', 'pending'].includes(text)) return 'is-warning'
  return 'is-info'
}

function statusLabel(value) {
  const map = { success: '成功', ok: '成功', failed: '失败', error: '失败', running: '执行中', pending: '等待' }
  return map[String(value).toLowerCase()] || value
}
const open = ref(false)
const form = reactive({ name: '', cron: '0 * * * *', handler: 'ping', enabled: true })

async function load() {
  items.value = (await http.get('/jobs')).items || []
}
function openCreate() { open.value = true }
async function save() {
  await http.post('/jobs/save', { ...form })
  open.value = false
  await load()
}
async function run(row) {
  const result = await http.post('/jobs/run', { id: row.id })
  ElMessage.success(result.item.last_message || '已执行')
  await load()
}
async function toggle(row) {
  await http.post('/jobs/save', { ...row, enabled: !row.enabled })
  await load()
}
onMounted(load)
</script>

<style scoped>
.page-shell { display: flex; flex-direction: column; gap: 12px; }
</style>
