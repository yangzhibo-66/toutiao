<template>
  <article
    class="news-feed-card"
    :class="{ featured }"
    @click="$emit('select', news)"
  >
    <div v-if="featured" class="featured-image">
      <img :src="imageUrl" :alt="news.title">
      <div class="featured-mask"></div>
      <div class="featured-title">{{ news.title }}</div>
    </div>

    <template v-else>
      <div class="feed-copy">
        <h3>{{ news.title }}</h3>
        <p>{{ news.description }}</p>
        <div class="feed-meta">
          <span>{{ news.author || '头条新闻' }}</span>
          <span>{{ formatCount(news.views) }}评论</span>
          <span>{{ formatPublishTime(news.publishTime) }}</span>
        </div>
      </div>
      <div class="feed-thumb">
        <img :src="imageUrl" :alt="news.title">
      </div>
    </template>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { resolveNewsImage } from '../utils/newsMedia'
import { formatCount, formatPublishTime } from '../utils/newsFormat'

const props = defineProps({
  news: {
    type: Object,
    required: true
  },
  featured: {
    type: Boolean,
    default: false
  }
})

defineEmits(['select'])

const imageUrl = computed(() => resolveNewsImage(props.news))
</script>

<style scoped>
.news-feed-card {
  display: flex;
  gap: 12px;
  padding: 12px 14px;
  background: #fff;
  border-bottom: 1px solid #f1f3f5;
}

.news-feed-card:active {
  background: #f8fafc;
}

.feed-copy {
  flex: 1;
  min-width: 0;
}

.feed-copy h3 {
  margin: 0 0 7px;
  color: #111827;
  font-size: 16px;
  font-weight: 800;
  line-height: 1.42;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.feed-copy p {
  margin: 0 0 8px;
  color: #5f6673;
  font-size: 13px;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.feed-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  color: #9aa3af;
  font-size: 12px;
}

.feed-thumb {
  flex: 0 0 112px;
  width: 112px;
  height: 78px;
  overflow: hidden;
  background: #eef2f7;
  border-radius: 6px;
}

.feed-thumb img,
.featured-image img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.news-feed-card.featured {
  display: block;
  padding: 0 14px 12px;
  border-bottom: 0;
}

.featured-image {
  position: relative;
  height: 150px;
  overflow: hidden;
  border-radius: 6px;
  background: #101828;
}

.featured-mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.05), rgba(0, 0, 0, 0.72));
}

.featured-title {
  position: absolute;
  left: 14px;
  right: 14px;
  bottom: 14px;
  color: #fff;
  font-size: 18px;
  font-weight: 900;
  line-height: 1.35;
}
</style>
