<template>
  <div class="tabbar-shell">
    <van-tabbar v-model="active" route>
      <van-tabbar-item to="/home" icon="home-o">首页</van-tabbar-item>
      <van-tabbar-item to="/hot" icon="fire-o">热榜</van-tabbar-item>
      <van-tabbar-item to="/aichat" icon="chat-o">AI</van-tabbar-item>
      <van-tabbar-item to="/my" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup>
import { ref, watchEffect } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const active = ref(0)

watchEffect(() => {
  if (route.path.includes('/hot')) {
    active.value = 1
  } else if (route.path.includes('/aichat')) {
    active.value = 2
  } else if (route.path.includes('/my')) {
    active.value = 3
  } else {
    active.value = 0
  }
})
</script>

<style scoped>
.tabbar-shell {
  position: relative;
}

:deep(.van-tabbar) {
  left: 50%;
  width: min(750px, 100vw);
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 -8px 24px rgba(17, 24, 39, 0.08);
  border-top: 1px solid #eef1f5;
}

:deep(.van-tabbar-item) {
  color: #111827;
}

:deep(.van-tabbar-item--active) {
  color: #f04438;
  font-weight: 900;
}

:deep(.van-tabbar-item__icon) {
  font-size: 22px;
}

:deep(.van-tabbar-item__text) {
  font-size: 12px;
  font-weight: 800;
}
</style>
