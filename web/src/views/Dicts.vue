<template>
  <div class="page-shell">
    <div class="page-head">
      <h1 class="page-title">字典</h1>
      <el-button type="primary" @click="openType">新建分组</el-button>
    </div>
    <div class="split">
      <section class="panel-card">
        <el-table :data="types" max-height="calc(100vh - 220px)" highlight-current-row @current-change="current = $event">
          <el-table-column prop="name" label="分组" />
          <el-table-column prop="code" label="编码" />
        </el-table>
      </section>
      <section class="panel-card">
        <div class="page-head">
          <strong>{{ current?.name || '字典项' }}</strong>
          <el-button :disabled="!current" @click="openItem">新建字典项</el-button>
        </div>
        <el-table :data="currentItems">
          <el-table-column prop="label" label="名称" />
          <el-table-column prop="value" label="值" />
          <el-table-column prop="is_active" label="启用" />
        </el-table>
      </section>
    </div>
    <el-dialog v-model="open" :title="mode === 'item' ? '字典项' : '分组'" width="420px">
      <el-form label-position="top">
        <el-form-item v-if="mode === 'type'" label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item v-if="mode === 'type'" label="编码"><el-input v-model="form.code" /></el-form-item>
        <el-form-item v-if="mode === 'item'" label="名称"><el-input v-model="form.label" /></el-form-item>
        <el-form-item v-if="mode === 'item'" label="值"><el-input v-model="form.value" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="open = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import http from '@/api/http'

const types = ref([])
const items = ref([])
const current = ref(null)
const open = ref(false)
const mode = ref('type')
const form = reactive({})
const currentItems = computed(() => items.value.filter((item) => item.dict_type_id === current.value?.id))

async function load() {
  const result = await http.get('/dicts')
  types.value = result.types || []
  items.value = result.items || []
  current.value = current.value || types.value[0] || null
}

function openType() {
  mode.value = 'type'
  Object.assign(form, { name: '', code: '' })
  open.value = true
}

function openItem() {
  mode.value = 'item'
  Object.assign(form, { label: '', value: '', dict_type_id: current.value.id, is_active: true })
  open.value = true
}

async function save() {
  await http.post('/dicts/save', { ...form, kind: mode.value })
  open.value = false
  await load()
}

onMounted(load)
</script>

<style scoped>
.page-shell, .split { min-height: 0; }
.page-shell { display: flex; flex-direction: column; gap: 12px; height: 100%; }
.split { flex: 1; display: grid; grid-template-columns: 280px 1fr; gap: 12px; }
.panel-card { padding: 8px; overflow: auto; }
</style>
