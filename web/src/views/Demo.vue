<template>
  <div class="page-shell">
    <div class="page-head"><h1 class="page-title">扩展能力</h1></div>
    <section v-for="group in groups" :key="group.title" class="panel-card block">
      <h2>{{ group.title }}</h2>
      <div class="buttons">
        <el-button v-for="item in group.items" :key="item" @click="show(item)">{{ item }}</el-button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'

const groups = [
  { title: '登录与消息', items: ['短信验证码', '邮箱发送', 'OAuth 登录', 'SSO', '企业微信', '钉钉', 'WebSocket 推送'] },
  { title: '文件与报表', items: ['分片续传', 'MinIO', '对象存储', '异步导出', 'PDF 模板', '打印模板', '流程图设计', '拖拽报表'] },
  { title: '平台组件', items: ['Celery', 'Redis', '多数据库', '读写分离', '接口文档站', '灰度发布', 'PWA', '摄像头扫码', '木马扫描'] },
  { title: '业务扩展', items: ['支付', '电子签章', '地图', 'OCR', 'AI 对话', '即时通讯', '优惠券', '多租户'] },
]

function show(item) {
  ElMessage.info(`${item}：当前为演示`)
}
</script>

<style scoped>
.page-shell { overflow: auto; display: flex; flex-direction: column; gap: 12px; }
.block { padding: 16px; }
h2 { margin: 0 0 12px; font-size: 16px; }
.buttons { display: flex; flex-wrap: wrap; gap: 8px; }
</style>
