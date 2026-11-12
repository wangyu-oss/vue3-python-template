<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <h1 class="page-title">笔记</h1>
      </div>
      <el-button type="primary" @click="openCreate">新建</el-button>
    </div>
    <div class="panel-card table-wrap">
      <el-table :data="items" max-height="calc(100vh - 220px)" empty-text="暂无数据">
        <el-table-column prop="title" label="标题" min-width="160" />
        <el-table-column prop="content" label="内容" min-width="240" show-overflow-tooltip />
        <el-table-column label="更新时间" width="170">
          <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="148" align="right">
          <template #default="{ row }">
            <div class="row-ops">
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button link type="danger" @click="remove(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogOpen" :title="form.id ? '编辑笔记' : '新建笔记'" width="480px">
      <el-form label-position="top">
        <el-form-item label="标题">
          <el-input v-model="form.title" maxlength="120" show-word-limit />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="5" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogOpen = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'
import { formatDateTime } from '@/utils/datetime'

defineOptions({ name: 'Notes' })

const items = ref([])
const dialogOpen = ref(false)
const saving = ref(false)
const form = reactive({ id: null, title: '', content: '' })

function formatTime(value) {
  return formatDateTime(value) || ''
}

async function load() {
  const result = await http.get('/notes')
  items.value = result.items || []
}

function openCreate() {
  form.id = null
  form.title = ''
  form.content = ''
  dialogOpen.value = true
}

function openEdit(row) {
  form.id = row.id
  form.title = row.title
  form.content = row.content
  dialogOpen.value = true
}

async function save() {
  if (!form.title.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  saving.value = true
  try {
    await http.post('/notes/save', {
      id: form.id,
      title: form.title.trim(),
      content: form.content,
    })
    dialogOpen.value = false
    await load()
    ElMessage.success('已保存')
  } catch (error) {
    ElMessage.error(error.displayMessage || '保存失败')
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`删除「${row.title}」？`, '删除笔记', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await http.post('/notes/delete', { id: row.id })
    await load()
    ElMessage.success('已删除')
  } catch (error) {
    ElMessage.error(error.displayMessage || '删除失败')
  }
}

onMounted(async () => {
  try {
    await load()
  } catch (error) {
    ElMessage.error(error.displayMessage || '读取笔记失败')
  }
})
</script>

<style scoped>
.page-shell { display: flex; flex-direction: column; gap: 12px; }
</style>
