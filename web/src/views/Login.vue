<template>
  <div :class="['login-page', { 'is-leaving': leaving }]">
    <section class="brand-pane">
      <span class="brand-plate">
        <BrandMark class="brand-logo" />
      </span>
      <h1>管理系统</h1>
    </section>
    <section class="form-pane">
    <div class="login-card">
      <header class="login-brand">
        <h2>登录</h2>
      </header>
      <form @submit.prevent="submit">
        <div class="field" :class="{ lifted: userFocus || form.username, invalid: Boolean(errorMessage) }">
          <el-input
            id="login-username"
            v-model="form.username"
            autocomplete="username"
            @focus="userFocus = true"
            @blur="userFocus = false"
          />
          <label for="login-username">{{ t('username') }}</label>
        </div>
        <div class="field" :class="{ lifted: passwordFocus || form.password, invalid: Boolean(errorMessage) }">
          <el-input
            id="login-password"
            v-model="form.password"
            type="password"
            show-password
            autocomplete="current-password"
            @focus="passwordFocus = true"
            @blur="passwordFocus = false"
          />
          <label for="login-password">{{ t('password') }}</label>
        </div>
        <el-checkbox v-model="form.remember" class="remember">{{ t('remember') }}</el-checkbox>
        <p v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</p>
        <el-button type="primary" class="submit" native-type="submit" :loading="loading" :disabled="loading">
          {{ t('login') }}
        </el-button>
      </form>
      <footer class="login-foot">
        <button type="button" class="text-link" @click="registerOpen = true">{{ t('register') }}</button>
        <p class="hint">账号 admin / 123456</p>
      </footer>
    </div>
    </section>
    <el-dialog v-model="registerOpen" :title="t('register')" width="420px">
      <el-form label-position="top">
        <el-form-item label="用户名"><el-input v-model="registerForm.username" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="registerForm.password" type="password" show-password /></el-form-item>
        <el-form-item label="显示名称"><el-input v-model="registerForm.display_name" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="registerForm.email" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="registerOpen = false">取消</el-button>
        <el-button type="primary" @click="register">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import BrandMark from '@/components/BrandMark.vue'
import http from '@/api/http'
import { resetAccess } from '@/router'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const leaving = ref(false)
const errorMessage = ref('')
const registerOpen = ref(false)
const userFocus = ref(false)
const passwordFocus = ref(false)
const form = reactive({ username: 'admin', password: '123456', remember: true })
const registerForm = reactive({ username: '', password: '', display_name: '', email: '' })

async function submit() {
  errorMessage.value = ''
  loading.value = true
  try {
    const result = await http.post('/login', { ...form }, { skipAuth: true })
    resetAccess()
    userStore.persist(form.remember, result)
    leaving.value = true
    window.setTimeout(() => {
      router.push(result.user.must_change_password ? '/account' : '/home')
    }, 220)
  } catch (error) {
    errorMessage.value = error.displayMessage || '登录失败'
  } finally {
    loading.value = false
  }
}

async function register() {
  await http.post('/register', { ...registerForm }, { skipAuth: true })
  registerOpen.value = false
  ElMessage.success('已提交，等待管理员启用')
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: grid;
  grid-template-columns: minmax(280px, 42%) 1fr;
  overflow: hidden;
  background: var(--app-surface);
  transition: opacity 0.22s ease-out;
}
.login-page.is-leaving { opacity: 0; }

.brand-pane {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 12px;
  padding: 48px;
  color: #f4fbf9;
  background:
    radial-gradient(520px 320px at 20% 0%, color-mix(in srgb, #fff 18%, transparent), transparent 70%),
    var(--app-primary);
  overflow: hidden;
}
.brand-pane::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgb(255 255 255 / 3.5%) 1px, transparent 1.2px);
  background-size: 22px 22px;
  pointer-events: none;
}
.brand-plate {
  position: relative;
  display: block;
  width: 56px;
  height: 56px;
  padding: 4px;
  border-radius: 16px;
  background: #fff;
  box-sizing: border-box;
}
.brand-logo { display: block; width: 100%; height: 100%; }
.brand-pane h1 { position: relative; margin: 8px 0 0; font-size: 32px; font-weight: 600; }

.form-pane {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  background:
    radial-gradient(480px 240px at 80% 0%, var(--app-accent), transparent 70%),
    var(--app-bg);
}

.login-card {
  width: min(400px, 100%);
  padding: 8px 8px 0;
  background: transparent;
  border: 0;
  box-shadow: none;
}

.login-brand { margin-bottom: 24px; }
h2 { margin: 0; font-size: var(--text-display); font-weight: 600; }

.submit {
  background-image: linear-gradient(180deg, color-mix(in srgb, var(--app-primary) 82%, #fff), var(--app-primary));
}
.submit:hover:not(.is-disabled) { transform: translateY(-1px); }
.field.invalid { animation: field-shake 0.22s ease-out; }

@keyframes field-shake {
  25% { transform: translateX(-2px); }
  75% { transform: translateX(2px); }
}

@media (max-width: 860px) {
  .login-page { grid-template-columns: 1fr; }
  .brand-pane { min-height: 180px; padding: 32px 24px; justify-content: flex-start; }
  .brand-pane h1 { font-size: 24px; }
}

.field { position: relative; margin-bottom: 16px; }

.field :deep(.el-input__wrapper) {
  height: 40px;
  background: var(--app-surface);
  box-shadow: 0 0 0 1px var(--app-border) inset;
  transition: box-shadow 0.22s ease-out;
}

.field:hover :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--app-primary) 45%, var(--app-border)) inset;
}

.field:focus-within :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--app-primary) inset, 0 0 0 3px var(--app-primary-glow);
}

.field label {
  position: absolute;
  left: 12px;
  top: 50%;
  z-index: 1;
  margin: 0;
  padding: 0 4px;
  color: var(--app-muted);
  font-size: 14px;
  line-height: 1;
  pointer-events: none;
  transform: translateY(-50%);
  transition: top 0.22s ease-out, transform 0.22s ease-out, font-size 0.22s ease-out, color 0.22s ease-out;
}

.field.lifted label,
.field:focus-within label {
  top: 0;
  font-size: 12px;
  color: var(--app-primary);
  background: var(--app-bg);
}

.field.invalid :deep(.el-input__wrapper),
.field.invalid:focus-within :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--color-danger) inset, 0 0 0 3px color-mix(in srgb, var(--color-danger) 16%, transparent);
}

.field.invalid label,
.field.invalid:focus-within label { color: var(--color-danger); }

.remember { display: flex; margin: 0 0 8px; }

.form-error {
  margin: 0 0 8px;
  color: var(--color-danger);
  font-size: var(--text-caption);
}

.submit { width: 100%; height: 40px; margin-top: 8px; }
.submit:focus-visible { outline: 2px solid var(--app-primary); outline-offset: 2px; }

.login-foot {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin-top: 16px;
}

.text-link {
  border: 0;
  padding: 0;
  background: transparent;
  color: var(--app-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.text-link:hover { color: var(--app-primary-deep); }
.text-link:focus-visible { outline: 2px solid var(--app-primary); outline-offset: 2px; border-radius: 2px; }

.hint {
  margin: 0;
  color: var(--app-faint);
  font-size: 12px;
  font-weight: 400;
}
</style>
