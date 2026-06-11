<template>
  <div class="tabbar-shell">
    <van-tabbar v-model="active" route>
      <van-tabbar-item to="/home" icon="home-o">{{ $t('nav.home') }}</van-tabbar-item>
      <van-tabbar-item to="/aichat" icon="chat-o">{{ $t('nav.aiChat') }}</van-tabbar-item>
      <van-tabbar-item to="/my" icon="user-o">{{ $t('nav.my') }}</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup>
import { ref, watchEffect } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const active = ref(0)

watchEffect(() => {
  if (route.path.includes('/home')) {
    active.value = 0
  } else if (route.path.includes('/aichat')) {
    active.value = 1
  } else if (route.path.includes('/my')) {
    active.value = 2
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
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(22px);
  box-shadow: 0 -10px 30px rgba(31, 59, 89, 0.08);
  border-top: 1px solid rgba(221, 230, 241, 0.82);
}

:deep(.van-tabbar-item) {
  color: var(--text-color-lighter);
  transition: transform 0.18s ease;
}

:deep(.van-tabbar-item--active) {
  color: var(--primary-color);
}

:deep(.van-tabbar-item--active .van-tabbar-item__icon) {
  transform: translateY(-2px);
}

:deep(.van-tabbar-item__icon) {
  font-size: 22px;
}

:deep(.van-tabbar-item__text) {
  font-size: 12px;
  font-weight: 700;
}
</style>
