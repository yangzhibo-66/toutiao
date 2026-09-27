<template>
  <header class="app-search-header">
    <div class="search-pill">
      <van-icon name="search" />
      <input
        :value="modelValue"
        type="search"
        placeholder="搜你想看的"
        @input="$emit('update:modelValue', $event.target.value)"
        @keyup.enter="$emit('search')"
      >
      <button type="button" @click="$emit('search')">搜索</button>
    </div>
    <button class="publish-btn" type="button" @click="$emit('publish')">
      <van-icon name="plus" />
      <span>发布</span>
    </button>
  </header>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

defineEmits(['update:modelValue', 'search', 'publish'])
</script>

<style scoped>
.app-search-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 12px 14px 8px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(20px);
}

.search-pill {
  flex: 1;
  display: flex;
  align-items: center;
  height: 38px;
  padding: 0 8px 0 12px;
  color: #9aa3af;
  background: #f4f5f7;
  border-radius: 999px;
}

.search-pill input {
  flex: 1;
  min-width: 0;
  height: 100%;
  margin: 0 8px;
  color: #111827;
  font-size: 14px;
  background: transparent;
  border: 0;
  outline: 0;
}

.search-pill button {
  flex: 0 0 auto;
  padding: 0 4px;
  color: #f04438;
  font-size: 13px;
  font-weight: 800;
  background: transparent;
  border: 0;
}

.publish-btn {
  flex: 0 0 auto;
  display: inline-flex;
  gap: 4px;
  align-items: center;
  justify-content: center;
  height: 38px;
  padding: 0 10px;
  color: #111827;
  font-size: 13px;
  font-weight: 800;
  background: #fff;
  border: 1px solid #eceff3;
  border-radius: 999px;
  box-shadow: 0 8px 18px rgba(17, 24, 39, 0.06);
}
</style>
