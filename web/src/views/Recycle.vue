<template>
  <div class="page-shell">
    <div class="page-head"><h1 class="page-title">回收站</h1></div>
    <div class="panel-card table-wrap">
      <el-table :data="items" max-height="calc(100vh - 220px)">
        <el-table-column prop="title" label="记录" />
        <el-table-column prop="model_name" label="类型" />
        <el-table-column prop="deleted_by" label="操作人" />
        <el-table-column prop="created_at" label="时间" :formatter="formatColumn" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" @click="restore(row)">恢复</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'
import { formatDateTime } from '@/utils/datetime'

const items = ref([])

function formatColumn(_row, _column, value) {
  return formatDateTime(value)
}
async function load() { items.value = (await http.get('/recycle')).items || [] }
async function restore(row) {
  await http.post('/recycle/restore', { id: row.id })
  ElMessage.success('已恢复')
  await load()
}
onMounted(load)
</script>

<style scoped>
.page-shell { display: flex; flex-direction: column; gap: 12px; }
</style>
