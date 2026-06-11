<template>
  <article class="news-item" @click="goToDetail">
    <div class="news-content">
      <div class="news-source">{{ news.author || '今日要闻' }}</div>
      <h3 class="news-title">{{ news.title }}</h3>
      <p class="news-desc">{{ news.description }}</p>
      <div class="news-info">
        <span>{{ news.publishTime }}</span>
        <span class="dot"></span>
        <span>{{ news.views }} 阅读</span>
      </div>
    </div>
    <div class="news-image">
      <img :src="imageUrl" :alt="news.title">
    </div>
  </article>
</template>

<script setup>
import { computed, defineProps } from 'vue'
import { useRouter } from 'vue-router'
import { resolveNewsImage } from '../utils/newsMedia'

const props = defineProps({
  news: {
    type: Object,
    required: true
  }
})

const router = useRouter()
const imageUrl = computed(() => resolveNewsImage(props.news))

const goToDetail = () => {
  router.push(`/news/detail/${props.news.id}`)
}
</script>

<style scoped>
.news-item {
  position: relative;
  display: flex;
  gap: 14px;
  margin: 10px 0;
  padding: 14px;
  background: var(--card-color);
  border: 1px solid color-mix(in srgb, var(--border-color) 86%, transparent);
  border-radius: 20px;
  box-shadow: 0 10px 28px var(--shadow-color);
  overflow: hidden;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.news-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 16px;
  width: 3px;
  height: 38px;
  border-radius: 999px;
  background: var(--primary-color);
  opacity: 0.82;
}

.news-item:active {
  transform: scale(0.985);
  box-shadow: 0 5px 18px var(--shadow-color);
}

.news-content {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.news-source {
  margin-bottom: 5px;
  color: var(--primary-color);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.news-title {
  margin: 0 0 7px;
  color: var(--text-color);
  font-size: 16px;
  font-weight: 800;
  line-height: 1.38;
  letter-spacing: -0.02em;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.news-desc {
  margin: 0 0 10px;
  color: var(--text-color-light);
  font-size: 13px;
  line-height: 1.45;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.news-info {
  display: flex;
  align-items: center;
  color: var(--text-color-lighter);
  font-size: 11px;
  line-height: 1;
}

.news-info span {
  flex-shrink: 0;
}

.news-info .dot {
  width: 4px;
  height: 4px;
  margin: 0 7px;
  border-radius: 50%;
  background: var(--text-color-lighter);
  opacity: 0.55;
}

.news-image {
  width: 112px;
  height: 86px;
  flex-shrink: 0;
  border-radius: var(--image-radius);
  background: var(--secondary-color);
  overflow: hidden;
}

.news-image img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  transition: transform 0.24s ease;
}

.news-item:active .news-image img {
  transform: scale(1.04);
}
</style>
