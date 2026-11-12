import { defineStore } from 'pinia'
import { ref } from 'vue'
import http, { readRefresh, readToken } from '@/api/http'

const box = () => (localStorage.getItem('token') ? localStorage : sessionStorage)

export const useUserStore = defineStore('user', () => {
  const token = ref(readToken())
  const refreshToken = ref(readRefresh())
  const user = ref(JSON.parse(localStorage.getItem('user') || sessionStorage.getItem('user') || 'null'))
  const permissions = ref(JSON.parse(localStorage.getItem('permissions') || sessionStorage.getItem('permissions') || '[]'))
  const menus = ref([])

  function persist(remember, payload) {
    const target = remember ? localStorage : sessionStorage
    const other = remember ? sessionStorage : localStorage
    for (const key of ['token', 'refreshToken', 'user', 'permissions', 'username', 'displayName']) other.removeItem(key)
    target.setItem('token', payload.token)
    target.setItem('refreshToken', payload.refresh_token)
    target.setItem('user', JSON.stringify(payload.user))
    target.setItem('permissions', JSON.stringify(payload.permissions || []))
    target.setItem('username', payload.user.username)
    target.setItem('displayName', payload.user.display_name)
    token.value = payload.token
    refreshToken.value = payload.refresh_token
    user.value = payload.user
    permissions.value = payload.permissions || []
    menus.value = payload.menus || []
  }

  function clearSession() {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    permissions.value = []
    menus.value = []
    for (const key of ['token', 'refreshToken', 'user', 'permissions', 'username', 'displayName']) {
      localStorage.removeItem(key)
      sessionStorage.removeItem(key)
    }
  }

  async function loadMe() {
    const result = await http.get('/me')
    user.value = result.user
    permissions.value = result.permissions || []
    menus.value = result.menus || []
    box().setItem('user', JSON.stringify(result.user))
    box().setItem('permissions', JSON.stringify(permissions.value))
    return result
  }

  function can(code) {
    if (!code || user.value?.is_super) return true
    return permissions.value.includes(code)
  }

  return { token, refreshToken, user, permissions, menus, persist, clearSession, loadMe, can }
})
