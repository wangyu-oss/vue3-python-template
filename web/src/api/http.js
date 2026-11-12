import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 20000,
})

const pending = new Map()
let refreshing = null

export function readToken() {
  return localStorage.getItem('token') || sessionStorage.getItem('token') || ''
}

export function readRefresh() {
  return localStorage.getItem('refreshToken') || sessionStorage.getItem('refreshToken') || ''
}

function writeToken(token) {
  if (localStorage.getItem('token')) localStorage.setItem('token', token)
  if (sessionStorage.getItem('token')) sessionStorage.setItem('token', token)
  if (!localStorage.getItem('token') && !sessionStorage.getItem('token')) localStorage.setItem('token', token)
}

function clearSession() {
  for (const key of ['token', 'refreshToken', 'username', 'displayName', 'user', 'permissions']) {
    localStorage.removeItem(key)
    sessionStorage.removeItem(key)
  }
}

http.interceptors.request.use((config) => {
  const token = readToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  if (config.idempotent) config.headers['Idempotency-Key'] = crypto.randomUUID()
  const key = `${config.method}:${config.url}`
  if (config.cancelPrevious && pending.has(key)) pending.get(key).abort()
  if (config.cancelPrevious) {
    const controller = new AbortController()
    config.signal = controller.signal
    pending.set(key, controller)
    config.dupKey = key
  }
  return config
})

http.interceptors.response.use(
  (response) => {
    if (response.config.dupKey) pending.delete(response.config.dupKey)
    return response.data
  },
  async (error) => {
    if (error.code === 'ERR_CANCELED') return Promise.reject(error)
    const config = error.config || {}
    if (config.dupKey) pending.delete(config.dupKey)
    if (error.response?.status === 401 && !config.skipAuth && !config.retried && readRefresh()) {
      try {
        refreshing = refreshing || axios.post('/api/v1/refresh', { refresh_token: readRefresh() })
        const result = await refreshing
        refreshing = null
        writeToken(result.data.token)
        config.retried = true
        config.headers = { ...(config.headers || {}), Authorization: `Bearer ${result.data.token}` }
        return http(config)
      } catch {
        refreshing = null
        clearSession()
      }
    }
    if (error.response?.status === 401 && !config.skipAuth && !location.hash.startsWith('#/login')) {
      clearSession()
      location.hash = '#/login'
    }
    const status = error.response?.status
    error.displayMessage = error.response?.data?.error
      || (status === 404 ? '内容不存在或已移除' : '')
      || '请求失败'
    return Promise.reject(error)
  },
)

export default http
