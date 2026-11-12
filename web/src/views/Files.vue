<template>
  <div class="page-shell">
    <div class="page-head">
      <h1 class="page-title">{{ title }}</h1>
      <el-upload :show-file-list="false" :http-request="upload">
        <el-button type="primary">上传</el-button>
      </el-upload>
    </div>
    <div class="panel-card table-wrap">
      <el-table :data="items" max-height="calc(100vh - 220px)">
        <el-table-column prop="name" label="文件" min-width="180" />
        <el-table-column prop="size" label="大小" width="100" />
        <el-table-column prop="content_type" label="类型" width="160" />
        <el-table-column prop="uploader_name" label="上传人" width="120" />
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button link type="primary" @click="preview(row)">预览</el-button>
            <el-button link @click="rename(row)">重命名</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <el-dialog v-model="previewOpen" title="预览" width="640px">
      <img v-if="previewType.startsWith('image/')" :src="previewUrl" alt="" class="preview" />
      <iframe v-else-if="previewType.includes('pdf')" :src="previewUrl" class="preview" />
      <p v-else>该文件请下载后查看。</p>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import http, { readToken } from '@/api/http'

const route = useRoute()
const title = route.meta.title
const items = ref([])
const previewOpen = ref(false)
const previewUrl = ref('')
const previewType = ref('')

async function load() {
  const result = await http.get('/files', { params: { page: 1, page_size: 100 } })
  items.value = result.items || []
}

async function upload(option) {
  const data = new FormData()
  data.append('file', option.file)
  await http.post('/files/upload', data)
  ElMessage.success('已上传')
  await load()
}

function preview(row) {
  previewType.value = row.content_type || ''
  previewUrl.value = `/api/v1/files/${row.id}/raw?token=${readToken()}`
  previewOpen.value = true
}

async function rename(row) {
  const result = await ElMessageBox.prompt('文件名', '重命名', { inputValue: row.name })
  await http.post('/files/rename', { id: row.id, name: result.value })
  await load()
}

async function remove(row) {
  await ElMessageBox.confirm(`删除 ${row.name}？`, '删除')
  await http.post('/files/delete', { ids: [row.id] })
  await load()
}

onMounted(load)
</script>

<style scoped>
.page-shell { display: flex; flex-direction: column; gap: 12px; }
.preview { width: 100%; max-height: 420px; border: 0; }
</style>
