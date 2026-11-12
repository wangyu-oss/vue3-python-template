<template>
  <div class="page-shell">
    <div class="page-head"><h1 class="page-title">在线用户</h1></div>
    <div class="panel-card table-wrap">
      <el-table :data="items" max-height="calc(100vh - 220px)">
        <el-table-column prop="display_name" label="用户" />
        <el-table-column prop="ip" label="地址" />
        <el-table-column prop="user_agent" label="设备" show-overflow-tooltip />
        <el-table-column prop="created_at" label="登录时间" :formatter="formatColumn" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="danger" @click="kick(row)">下线</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
import { formatDateTime } from '@/utils/datetime'

const items = ref([])

function formatColumn(_row, _column, value) {
  return formatDateTime(value)
}
async function load() { items.value = (await http.get('/online')).items || [] }
async function kick(row) { await http.post('/online/kick', { ids: [row.id] }); await load() }
onMounted(load)
</script>

<style scoped>
.page-shell { display: flex; flex-direction: column; gap: 12px; }
</style>
