<template>
  <div class="page-shell">
    <div class="page-head"><h1 class="page-title">账号</h1></div>
    <div class="grid">
      <section class="panel-card block">
        <h2>资料</h2>
        <el-form label-position="top">
          <el-form-item label="显示名称"><el-input v-model="form.display_name" /></el-form-item>
          <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
          <el-form-item label="手机"><el-input v-model="form.phone" /></el-form-item>
        </el-form>
        <el-upload :show-file-list="false" :http-request="uploadAvatar"><el-button>上传头像</el-button></el-upload>
        <el-button type="primary" :loading="saving" @click="saveProfile">保存</el-button>
      </section>
      <section class="panel-card block">
        <h2>修改密码</h2>
        <el-input v-model="oldPassword" type="password" show-password placeholder="当前密码" />
        <el-input v-model="newPassword" type="password" show-password placeholder="新密码" />
        <el-button type="primary" :loading="savingPassword" @click="savePassword">更新密码</el-button>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const form = reactive({ display_name: '', email: '', phone: '', avatar: '' })
const oldPassword = ref('')
const newPassword = ref('')
const saving = ref(false)
const savingPassword = ref(false)

onMounted(() => Object.assign(form, userStore.user || {}))

async function uploadAvatar(option) {
  const data = new FormData()
  data.append('file', option.file)
  const result = await http.post('/files/upload', data)
  form.avatar = `/api/v1/files/${result.item.id}/raw`
}

async function saveProfile() {
  saving.value = true
  try {
    const result = await http.post('/profile', { ...form })
    userStore.user = result.user
    ElMessage.success('已保存')
  } catch (error) {
    ElMessage.error(error.displayMessage || '保存失败')
  } finally {
    saving.value = false
  }
}

async function savePassword() {
  savingPassword.value = true
  try {
    const result = await http.post('/password', { old_password: oldPassword.value, new_password: newPassword.value }, { idempotent: true })
    const store = localStorage.getItem('token') ? localStorage : sessionStorage
    store.setItem('token', result.token)
    userStore.user = result.user
    oldPassword.value = ''
    newPassword.value = ''
    ElMessage.success('密码已更新')
  } catch (error) {
    ElMessage.error(error.displayMessage || '更新失败')
  } finally {
    savingPassword.value = false
  }
}
</script>

<style scoped>
.page-shell { overflow: auto; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 420px)); gap: 12px; }
.block { display: flex; flex-direction: column; gap: 12px; padding: 18px; }
h2 { margin: 0; font-size: 16px; }
</style>
