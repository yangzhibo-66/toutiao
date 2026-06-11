<template>
  <div class="news-detail">
    <van-nav-bar
      title="新闻详情"
      left-text="返回"
      left-arrow
      fixed
      @click-left="onClickLeft"
    />

    <div v-if="newsStore.newsDetail.id" class="detail-content">
      <div class="title-container">
        <h1 class="title">{{ newsStore.newsDetail.title }}</h1>
        <van-button
          class="favorite-btn"
          :icon="isFavorite ? 'star' : 'star-o'"
          :class="{ 'is-favorite': isFavorite }"
          @click="toggleFavorite"
        />
      </div>

      <div class="info">
        <span>{{ newsStore.newsDetail.author || '新闻聚合' }}</span>
        <span>{{ newsStore.newsDetail.publishTime }}</span>
        <span>{{ newsStore.newsDetail.views }} 阅读</span>
      </div>

      <div class="cover">
        <img :src="coverImage" :alt="newsStore.newsDetail.title">
      </div>

      <div v-if="hasRealContent" class="content-card">
        <div class="content">
          <p
            v-for="(paragraph, index) in contentParagraphs"
            :key="index"
            :class="{ lead: index === 0 && paragraph.length >= 40 }"
          >
            {{ paragraph }}
          </p>
        </div>
      </div>

      <div v-else class="summary-tip">
        暂未整理出适合阅读的正文排版，请点击下方按钮查看原文。
      </div>

      <div v-if="newsStore.newsDetail.sourceUrl" class="source-link">
        <a :href="newsStore.newsDetail.sourceUrl" target="_blank" rel="noopener noreferrer">查看原文</a>
      </div>

      <div v-if="newsStore.newsDetail.relatedNews?.length" class="related-news">
        <h3>相关推荐</h3>
        <div class="related-list">
          <div
            v-for="item in newsStore.newsDetail.relatedNews"
            :key="item.id"
            class="related-item"
            @click="goToRelatedNews(item.id)"
          >
            <div class="related-image">
              <img :src="resolveNewsImage(item)" :alt="item.title">
            </div>
            <div class="related-title">{{ item.title }}</div>
          </div>
        </div>
      </div>
    </div>

    <van-empty v-else description="加载中..." />
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useFavoriteStore } from '../store/modules/favorite'
import { useHistoryStore } from '../store/modules/history'
import { useNewsStore } from '../store/modules/news'
import { useUserStore } from '../store/user'
import { resolveNewsImage } from '../utils/newsMedia'

const route = useRoute()
const router = useRouter()
const newsStore = useNewsStore()
const historyStore = useHistoryStore()
const favoriteStore = useFavoriteStore()
const userStore = useUserStore()

const newsId = computed(() => Number(route.params.id))
const coverImage = computed(() => resolveNewsImage(newsStore.newsDetail))

const normalizeText = (value) => String(value || '')
  .replace(/\s+/g, '')
  .replace(/[：:|｜\-—_、，。！？“”"'‘’（）()【】\[\]]/g, '')
  .trim()

const stripSourceSuffix = (value) => String(value || '')
  .replace(/\s*[-|｜—_]\s*[^-|｜—_]+$/, '')
  .trim()

const splitLongParagraph = (paragraph) => {
  const text = String(paragraph || '').trim()
  if (!text) return []
  if (text.length <= 110) return [text]

  const parts = text.match(/[^。！？!?]+[。！？!?]?/g) || [text]
  const chunks = []
  let buffer = ''

  parts.forEach((part) => {
    const sentence = part.trim()
    if (!sentence) return

    if (!buffer) {
      buffer = sentence
      return
    }

    if ((buffer + sentence).length > 110) {
      chunks.push(buffer.trim())
      buffer = sentence
      return
    }

    buffer += sentence
  })

  if (buffer) {
    chunks.push(buffer.trim())
  }

  return chunks.filter(Boolean)
}

const contentParagraphs = computed(() => {
  const rawContent = String(newsStore.newsDetail.content || '').trim()
  const title = String(newsStore.newsDetail.title || '').trim()
  const description = String(newsStore.newsDetail.description || '').trim()
  const normalizedTitle = normalizeText(title)
  const normalizedShortTitle = normalizeText(stripSourceSuffix(title))
  const normalizedDescription = normalizeText(description)

  if (!rawContent) return []

  return rawContent
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean)
    .filter((item) => !/^来源[:：]/i.test(item))
    .flatMap(splitLongParagraph)
    .filter((item) => {
      const normalized = normalizeText(item)
      if (!normalized) return false
      if (normalized === normalizedTitle || normalized === normalizedShortTitle) return false
      if (normalizedDescription && normalized === normalizedDescription) return false
      if (normalizedShortTitle && normalized.includes(normalizedShortTitle) && normalized.length < 180) return false
      return true
    })
})

const hasRealContent = computed(() => {
  if (!contentParagraphs.value.length) return false

  const merged = contentParagraphs.value.join('\n\n').trim()
  const mergedLength = normalizeText(merged).length
  const sentenceCount = (merged.match(/[。！？!?]/g) || []).length

  if (mergedLength < 180) return false
  if (contentParagraphs.value.length === 1) {
    return mergedLength >= 220 && sentenceCount >= 4
  }
  return sentenceCount >= 3 || mergedLength >= 260
})

const onClickLeft = () => {
  router.back()
}

const goToRelatedNews = (id) => {
  router.push(`/news/detail/${id}`)
}

const isFavorite = computed(() => favoriteStore.isFavorite(newsId.value))

const toggleFavorite = async () => {
  if (!userStore.getLoginStatus) {
    showToast({
      message: '请先登录后再收藏',
      position: 'bottom'
    })
    router.push('/login')
    return
  }

  const status = await favoriteStore.toggleFavorite(newsStore.newsDetail)
  if (status === true) {
    showToast({ message: '已添加到收藏', position: 'bottom' })
  } else if (status === false) {
    showToast({ message: '已取消收藏', position: 'bottom' })
  } else {
    showToast({ message: '操作失败，请稍后重试', position: 'bottom' })
  }
}

const syncFavoriteStatus = async (detail) => {
  const result = await favoriteStore.checkFavoriteStatusApi(detail.id)
  if (result.success && !result.isLocal) {
    if (result.isFavorite && !favoriteStore.isFavorite(detail.id)) {
      favoriteStore.addFavorite(detail)
    } else if (!result.isFavorite && favoriteStore.isFavorite(detail.id)) {
      favoriteStore.removeFavorite(detail.id)
    }
  }
}

const loadNewsDetail = async (id) => {
  await newsStore.getNewsDetail(id)
  if (!newsStore.newsDetail.id) return

  favoriteStore.loadFavorites()
  if (userStore.getLoginStatus) {
    const detail = { ...newsStore.newsDetail }
    historyStore.addHistoryApi(detail.id).catch((error) => {
      console.error('记录浏览历史 API 失败:', error)
    })
    syncFavoriteStatus(detail).catch((error) => {
      console.error('检查收藏状态失败:', error)
    })
  }
}

onMounted(() => loadNewsDetail(newsId.value))
watch(newsId, (newId) => {
  loadNewsDetail(newId)
})
</script>

<style scoped>
.news-detail {
  min-height: 100vh;
  padding-top: 46px;
  background: linear-gradient(180deg, #f7f9fc 0%, #ffffff 180px);
}

.detail-content {
  padding: 16px;
}

.title-container {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
}

.title {
  flex: 1;
  margin: 0;
  color: #1f2937;
  font-size: 24px;
  font-weight: 800;
  line-height: 1.45;
  letter-spacing: -0.02em;
}

.favorite-btn {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  margin-left: 10px;
  padding: 0;
  border-radius: 50%;
}

.favorite-btn.is-favorite {
  color: #ff9500;
}

.info {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
  color: #6b7280;
  font-size: 12px;
}

.cover {
  margin-bottom: 18px;
}

.cover img {
  display: block;
  width: 100%;
  max-height: 240px;
  object-fit: cover;
  border-radius: 16px;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.08);
}

.content-card {
  margin-bottom: 18px;
  padding: 18px 16px;
  background: #ffffff;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 18px;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
}

.content {
  color: #263238;
  font-size: 17px;
  line-height: 2;
  word-break: break-word;
}

.content p {
  margin: 0 0 18px;
  text-align: justify;
  text-indent: 2em;
}

.content p:last-child {
  margin-bottom: 0;
}

.content p.lead {
  color: #334155;
  font-size: 18px;
}

.summary-tip {
  margin-bottom: 16px;
  padding: 14px 16px;
  color: #8a5a00;
  font-size: 14px;
  line-height: 1.7;
  background: #fff7e6;
  border-radius: 12px;
}

.source-link {
  margin-bottom: 20px;
}

.source-link a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 112px;
  height: 40px;
  padding: 0 18px;
  color: #1677ff;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  background: rgba(22, 119, 255, 0.08);
  border-radius: 999px;
}

.related-news {
  margin-top: 28px;
  padding-top: 18px;
  border-top: 8px solid #f3f4f6;
}

.related-news h3 {
  margin: 0 0 16px;
  color: #1f2937;
  font-size: 18px;
}

.related-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.related-item {
  display: flex;
  align-items: center;
}

.related-image {
  flex-shrink: 0;
  width: 80px;
  height: 60px;
  margin-right: 12px;
}

.related-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
}

.related-title {
  flex: 1;
  color: #334155;
  font-size: 14px;
  line-height: 1.5;
}
</style>
