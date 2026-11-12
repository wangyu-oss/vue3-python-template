import { createRouter, createWebHashHistory } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useLayoutStore } from '@/stores/layout'
import { useUserStore } from '@/stores/user'

const pages = {
  home: () => import('@/views/Home.vue'),
  entity: () => import('@/views/Entity.vue'),
  files: () => import('@/views/Files.vue'),
  messages: () => import('@/views/Messages.vue'),
  dicts: () => import('@/views/Dicts.vue'),
  jobs: () => import('@/views/Jobs.vue'),
  logs: () => import('@/views/Logs.vue'),
  online: () => import('@/views/Online.vue'),
  recycle: () => import('@/views/Recycle.vue'),
  settings: () => import('@/views/Settings.vue'),
  demo: () => import('@/views/Demo.vue'),
  account: () => import('@/views/Account.vue'),
}

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/Login.vue'), meta: { hidden: true } },
    { path: '/', name: 'layout', component: () => import('@/components/layout/AdminLayout.vue'), redirect: '/home', children: [] },
  ],
})

let installed = false

export function resetAccess() {
  installed = false
  for (const route of router.getRoutes()) {
    if (typeof route.name === 'string' && route.name.startsWith('/')) router.removeRoute(route.name)
  }
}

function flatten(items, bucket = []) {
  for (const item of items || []) {
    if (item.path && item.component && item.component !== 'dir') bucket.push(item)
    flatten(item.children, bucket)
  }
  return bucket
}

export function installMenus(menus) {
  const items = flatten(menus)
  items.push({ path: '/account', name: '账号', name_en: 'Account', icon: 'User', component: 'account', keep_alive: true })
  for (const item of items) {
    if (router.hasRoute(item.path)) continue
    router.addRoute('layout', {
      path: item.path.replace(/^\//, ''),
      name: item.path,
      component: pages[item.component] || pages.entity,
      meta: {
        title: item.name,
        titleEn: item.name_en,
        icon: item.icon,
        keepAlive: item.keep_alive,
        component: item.component,
        permission: item.permission,
      },
    })
  }
  installed = true
}

router.beforeEach(async (to) => {
  const userStore = useUserStore()
  if (to.path === '/login') return userStore.token ? '/home' : true
  if (!userStore.token) return '/login'
  if (!installed) {
    const result = await userStore.loadMe()
    installMenus(result.menus)
    const appStore = useAppStore()
    await appStore.hydrate()
    return to.fullPath
  }
  if (userStore.user?.must_change_password && to.path !== '/account') return '/account'
  return true
})

router.afterEach((to) => {
  if (to.path !== '/login') useLayoutStore().addVisitedView(to)
})

export default router
