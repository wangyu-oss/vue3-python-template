<template>
  <div class="page-shell">
    <div class="page-head">
      <h1 class="page-title">系统设置</h1>
      <el-button type="primary" :loading="saving" @click="save">保存</el-button>
    </div>
    <div class="grid">
      <section class="panel-card block">
        <el-form label-position="top">
          <el-form-item v-for="item in items" :key="item.key" :label="item.key">
            <el-input v-model="item.value" />
          </el-form-item>
        </el-form>
      </section>
      <section class="panel-card block">
        <h2>功能开关</h2>
        <div v-for="flag in flags" :key="flag.id" class="flag">
          <span>{{ flag.name }}</span>
          <el-switch v-model="flag.enabled" />
        </div>
        <el-button @click="runBackup">备份数据库</el-button>
        <p v-if="backupFile" class="muted">{{ backupFile }}</p>
        <div ref="qrHost" class="qr"></div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import QRCode from 'qrcode'
import http from '@/api/http'

const items = ref([])
const flags = ref([])
const saving = ref(false)
const backupFile = ref('')
const qrHost = ref()

async function load() {
  const result = await http.get('/settings')
  items.value = result.items || []
  flags.value = result.flags || []
  await nextTick()
  if (qrHost.value) {
    qrHost.value.innerHTML = ''
    const canvas = document.createElement('canvas')
    await QRCode.toCanvas(canvas, location.origin)
    qrHost.value.appendChild(canvas)
  }
}

async function save() {
  saving.value = true
  try {
    const settings = Object.fromEntries(items.value.map((item) => [item.key, item.value]))
    await http.post('/settings/save', { settings, flags: flags.value })
    ElMessage.success('已保存')
  } finally {
    saving.value = false
  }
}

async function runBackup() {
  const result = await http.post('/backup')
  backupFile.value = result.file
  ElMessage.success('备份已生成')
}

onMounted(load)
</script>

<style scoped>
.page-shell { display: flex; flex-direction: column; gap: 12px; overflow: auto; }
.grid { display: grid; grid-template-columns: minmax(280px, 1fr) 320px; gap: 12px; }
.block { padding: 16px; }
.flag { display: flex; justify-content: space-between; margin-bottom: 10px; }
.qr { margin-top: 16px; }
</style>
