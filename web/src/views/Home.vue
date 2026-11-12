<template>
  <div class="page-shell">
    <div class="page-head">
      <h1 class="page-title">概览</h1>
      <el-dropdown class="no-print" trigger="click">
        <button type="button" class="icon-action" aria-label="操作">
          <el-icon><MoreFilled /></el-icon>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="printPage">打印</el-dropdown-item>
            <el-dropdown-item @click="exportChart">导出图片</el-dropdown-item>
            <el-dropdown-item @click="load(false)">刷新</el-dropdown-item>
            <el-dropdown-item v-for="(card, index) in cards" :key="card.key" :divided="index === 0" @click="toggleCard(card.key)">
              {{ hiddenCards.includes(card.key) ? '显示' : '隐藏' }}{{ card.label }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <template v-if="loading">
      <div class="cards" aria-hidden="true">
        <div v-for="index in 4" :key="index" class="panel-card stat skeleton"></div>
      </div>
      <div class="panel-card chart-skeleton skeleton" aria-hidden="true"></div>
    </template>
    <div v-else-if="loadError" class="panel-card empty-block">
      <p>{{ loadError }}</p>
      <el-button type="primary" @click="load(true)">重试</el-button>
    </div>
    <template v-else>
      <div class="cards">
        <button
          v-for="card in visibleCards"
          :key="card.key"
          type="button"
          draggable="true"
          :class="['panel-card', 'stat', { 'is-feature': card.feature }]"
          @click="openCard(card)"
          @dragstart="onDragStart(card.key, $event)"
          @dragover.prevent
          @drop="onDrop(card.key)"
        >
          <span :class="['stat-icon', card.tone]">
            <el-icon><component :is="card.icon" /></el-icon>
          </span>
          <span class="label">{{ card.label }}</span>
          <span class="figure">
            <strong class="num">{{ card.value }}</strong>
            <span class="unit">{{ card.unit }}</span>
          </span>
          <span v-if="card.hint" :class="['status-pill', card.tone]">{{ card.hint }}</span>
        </button>
      </div>
      <section class="panel-card chart-card">
        <header class="chart-head">
          <div>
            <h2>登录趋势</h2>
            <span v-if="delta" :class="['status-pill', delta.tone]">{{ delta.text }}</span>
          </div>
          <el-segmented v-model="range" class="no-print" :options="ranges" size="small" @change="load(false)" />
        </header>
        <div class="chart-wrap">
          <div v-if="!chartLoading && !trend.length" class="chart-empty">
            <p>暂无登录记录</p>
          </div>
          <div v-show="trend.length" ref="chartHost" class="chart"></div>
          <div v-if="chartLoading" class="chart-mask skeleton"></div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, markRaw, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Document, FolderOpened, MoreFilled, Stamp, User } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import http from '@/api/http'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const appStore = useAppStore()
const summary = ref({})
const chartHost = ref()
const loading = ref(true)
const chartLoading = ref(false)
const loadError = ref('')
const range = ref(7)
const ranges = [
  { label: '今日', value: 1 },
  { label: '近 7 天', value: 7 },
  { label: '近 30 天', value: 30 },
]
let chart

const trend = computed(() => summary.value.login_trend || [])

const cards = computed(() => {
  const pending = summary.value.pending
  return [
    { key: 'users', label: '启用用户', value: summary.value.users ?? '—', unit: '人', icon: markRaw(User), to: '/users', tone: 'is-info' },
    { key: 'notes', label: '笔记', value: summary.value.notes ?? '—', unit: '条', icon: markRaw(Document), to: '/notes', tone: 'is-info' },
    { key: 'files', label: '文件', value: summary.value.files ?? '—', unit: '个', icon: markRaw(FolderOpened), to: '/files', tone: 'is-info' },
    {
      key: 'pending',
      label: '待审批',
      value: pending ?? '—',
      unit: '单',
      icon: markRaw(Stamp),
      to: '/approvals',
      feature: Number(pending) > 0,
      tone: pending > 0 ? 'is-warning' : 'is-muted',
      hint: pending > 0 ? '待处理' : '暂无待办',
    },
  ]
})

function readList(name, fallback) {
  try {
    const parsed = JSON.parse(localStorage.getItem(name) || '')
    return Array.isArray(parsed) ? parsed : fallback
  } catch {
    return fallback
  }
}

const cardOrder = ref(readList('dash-order', ['users', 'notes', 'files', 'pending']))
const hiddenCards = ref(readList('dash-hidden', []))
const dragKey = ref('')
const skipClick = ref(false)
const visibleCards = computed(() => {
  const list = cards.value.filter((card) => !hiddenCards.value.includes(card.key))
  return [...list].sort((left, right) => {
    const leftIndex = cardOrder.value.indexOf(left.key)
    const rightIndex = cardOrder.value.indexOf(right.key)
    return (leftIndex < 0 ? 99 : leftIndex) - (rightIndex < 0 ? 99 : rightIndex)
  })
})

const delta = computed(() => {
  if (trend.value.length < 2) return null
  const diff = trend.value[trend.value.length - 1].count - trend.value[trend.value.length - 2].count
  if (diff > 0) return { tone: 'is-success', text: `较上一日上升 ${diff}` }
  if (diff < 0) return { tone: 'is-danger', text: `较上一日下降 ${Math.abs(diff)}` }
  return { tone: 'is-muted', text: '较上一日持平' }
})

function readColor(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

function hexToRgb(hex) {
  const value = Number.parseInt(hex.replace('#', ''), 16)
  return { r: (value >> 16) & 255, g: (value >> 8) & 255, b: value & 255 }
}

function renderChart() {
  if (!trend.value.length || !chartHost.value) return
  if (!chart) chart = echarts.init(chartHost.value)
  const points = trend.value
  const primary = readColor('--app-primary') || '#146860'
  const rgb = hexToRgb(primary)
  const area = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.08)`
  chart.setOption({
    grid: { left: 36, right: 16, top: 24, bottom: 28 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: readColor('--app-surface') || '#fff',
      borderColor: readColor('--app-border-light') || '#e7eeeb',
      borderWidth: 1,
      textStyle: { color: readColor('--app-text') || '#1c2b27', fontSize: 12 },
      extraCssText: 'border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.08);padding:8px 12px;',
      formatter(params) {
        const point = params[0]
        return `${point.axisValue}<br/>登录 ${point.data}`
      },
    },
    xAxis: {
      type: 'category',
      data: points.map((item) => item.day.slice(5)),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: readColor('--chart-label'), fontSize: 12 },
      axisPointer: { lineStyle: { color: primary, width: 1 } },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: readColor('--chart-label'), fontSize: 12 },
      splitLine: { lineStyle: { color: readColor('--chart-grid'), width: 1 } },
    },
    series: [{
      type: 'line',
      data: points.map((item) => item.count),
      smooth: true,
      showSymbol: false,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: { width: 2, color: primary, cap: 'round' },
      itemStyle: { color: primary, borderColor: readColor('--app-surface') || '#fff', borderWidth: 2 },
      emphasis: { focus: 'series', scale: 1.2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: area },
          { offset: 1, color: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.01)` },
        ]),
      },
    }],
  }, true)
  chart.resize()
}

async function load(initial = false) {
  if (initial) loading.value = true
  else chartLoading.value = true
  loadError.value = ''
  try {
    summary.value = await http.get('/dashboard', { params: { days: range.value } })
  } catch (error) {
    loadError.value = error.displayMessage || '概览暂时无法加载'
  } finally {
    loading.value = false
    chartLoading.value = false
  }
  await nextTick()
  if (!loadError.value) renderChart()
}

function printPage() { window.print() }
function exportChart() {
  if (!chart) return
  const link = document.createElement('a')
  link.href = chart.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#ffffff' })
  link.download = '登录趋势.png'
  link.click()
}
function openCard(card) {
  if (skipClick.value) {
    skipClick.value = false
    return
  }
  router.push(card.to)
}
function onDragStart(key, event) {
  dragKey.value = key
  event.dataTransfer.effectAllowed = 'move'
}
function onDrop(target) {
  skipClick.value = true
  const keys = visibleCards.value.map((card) => card.key)
  const from = keys.indexOf(dragKey.value)
  const to = keys.indexOf(target)
  if (from < 0 || to < 0 || from === to) return
  const [moved] = keys.splice(from, 1)
  keys.splice(to, 0, moved)
  cardOrder.value = [...keys, ...cardOrder.value.filter((key) => !keys.includes(key))]
  localStorage.setItem('dash-order', JSON.stringify(cardOrder.value))
}
function toggleCard(key) {
  const next = hiddenCards.value.includes(key)
    ? hiddenCards.value.filter((item) => item !== key)
    : [...hiddenCards.value, key]
  if (next.length >= cards.value.length) return
  hiddenCards.value = next
  localStorage.setItem('dash-hidden', JSON.stringify(next))
}
function onResize() { chart?.resize() }

watch(() => [appStore.theme, appStore.primary], () => nextTick(renderChart))

onMounted(() => {
  window.addEventListener('resize', onResize)
  load(true)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.cards { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }

.stat {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  min-height: 136px;
  padding: var(--card-padding);
  text-align: left;
  color: inherit;
  cursor: pointer;
  transition: transform 0.22s ease-out, box-shadow 0.22s ease-out, border-color 0.22s ease-out;
}

.stat:hover { transform: translateY(-2px); box-shadow: var(--shadow-pop); }
.stat:focus-visible { outline: 2px solid var(--app-primary); outline-offset: 2px; }
.stat.is-feature {
  background: linear-gradient(135deg, var(--app-accent), var(--app-surface) 68%);
  border-color: transparent;
}
.stat.skeleton { min-height: 136px; cursor: default; }

.stat-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: var(--app-primary-soft);
  color: var(--app-primary);
  font-size: 16px;
}

.stat-icon.is-warning { background: var(--color-warning-soft); color: var(--color-warning); }
.stat-icon.is-muted { background: var(--app-surface-muted); color: var(--app-muted); }

.label { color: var(--app-muted); font-size: var(--text-caption); }
.figure { display: flex; align-items: baseline; gap: 4px; }
.figure { gap: 8px; }
.figure strong { font-size: 32px; font-weight: 650; line-height: 1.1; }
.unit { color: var(--app-faint); font-size: 12px; font-weight: 400; }

.chart-card { padding: 16px 16px 8px; }
.chart-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 32px; }
.chart-head h2 { margin: 0; font-size: var(--text-subtitle); font-weight: 500; }
.chart-head > div { display: flex; align-items: center; gap: 8px; }
.chart-wrap { position: relative; }
.chart { height: 280px; }
.chart-mask { position: absolute; inset: 0; border-radius: var(--radius-sm); }
.chart-skeleton { height: 320px; }
.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 280px;
  color: var(--app-muted);
}
.chart-empty p { margin: 0; }
.icon-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--app-text);
  cursor: pointer;
  transition: background-color 0.22s ease-out;
}
.icon-action:hover { background: var(--app-surface-muted); }
.icon-action:focus-visible { outline: 2px solid var(--app-primary); outline-offset: 2px; }
.empty-block { display: flex; flex-direction: column; align-items: flex-start; gap: 12px; padding: 24px; }
.empty-block p { margin: 0; color: var(--app-muted); }

@media (max-width: 1100px) {
  .cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 640px) {
  .cards { grid-template-columns: 1fr; }
  .chart-head { align-items: flex-start; flex-direction: column; }
}
</style>
