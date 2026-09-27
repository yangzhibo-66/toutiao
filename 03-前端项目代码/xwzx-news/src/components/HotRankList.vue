<template>
  <div class="hot-rank-list">
    <div
      v-for="(item, index) in items"
      :key="item.id"
      class="rank-row"
      @click="$emit('select', item)"
    >
      <div class="rank-index" :class="{ top: index < 3 }">{{ index + 1 }}</div>
      <div class="rank-title">{{ item.title }}</div>
      <div class="rank-heat">
        <van-icon name="fire-o" />
        {{ heatText(item, index) }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatCount } from '../utils/newsFormat'

defineProps({
  items: {
    type: Array,
    default: () => []
  }
})

defineEmits(['select'])

const heatText = (item, index) => {
  const base = Number(item.views || 0) + (10 - index) * 48600
  return formatCount(Math.max(base, 26000))
}
</script>

<style scoped>
.hot-rank-list {
  background: #fff;
  border-radius: 10px;
}

.rank-row {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  min-height: 44px;
  padding: 0 12px;
  border-bottom: 1px solid #f2f4f7;
}

.rank-row:last-child {
  border-bottom: 0;
}

.rank-index {
  color: #9aa3af;
  font-size: 14px;
  font-weight: 900;
  text-align: center;
}

.rank-index.top {
  color: #f04438;
}

.rank-title {
  min-width: 0;
  color: #111827;
  font-size: 14px;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rank-heat {
  display: inline-flex;
  gap: 3px;
  align-items: center;
  color: #ff6b35;
  font-size: 11px;
  font-weight: 800;
}
</style>
