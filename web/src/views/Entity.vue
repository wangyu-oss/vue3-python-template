<template>
  <div class="page-shell" v-loading="loading">
    <div class="page-head">
      <h1 class="page-title">{{ title }}</h1>
      <div class="tools">
        <el-input v-if="config.keyword" v-model="keyword" clearable placeholder="关键字" @input="onSearch" />
        <button v-if="keyword" type="button" class="filter-chip" @click="reset">关键字 {{ keyword }} <span aria-hidden="true">×</span></button>
        <el-button v-if="config.keyword" @click="reset">{{ t('reset') }}</el-button>
        <el-button v-if="canCreate" type="primary" @click="openCreate">{{ t('create') }}</el-button>
        <el-button v-if="config.batchStatus && userStore.can('user:update')" @click="setStatus('active')">{{ t('enable') }}</el-button>
        <el-button v-if="config.batchStatus && userStore.can('user:update')" @click="setStatus('disabled')">{{ t('disable') }}</el-button>
        <el-button v-if="canDelete" type="danger" plain @click="removeSelected">{{ t('delete') }}</el-button>
        <el-button v-if="config.next" @click="takeNumber">取号</el-button>
      </div>
    </div>
    <div class="panel-card table-wrap">
      <el-table :data="items" max-height="calc(100vh - 230px)" @selection-change="selected = $event" @sort-change="onSort">
        <el-table-column v-if="config.selection" type="selection" width="46" />
        <el-table-column
          v-for="column in config.columns"
          :key="column.prop"
          :prop="column.prop"
          :label="column.label"
          :sortable="column.sort ? 'custom' : false"
          :formatter="formatColumn"
          min-width="120"
          show-overflow-tooltip
        >
          <template v-if="isTag(column.prop) || column.prop === 'data_scope'" #default="{ row }">
            <span v-if="column.prop === 'data_scope'">{{ scopeText(row.data_scope) }}</span>
            <span v-else class="status-pill" :class="pillTone(column.prop, row[column.prop])">{{ pillText(column.prop, row[column.prop]) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="148" align="right">
          <template #default="{ row }">
            <div class="row-ops">
            <el-button link type="primary" @click="openEdit(row)">{{ t('edit') }}</el-button>
            <el-dropdown trigger="click">
              <el-button link>更多</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-for="action in config.actions || []" :key="action.key" @click="runAction(row, action.key)">
                    {{ action.label }}
                  </el-dropdown-item>
                  <el-dropdown-item @click="copyText(String(row.id))">复制编号</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        class="pager"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        @current-change="load"
        @size-change="load"
      />
    </div>
    <el-dialog v-model="open" :title="form.id ? t('edit') : t('create')" width="520px">
      <el-form label-position="top">
        <el-form-item v-for="field in visibleFields" :key="field.prop" :label="field.label" :required="field.required" :error="fieldErrors[field.prop]">
          <el-input v-if="!field.type || field.type === 'text'" v-model="form[field.prop]" />
          <el-input v-else-if="field.type === 'textarea'" v-model="form[field.prop]" type="textarea" :rows="4" />
          <el-input-number v-else-if="field.type === 'number'" v-model="form[field.prop]" />
          <el-switch v-else-if="field.type === 'switch'" v-model="form[field.prop]" />
          <el-select v-else-if="field.type === 'select'" v-model="form[field.prop]" clearable :multiple="field.multiple" style="width: 100%">
            <el-option v-for="option in optionsOf(field)" :key="option.value" :label="option.label" :value="option.value" />
          </el-select>
          <el-tree
            v-else-if="field.type === 'menus'"
            ref="menuTree"
            node-key="id"
            show-checkbox
            default-expand-all
            :data="menuTree"
            :props="{ label: 'name', children: 'children' }"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="open = false">{{ t('cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="save">{{ t('save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'
import { formatDateTime } from '@/utils/datetime'
import { entities } from '@/config/entities'
import { useUserStore } from '@/stores/user'

defineOptions({ name: 'Entity' })

const route = useRoute()
const pagePath = route.path
const pageTitle = route.meta.title || ''
const pageTitleEn = route.meta.titleEn || pageTitle
const { t, locale } = useI18n()
const userStore = useUserStore()
const config = computed(() => entities[pagePath] || { columns: [], fields: [] })
const title = computed(() => (locale.value === 'en' ? pageTitleEn : pageTitle) || pagePath)
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref(localStorage.getItem(`keyword:${pagePath}`) || '')
const ordering = ref('')
const selected = ref([])
const loading = ref(false)
const saving = ref(false)
const open = ref(false)
const form = reactive({})
const fieldErrors = reactive({})
const tagProps = new Set(['status', 'is_active', 'done'])
const sources = ref({})
const menuTree = ref()
const menus = ref([])
let timer = 0

const visibleFields = computed(() => config.value.fields.filter((field) => !field.createOnly || !form.id))
const canCreate = computed(() => userStore.can(config.value.createPermission))
const canDelete = computed(() => userStore.can(config.value.deletePermission || config.value.createPermission))

function optionsOf(field) {
  if (field.options) return field.options
  return sources.value[field.source] || []
}

function buildTree(rows) {
  const map = {}
  rows.forEach((row) => { map[row.id] = { ...row, children: [] } })
  const roots = []
  rows.forEach((row) => {
    if (row.parent_id && map[row.parent_id]) map[row.parent_id].children.push(map[row.id])
    else roots.push(map[row.id])
  })
  return roots
}

async function loadSources() {
  const needed = [...new Set(config.value.fields.map((field) => field.source).filter(Boolean))]
  if (config.value.fields.some((field) => field.type === 'menus')) needed.push('/menus')
  await Promise.all(needed.map(async (source) => {
    const result = await http.get(source, { params: { page: 1, page_size: 200 } })
    const rows = result.items || []
    if (source === '/menus') menus.value = rows
    sources.value[source] = rows.map((row) => ({ label: row.name || row.username || row.title, value: row.id }))
  }))
}

async function load() {
  loading.value = true
  try {
    const result = await http.get(pagePath, {
      params: { page: page.value, page_size: pageSize.value, keyword: keyword.value, ordering: ordering.value },
      cancelPrevious: true,
    })
    items.value = result.items || []
    total.value = result.total || items.value.length
  } catch (error) {
    if (error.code !== 'ERR_CANCELED') ElMessage.error(error.displayMessage || '读取失败')
  } finally {
    loading.value = false
  }
}

function onSearch() {
  localStorage.setItem(`keyword:${pagePath}`, keyword.value)
  clearTimeout(timer)
  timer = setTimeout(() => { page.value = 1; load() }, 300)
}

function reset() {
  keyword.value = ''
  ordering.value = ''
  localStorage.removeItem(`keyword:${pagePath}`)
  page.value = 1
  load()
}

function onSort({ prop, order }) {
  const column = config.value.columns.find((item) => item.prop === prop)
  ordering.value = !order || !column?.sort ? '' : `${order === 'descending' ? '-' : ''}${column.sort}`
  load()
}

function isTag(prop) { return tagProps.has(prop) }

function formatColumn(_row, _column, value) {
  return formatDateTime(value)
}

function scopeText(value) {
  return { all: '全部', dept: '本部门', self: '本人' }[value] || String(value ?? '—')
}

function pillText(prop, value) {
  if (prop === 'status') {
    return {
      active: '启用',
      disabled: '停用',
      pending: '待处理',
      approved: '已同意',
      rejected: '已驳回',
      withdrawn: '已撤回',
    }[value] || String(value ?? '—')
  }
  if (value === true || value === 1) return prop === 'done' ? '已完成' : '启用'
  return prop === 'done' ? '未完成' : '停用'
}

function pillTone(prop, value) {
  if (prop === 'status') {
    if (value === 'active' || value === 'approved') return 'is-success'
    if (value === 'pending') return 'is-warning'
    if (value === 'rejected') return 'is-danger'
    return 'is-muted'
  }
  return value === true || value === 1 ? 'is-success' : 'is-muted'
}

function openCreate() {
  Object.keys(form).forEach((key) => delete form[key])
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key])
  const memory = JSON.parse(localStorage.getItem(`form:${pagePath}`) || '{}')
  Object.assign(form, memory, { id: null })
  open.value = true
}

function openEdit(row) {
  Object.keys(form).forEach((key) => delete form[key])
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key])
  Object.assign(form, row)
  open.value = true
  nextTick(() => {
    const tree = Array.isArray(menuTree.value) ? menuTree.value[0] : menuTree.value
    tree?.setCheckedKeys?.(row.menu_ids || [])
  })
}

async function save() {
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key])
  for (const field of visibleFields.value) {
    if (field.required && !form[field.prop]) fieldErrors[field.prop] = `请填写${field.label}`
  }
  if (Object.keys(fieldErrors).length) return
  if (config.value.fields.some((field) => field.type === 'menus')) {
    const tree = Array.isArray(menuTree.value) ? menuTree.value[0] : menuTree.value
    form.menu_ids = tree?.getCheckedKeys?.() || form.menu_ids || []
  }
  saving.value = true
  try {
    await http.post(`${pagePath}/save`, { ...form }, { idempotent: true })
    localStorage.setItem(`form:${pagePath}`, JSON.stringify(form))
    open.value = false
    ElMessage.success('已保存')
    await load()
  } catch (error) {
    ElMessage.error(error.displayMessage || '保存失败')
  } finally {
    saving.value = false
  }
}

async function removeSelected() {
  const ids = selected.value.map((row) => row.id)
  if (!ids.length) return
  try {
    await ElMessageBox.confirm(t('confirmDelete'), t('delete'), { type: 'warning' })
  } catch {
    return
  }
  await http.post(`${pagePath}/delete`, { ids })
  ElMessage.success('已删除')
  await load()
}

async function setStatus(status) {
  const ids = selected.value.map((row) => row.id)
  if (!ids.length) return
  await http.post(`${pagePath}/status`, { ids, status })
  await load()
}

async function runAction(row, action) {
  let opinion = ''
  if (action === 'reject') {
    try {
      const result = await ElMessageBox.prompt('驳回意见', '驳回')
      opinion = result.value
    } catch {
      return
    }
  }
  await http.post(`${pagePath}/act`, { id: row.id, action, opinion })
  await load()
}

async function takeNumber() {
  const code = items.value[0]?.code
  if (!code) return
  const result = await http.post(`${pagePath}/next`, { code })
  ElMessage.success(result.number)
  await load()
}

async function copyText(text) {
  await navigator.clipboard.writeText(text)
  ElMessage.success('已复制')
}

onMounted(async () => {
  await loadSources()
  await load()
})
</script>

<style scoped>
.page-shell { display: flex; flex-direction: column; gap: 16px; }
</style>
