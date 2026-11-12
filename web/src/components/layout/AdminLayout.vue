<template>
  <div :class="['admin-shell', `layout-${appStore.layout}`]">
    <div
      v-if="appStore.layout !== 'top' && !layoutStore.sidebarCollapsed"
      class="sidebar-mask"
      @click="layoutStore.toggleSidebar()"
    ></div>
    <aside v-if="appStore.layout !== 'top'" :class="['sidebar', { 'is-collapsed': layoutStore.sidebarCollapsed }]">
      <div class="brand">
        <BrandMark class="brand-logo" />
        <strong v-show="!layoutStore.sidebarCollapsed">管理系统</strong>
      </div>
      <div v-if="favorites.length && !layoutStore.sidebarCollapsed" class="fav-block">
        <p>收藏</p>
        <button
          v-for="item in favorites"
          :key="item.id"
          type="button"
          :class="{ on: route.path === item.path }"
          @click="router.push(item.path)"
        >{{ appStore.locale === 'en' ? item.name_en : item.name }}</button>
      </div>
      <el-menu
        :default-active="route.path"
        :collapse="layoutStore.sidebarCollapsed"
        :collapse-transition="false"
        router
      >
        <MenuNodes :items="sideMenus" :locale="appStore.locale" />
      </el-menu>
    </aside>
    <div class="main-col">
      <header class="topbar">
        <button type="button" class="icon-btn" aria-label="切换侧栏" @click="layoutStore.toggleSidebar()">
          <el-icon><Fold v-if="!layoutStore.sidebarCollapsed" /><Expand v-else /></el-icon>
        </button>
        <nav v-if="crumbs.length > 1" class="crumb-inline" aria-label="当前位置">
          <template v-for="(item, index) in crumbs" :key="item.path">
            <router-link v-if="index < crumbs.length - 1" :to="item.path">{{ item.title }}</router-link>
            <strong v-else>{{ item.title }}</strong>
          </template>
        </nav>
        <el-menu v-if="appStore.layout !== 'side'" mode="horizontal" :default-active="topActive" router class="top-menu">
          <el-menu-item v-for="item in topMenus" :key="item.id" :index="item.path || item.children?.[0]?.path || '/'">
            {{ appStore.locale === 'en' ? item.name_en : item.name }}
          </el-menu-item>
        </el-menu>
        <div class="tags-track">
          <button
            v-for="view in layoutStore.visitedViews"
            :key="view.path"
            type="button"
            draggable="true"
            :class="['tag', { active: view.path === route.path }]"
            @click="router.push(view.path)"
            @contextmenu.prevent="openTagMenu($event, view)"
            @dragstart="dragTag = view.path"
            @dragover.prevent
            @drop="layoutStore.moveView(dragTag, view.path)"
          >
            <span>{{ view.title }}</span>
            <em v-if="!view.affix" @click.stop="closeView(view)">×</em>
          </button>
        </div>
        <div class="tool-group">
        <button type="button" class="icon-btn" aria-label="搜索菜单" @click="openPalette"><el-icon><Search /></el-icon></button>
        <el-badge is-dot :hidden="!unread">
          <button type="button" class="icon-btn" :aria-label="unread ? `消息 ${unread}` : '消息'" @click="router.push('/messages')"><el-icon><Bell /></el-icon></button>
        </el-badge>
        <el-dropdown trigger="click">
          <button type="button" class="icon-btn" aria-label="界面设置"><el-icon><Operation /></el-icon></button>
          <template #dropdown>
            <div class="pref" @click.stop>
              <span>{{ t('primaryColor') }}</span>
              <div class="swatches">
                <button
                  v-for="color in presets"
                  :key="color"
                  type="button"
                  class="swatch"
                  :class="{ on: appStore.primary === color }"
                  :style="{ background: color }"
                  :aria-label="color"
                  @click="setPrimary(color)"
                ></button>
                <input class="swatch-input" type="color" :value="appStore.primary" aria-label="自定义主色" @input="setPrimary($event.target.value)" />
              </div>
              <span>{{ t('theme') }}</span>
              <el-segmented v-model="appStore.theme" :options="[{ label: t('light'), value: 'light' }, { label: t('dark'), value: 'dark' }, { label: t('care'), value: 'care' }]" @change="appStore.save()" />
              <span>{{ t('layout') }}</span>
              <el-segmented v-model="appStore.layout" :options="['side', 'top', 'mix']" @change="appStore.save()" />
              <span>{{ t('density') }}</span>
              <el-segmented v-model="appStore.density" :options="[{ label: t('compact'), value: 'compact' }, { label: t('comfortable'), value: 'comfortable' }, { label: t('roomy'), value: 'roomy' }]" @change="appStore.save()" />
              <span>{{ t('language') }}</span>
              <el-segmented v-model="appStore.locale" :options="[{ label: '中文', value: 'zh' }, { label: 'EN', value: 'en' }]" @change="changeLocale" />
              <span>{{ t('font') }} {{ appStore.fontSize }}</span>
              <el-slider v-model="appStore.fontSize" :min="12" :max="18" @change="appStore.save()" />
              <div class="pref-row">
                <span>{{ t('watermark') }}</span>
                <el-switch v-model="appStore.watermark" @change="appStore.save()" />
              </div>
            </div>
          </template>
        </el-dropdown>
        <button type="button" class="icon-btn" aria-label="收藏" @click="toggleFavorite"><el-icon><Star /></el-icon></button>
        </div>
        <span class="user-name">{{ userStore.user?.display_name }}</span>
        <el-button link type="primary" @click="logout">{{ t('logout') }}</el-button>
      </header>
      <main class="content-main">
        <router-view v-slot="{ Component }">
          <transition name="fade-page" mode="out-in">
            <keep-alive>
              <component :is="Component" :key="`${route.path}-${layoutStore.refreshKey}`" />
            </keep-alive>
          </transition>
        </router-view>
      </main>
      <div v-if="appStore.watermark" class="watermark" :style="watermarkStyle" aria-hidden="true"></div>
    </div>
    <div v-if="tagMenu.visible" class="context-menu" :style="{ left: `${tagMenu.x}px`, top: `${tagMenu.y}px` }">
      <button type="button" @click="closeView(tagMenu.view)">关闭</button>
      <button type="button" @click="closeOther">关闭其他</button>
      <button type="button" @click="closeTagged('left')">关闭左侧</button>
      <button type="button" @click="closeTagged('right')">关闭右侧</button>
      <button type="button" @click="refreshView">刷新</button>
    </div>
    <el-dialog v-model="paletteOpen" width="440px" :show-close="false" append-to-body @opened="focusPalette">
      <el-input ref="paletteInput" v-model="paletteQuery" placeholder="搜索菜单" @keydown.enter.prevent="openPaletteHit" />
      <div class="palette-list">
        <button v-for="item in paletteHits" :key="item.path" type="button" @click="openMenu(item.path)">{{ item.title }}</button>
        <p v-if="!paletteHits.length">没有匹配的菜单</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, onUnmounted, reactive, ref, resolveComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Bell, Expand, Fold, Operation, Search, Star } from '@element-plus/icons-vue'
import BrandMark from '@/components/BrandMark.vue'
import http from '@/api/http'
import { i18n } from '@/i18n'
import { resetAccess } from '@/router'
import { useAppStore } from '@/stores/app'
import { useLayoutStore } from '@/stores/layout'
import { useUserStore } from '@/stores/user'

const MenuNodes = defineComponent({
  name: 'MenuNodes',
  props: { items: Array, locale: String },
  setup(props) {
    return () => props.items.map((item) => {
      const label = props.locale === 'en' ? item.name_en : item.name
      const icon = h(resolveComponent('el-icon'), () => h(resolveComponent(item.icon || 'Menu')))
      if (item.children?.length) {
        return h(resolveComponent('el-sub-menu'), { index: String(item.id) }, {
          title: () => [icon, h('span', label)],
          default: () => h(MenuNodes, { items: item.children, locale: props.locale }),
        })
      }
      if (!item.path) return null
      return h(resolveComponent('el-menu-item'), { index: item.path }, () => [icon, h('span', label)])
    })
  },
})

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const appStore = useAppStore()
const layoutStore = useLayoutStore()
const userStore = useUserStore()
const unread = ref(0)
const favorites = ref([])
const dragTag = ref('')
const paletteOpen = ref(false)
const paletteQuery = ref('')
const paletteInput = ref()
const tagMenu = reactive({ visible: false, x: 0, y: 0, view: null })
const presets = ['#0f766e', '#115e59', '#3d6b58', '#4e7c73']
let idleAt = Date.now()
const watermarkStyle = computed(() => {
  const name = (userStore.user?.display_name || '').replace(/[<>&"]/g, '')
  const fill = appStore.theme === 'dark' ? '%23c5d5cf' : '%230f766e'
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='240' height='140'><g transform='rotate(-24 120 70)'><rect x='16' y='62' width='16' height='16' rx='3' fill='${fill}' fill-opacity='0.16'/><text x='40' y='75' fill='${fill}' fill-opacity='0.16' font-size='13' font-family='sans-serif'>${name}</text></g></svg>`
  return { backgroundImage: `url("data:image/svg+xml,${svg}")` }
})

const topMenus = computed(() => userStore.menus)
const topActive = computed(() => route.path)
const sideMenus = computed(() => {
  if (appStore.layout !== 'mix') return userStore.menus
  const current = userStore.menus.find((item) => item.path === route.path || item.children?.some((child) => child.path === route.path))
  return current?.children?.length ? current.children : userStore.menus
})
const crumbs = computed(() => route.matched.filter((item) => item.meta?.title).map((item) => ({
  path: item.path.startsWith('/') ? item.path : `/${item.path}`,
  title: appStore.locale === 'en' ? item.meta.titleEn || item.meta.title : item.meta.title,
})))

function closeView(view) {
  tagMenu.visible = false
  const next = layoutStore.removeVisitedView(view, route.path)
  if (next) router.push(next)
}
function openTagMenu(event, view) {
  tagMenu.visible = true
  tagMenu.x = event.clientX
  tagMenu.y = event.clientY
  tagMenu.view = view
}
function closeOther() {
  layoutStore.closeOthers(route.path)
  tagMenu.visible = false
}
function closeTagged(direction) {
  const next = layoutStore.closeSide(tagMenu.view?.path, direction, route.path)
  tagMenu.visible = false
  if (next) router.push(next)
}
function flattenMenus(items, bucket = []) {
  for (const item of items || []) {
    if (item.path) bucket.push({ path: item.path, title: appStore.locale === 'en' ? item.name_en : item.name })
    flattenMenus(item.children, bucket)
  }
  return bucket
}
const paletteHits = computed(() => {
  const query = paletteQuery.value.trim().toLowerCase()
  return flattenMenus(userStore.menus).filter((item) => !query || item.title.toLowerCase().includes(query) || item.path.includes(query)).slice(0, 8)
})
function openPalette() {
  paletteQuery.value = ''
  paletteOpen.value = true
}
function focusPalette() {
  paletteInput.value?.focus?.()
}
function openMenu(path) {
  paletteOpen.value = false
  router.push(path)
}
function openPaletteHit() {
  const hit = paletteHits.value[0]
  if (hit) openMenu(hit.path)
}
function onCommandKey(event) {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    openPalette()
  }
}
function refreshView() {
  layoutStore.refresh()
  tagMenu.visible = false
}
function setPrimary(color) {
  appStore.primary = color
  appStore.save()
}
function changeLocale() {
  i18n.global.locale.value = appStore.locale
  localStorage.setItem('locale', appStore.locale)
  appStore.save()
}
async function toggleFavorite() {
  const menu = findMenu(userStore.menus, route.path)
  if (!menu) return
  await http.post('/favorites/toggle', { menu_id: menu.id })
  await loadFavorites()
}
async function loadFavorites() {
  try {
    favorites.value = (await http.get('/favorites')).items || []
  } catch { /* ignore */ }
}
function findMenu(items, path) {
  for (const item of items || []) {
    if (item.path === path) return item
    const found = findMenu(item.children, path)
    if (found) return found
  }
  return null
}
function logout() {
  http.post('/logout').catch(() => {})
  resetAccess()
  userStore.clearSession()
  router.push('/login')
}
function markActive() { idleAt = Date.now() }

let narrow = window.innerWidth < 960
if (narrow) layoutStore.sidebarCollapsed = true

function syncSidebar() {
  const next = window.innerWidth < 960
  if (next && !narrow) layoutStore.sidebarCollapsed = true
  if (!next && narrow) layoutStore.sidebarCollapsed = localStorage.getItem('sidebar-collapsed') === 'true'
  narrow = next
}

onMounted(async () => {
  window.addEventListener('click', () => { tagMenu.visible = false })
  window.addEventListener('keydown', onCommandKey)
  window.addEventListener('pointerdown', markActive)
  window.addEventListener('resize', syncSidebar)
  loadFavorites()
  try {
    unread.value = (await http.get('/messages', { params: { page: 1, page_size: 1 } })).unread || 0
  } catch { /* ignore */ }
  setInterval(() => {
    if (userStore.token && Date.now() - idleAt > appStore.sessionMinutes * 60 * 1000) logout()
  }, 30000)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onCommandKey)
  window.removeEventListener('pointerdown', markActive)
  window.removeEventListener('resize', syncSidebar)
})
</script>

<style scoped>
.admin-shell { position: relative; display: flex; height: 100vh; overflow: hidden; background: var(--app-bg); }
.layout-top { display: block; }
.layout-top .sidebar { display: none; }
.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  background: var(--app-surface);
  border-right: 1px solid var(--app-border-light);
  overflow: auto;
  transition: width 0.24s ease-out, transform 0.24s ease-out;
}
.sidebar.is-collapsed { width: var(--sidebar-collapsed); }
.sidebar :deep(.el-menu) { border-right: 0; background: transparent; }
.sidebar :deep(.el-icon) { font-size: 18px; }
.sidebar.is-collapsed .brand { justify-content: center; padding: 0; }
.brand { display: flex; align-items: center; gap: 8px; height: var(--header-height); padding: 0 16px; }
.brand strong { font-size: var(--text-subtitle); font-weight: 600; }
.brand-logo { width: 28px; height: 28px; }
.fav-block { padding: 4px 12px 8px; }
.fav-block p { margin: 0 4px 4px; color: var(--app-faint); font-size: 12px; }
.fav-block button { display: block; width: 100%; border: 0; background: transparent; text-align: left; border-radius: var(--radius-xs); padding: 6px 8px; color: var(--app-text); font: inherit; font-size: var(--text-body); font-weight: 400; line-height: 22px; cursor: pointer; }
.fav-block button.on, .fav-block button:hover { color: var(--app-primary); background: color-mix(in srgb, var(--app-primary) 8%, transparent); }
.palette-list { display: flex; flex-direction: column; gap: 4px; margin-top: 12px; }
.palette-list button { border: 0; background: transparent; text-align: left; border-radius: var(--radius-xs); padding: 8px 10px; cursor: pointer; color: var(--app-text); }
.palette-list button:hover { background: var(--app-surface-muted); }
.palette-list p { margin: 8px 0 0; color: var(--app-faint); font-size: 13px; }
.main-col { position: relative; flex: 1; min-width: 0; display: flex; flex-direction: column; }
.topbar {
  height: var(--header-height);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  background: var(--app-surface);
  border-bottom: 1px solid var(--app-border-light);
}
.top-menu { flex: 0 1 auto; max-width: 42%; border-bottom: 0; background: transparent; }
.crumb-inline { display: flex; align-items: center; gap: 8px; max-width: 220px; overflow: hidden; white-space: nowrap; font-size: 12px; color: var(--app-faint); }
.crumb-inline a { color: var(--app-muted); text-decoration: none; }
.crumb-inline strong { color: var(--app-text); font-weight: 500; }
.crumb-inline a + a::before, .crumb-inline a + strong::before { content: '/'; margin-right: 8px; color: var(--app-faint); font-weight: 400; }
.tags-track { flex: 1; min-width: 0; display: flex; gap: 4px; overflow: auto; scrollbar-width: none; }
.tags-track::-webkit-scrollbar { display: none; }
.tag {
  flex: 0 0 auto;
  border: 0;
  background: transparent;
  color: var(--app-muted);
  border-radius: var(--radius-xs);
  height: 28px;
  padding: 0 8px;
  cursor: pointer;
  font-size: var(--text-caption);
  transition: background-color 0.22s ease-out, color 0.22s ease-out;
}
.tag:hover { background: var(--app-surface-muted); color: var(--app-text); }
.tag.active {
  color: var(--app-primary);
  background: transparent;
  font-weight: 500;
  box-shadow: inset 0 -2px 0 var(--app-primary);
}
.tag em {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-left: 4px;
  border-radius: 50%;
  font-style: normal;
  color: var(--app-faint);
}
.tag em:hover { background: var(--app-surface-muted); color: var(--app-text); }
.tag-enter-active, .tag-leave-active { transition: opacity 0.22s ease-out, transform 0.22s ease-out; }
.tag-enter-from, .tag-leave-to { opacity: 0; transform: translateY(4px); }
.tool-group { display: flex; align-items: center; gap: 4px; }
.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  background: transparent;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--app-text);
  transition: background-color 0.22s ease-out;
}
.icon-btn:hover { background: var(--app-surface-muted); }
.icon-btn:focus-visible { outline: 2px solid var(--app-primary); outline-offset: 2px; }
.user-name { max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: var(--text-body); color: var(--app-muted); }
.crumb { padding: 8px 24px 0; }
.crumb :deep(.el-breadcrumb__inner) { color: var(--app-muted); font-weight: 400; font-size: var(--text-caption); }
.content-main { flex: 1; min-height: 0; overflow: hidden; }
.pref { width: 280px; display: flex; flex-direction: column; gap: 8px; padding: 16px; font-size: var(--text-caption); color: var(--app-muted); }
.pref-row { display: flex; align-items: center; justify-content: space-between; }
.swatches { display: flex; align-items: center; gap: 8px; }
.swatch, .swatch-input {
  width: 22px;
  height: 22px;
  padding: 0;
  border: 2px solid transparent;
  border-radius: 50%;
  cursor: pointer;
}
.swatch.on { border-color: var(--app-text); }
.swatch-input { background: transparent; }
.watermark {
  position: absolute;
  inset: var(--header-height) 0 0;
  pointer-events: none;
  background-repeat: repeat;
}
.context-menu { position: fixed; z-index: 30; background: var(--app-surface); border: 1px solid var(--app-border-light); border-radius: var(--radius-md); box-shadow: var(--shadow-pop); padding: 4px; }
.context-menu button { display: block; width: 100%; text-align: left; border: 0; background: transparent; border-radius: var(--radius-xs); padding: 8px 12px; cursor: pointer; color: var(--app-text); }
.context-menu button:hover { background: var(--app-surface-muted); }
.sidebar-mask { display: none; }

@media (max-width: 960px) {
  .sidebar {
    position: absolute;
    z-index: 40;
    height: 100%;
    box-shadow: var(--shadow-modal);
  }
  .sidebar.is-collapsed {
    width: var(--sidebar-width);
    transform: translateX(-100%);
    box-shadow: none;
  }
  .sidebar-mask {
    display: block;
    position: absolute;
    inset: 0;
    z-index: 30;
    background: rgba(16, 22, 20, 0.35);
  }
}
</style>
