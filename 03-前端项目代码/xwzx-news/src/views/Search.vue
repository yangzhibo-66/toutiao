<template>
  <div class="search-page">
    <header class="search-header">
      <van-icon name="arrow-left" @click="goBack" />
      <div class="search-pill">
        <van-icon name="search" />
        <input
          v-model="keyword"
          type="search"
          placeholder="搜你想看的"
          @keyup.enter="onSearch"
        >
        <button type="button" @click="onSearch">搜索</button>
      </div>
    </header>

    <div v-if="searched" class="result-summary">
      共 {{ total }} 条相关结果
    </div>

    <van-list
      v-model:loading="loading"
      :finished="finished"
      :immediate-check="false"
      finished-text="没有更多了"
      @load="loadMore"
    >
      <div
        v-for="item in results"
        :key="item.id"
        class="result-row"
        @click="goToDetail(item)"
      >
        <div class="result-title">{{ item.title }}</div>
        <div class="result-meta">
          <span>{{ item.author || '新闻聚合' }}</span>
          <span>{{ formatPublishTime(item.publishTime) }}</span>
        </div>
      </div>
    </van-list>

    <van-empty
      v-if="searched && !loading && !results.length"
      description="没有找到相关新闻，换个关键词试试"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { searchNews } from '../services/newsService'
import { formatPublishTime, normalizeNewsItem } from '../utils/newsFormat'

const PAGE_SIZE = 10

const router = useRouter()
const route = useRoute()

const keyword = ref('')
const results = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const finished = ref(true)
const searched = ref(false)

const onSearch = () => {
  const kw = keyword.value.trim()
  if (!kw) return

  results.value = []
  total.value = 0
  page.value = 1
  finished.value = false
  searched.value = true
  loadMore()
}

const loadMore = async () => {
  const kw = keyword.value.trim()
  if (!kw || loading.value) return

  loading.value = true
  try {
    const result = await searchNews({ keyword: kw, page: page.value, pageSize: PAGE_SIZE })
    const items = result.list.map(normalizeNewsItem)

    if (page.value === 1) {
      results.value = items
    } else {
      const existingIds = new Set(results.value.map((item) => item.id))
      results.value = [...results.value, ...items.filter((item) => !existingIds.has(item.id))]
    }

    total.value = result.total
    finished.value = !result.hasMore || items.length === 0
    page.value += 1
  } finally {
    loading.value = false
  }
}

const goToDetail = (item) => {
  router.push(`/news/detail/${item.id}`)
}

const goBack = () => {
  if (window.history.length > 1) router.back()
  else router.replace('/home')
}

onMounted(() => {
  // 支持从其他页面带关键词跳转进来，如 /search?keyword=xxx
  const initialKeyword = typeof route.query.keyword === 'string' ? route.query.keyword.trim() : ''
  if (initialKeyword) {
    keyword.value = initialKeyword
    onSearch()
  }
})
</script>

<style scoped>
.search-page {
  min-height: 100vh;
  padding-bottom: 32px;
  background: #f7f8fa;
}

.search-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  gap: 12px;
  align-items: center;
  height: 52px;
  padding: 0 14px;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(18px);
}

.search-header > .van-icon {
  color: #111827;
  font-size: 20px;
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

.result-summary {
  padding: 12px 16px 4px;
  color: #6b7280;
  font-size: 12px;
}

.result-row {
  margin: 8px 12px;
  padding: 12px 14px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 18px rgba(17, 24, 39, 0.04);
  cursor: pointer;
}

.result-title {
  color: #111827;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-meta {
  display: flex;
  gap: 12px;
  margin-top: 6px;
  color: #9aa3af;
  font-size: 12px;
}
</style>
