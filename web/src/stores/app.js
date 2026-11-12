import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import http from '@/api/http'

const BRAND_PRIMARY = '#0f766e'

function brandPrimary(value) {
  const color = String(value || '').toLowerCase()
  if (!color || color === '#2f6fad' || color === '#409eff') return BRAND_PRIMARY
  return value
}

const saved = JSON.parse(localStorage.getItem('preferences') || '{}')
saved.primary = brandPrimary(saved.primary)

function clampChannel(value) {
  return Math.max(0, Math.min(255, Math.round(value)))
}

function parseHex(hex) {
  const raw = String(hex || '').trim().replace('#', '')
  const full = raw.length === 3 ? raw.split('').map((char) => char + char).join('') : raw
  const value = Number.parseInt(full, 16)
  if (!Number.isFinite(value) || full.length !== 6) return { r: 15, g: 118, b: 110 }
  return { r: (value >> 16) & 255, g: (value >> 8) & 255, b: value & 255 }
}

function mix(from, to, amount) {
  return {
    r: from.r + (to.r - from.r) * amount,
    g: from.g + (to.g - from.g) * amount,
    b: from.b + (to.b - from.b) * amount,
  }
}

function toHex(rgb) {
  return `#${[rgb.r, rgb.g, rgb.b].map((channel) => clampChannel(channel).toString(16).padStart(2, '0')).join('')}`
}

function toRgba(rgb, alpha) {
  return `rgba(${clampChannel(rgb.r)}, ${clampChannel(rgb.g)}, ${clampChannel(rgb.b)}, ${alpha})`
}

export const useAppStore = defineStore('app', () => {
  const theme = ref(saved.theme || 'light')
  const layout = ref(saved.layout || 'side')
  const locale = ref(saved.locale || 'zh')
  const fontSize = ref(saved.fontSize || 14)
  const primary = ref(saved.primary || BRAND_PRIMARY)
  const density = ref(saved.density || 'comfortable')
  const watermark = ref(false)
  const sessionMinutes = ref(Number(saved.sessionMinutes || 120))

  function apply() {
    const root = document.documentElement
    const dark = theme.value === 'dark'
    root.classList.toggle('dark', dark)
    root.classList.toggle('theme-care', theme.value === 'care')
    root.classList.toggle('density-compact', density.value === 'compact')
    root.classList.toggle('density-roomy', density.value === 'roomy')
    root.style.fontSize = ''
    root.style.setProperty('--text-body', `${fontSize.value}px`)
    root.style.setProperty('--el-font-size-base', `${fontSize.value}px`)
    const rgb = parseHex(primary.value)
    const lift = dark ? { r: 226, g: 236, b: 232 } : { r: 255, g: 255, b: 255 }
    const softBase = dark ? { r: 26, g: 35, b: 32 } : { r: 255, g: 255, b: 255 }
    root.style.setProperty('--app-primary', toHex(rgb))
    root.style.setProperty('--app-primary-deep', toHex(mix(rgb, { r: 0, g: 0, b: 0 }, 0.18)))
    root.style.setProperty('--app-primary-soft', toHex(mix(rgb, softBase, dark ? 0.82 : 0.9)))
    root.style.setProperty('--app-primary-glow', toRgba(rgb, dark ? 0.28 : 0.16))
    root.style.setProperty('--el-color-primary', toHex(rgb))
    root.style.setProperty('--el-color-primary-dark-2', toHex(mix(rgb, { r: 0, g: 0, b: 0 }, 0.2)))
    ;[3, 5, 7, 8, 9].forEach((step) => {
      root.style.setProperty(`--el-color-primary-light-${step}`, toHex(mix(rgb, lift, step / 10)))
    })
  }

  async function save() {
    const preferences = {
      theme: theme.value,
      layout: layout.value,
      locale: locale.value,
      fontSize: fontSize.value,
      primary: primary.value,
      density: density.value,
      watermark: watermark.value,
      sessionMinutes: sessionMinutes.value,
    }
    localStorage.setItem('preferences', JSON.stringify(preferences))
    apply()
    if (localStorage.getItem('token') || sessionStorage.getItem('token')) {
      await http.post('/preferences', preferences)
    }
  }

  async function hydrate() {
    try {
      const result = await http.get('/preferences')
      Object.assign(saved, result.preferences || {})
      theme.value = saved.theme || theme.value
      layout.value = saved.layout || layout.value
      locale.value = saved.locale || locale.value
      fontSize.value = saved.fontSize || fontSize.value
      primary.value = brandPrimary(saved.primary || primary.value)
      density.value = saved.density || density.value
      watermark.value = saved.watermark === true
    } catch {
      /* keep local preferences */
    }
    apply()
  }

  watch([theme, layout, locale, fontSize, primary, density, watermark], apply)

  return { theme, layout, locale, fontSize, primary, density, watermark, sessionMinutes, apply, save, hydrate }
})
