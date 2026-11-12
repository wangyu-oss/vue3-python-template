import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useLayoutStore = defineStore('layout', () => {
  const sidebarCollapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')
  const visitedViews = ref([])
  const refreshKey = ref(0)

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem('sidebar-collapsed', String(sidebarCollapsed.value))
  }

  function addVisitedView(route) {
    if (!route.name || route.path === '/login') return
    const existing = visitedViews.value.find((view) => view.path === route.path)
    const title = route.meta?.title || route.name
    if (existing) {
      existing.title = title
      existing.fullPath = route.fullPath
      return
    }
    visitedViews.value.push({
      path: route.path,
      fullPath: route.fullPath,
      title,
      affix: route.path === '/home',
    })
  }

  function removeVisitedView(view, activePath) {
    if (view.affix) return null
    const index = visitedViews.value.findIndex((item) => item.path === view.path)
    if (index < 0) return null
    visitedViews.value.splice(index, 1)
    if (view.path !== activePath) return null
    const next = visitedViews.value[index] || visitedViews.value[index - 1]
    return next?.fullPath || '/home'
  }

  function closeOthers(path) {
    visitedViews.value = visitedViews.value.filter((view) => view.affix || view.path === path)
  }

  function closeSide(path, direction, activePath) {
    const index = visitedViews.value.findIndex((view) => view.path === path)
    if (index < 0) return null
    visitedViews.value = visitedViews.value.filter((view, itemIndex) => {
      if (view.affix) return true
      return direction === 'left' ? itemIndex >= index : itemIndex <= index
    })
    if (visitedViews.value.some((view) => view.path === activePath)) return null
    const next = visitedViews.value[Math.min(index, visitedViews.value.length - 1)]
    return next?.fullPath || '/home'
  }

  function moveView(fromPath, toPath) {
    const from = visitedViews.value.findIndex((view) => view.path === fromPath)
    const to = visitedViews.value.findIndex((view) => view.path === toPath)
    if (from < 0 || to < 0 || from === to) return
    const [item] = visitedViews.value.splice(from, 1)
    visitedViews.value.splice(to, 0, item)
  }

  function refresh() {
    refreshKey.value += 1
  }

  return { sidebarCollapsed, visitedViews, refreshKey, toggleSidebar, addVisitedView, removeVisitedView, closeOthers, closeSide, moveView, refresh }
})
