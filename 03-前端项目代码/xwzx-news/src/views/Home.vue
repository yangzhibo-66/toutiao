<template>
  <div class="home-page">
    <app-search-header v-model="keyword" @search="applySearch" @publish="showPublishTip" />

    <div class="channel-strip">
      <button v-for="(category, index) in displayCategories" :key="category.id" type="button" :class="['channel-tab', { active: activeTab === index }]" @click="switchCategory(index)">
        {{ displayCategoryName(category) }}
      </button>
      <button type="button" class="channel-more" @click="goToCategory">更多 <van-icon name="arrow-down" /></button>
    </div>

    <main class="home-content">
      <news-feed-card v-if="featuredNews" :news="featuredNews" featured @select="goToDetail" />

      <section v-if="recommendItems.length" class="recommend-section">
        <div class="section-head"><strong>为你推荐</strong><span>根据当前频道精选</span></div>
        <div class="recommend-scroll">
          <article v-for="item in recommendItems" :key="item.id" class="recommend-card" @click="goToDetail(item)">
            <img :src="resolveNewsImage(item)" :alt="item.title">
            <p>{{ item.title }}</p>
            <span>{{ formatCount(item.views) }}阅读</span>
          </article>
        </div>
      </section>

      <van-pull-refresh v-model="newsStore.refreshing" @refresh="onRefresh">
        <van-list v-model:loading="newsStore.loading" :finished="newsStore.finished" finished-text="没有更多了" @load="onLoad">
          <news-feed-card v-for="item in visibleNews" :key="item.id" :news="item" @select="goToDetail" />
        </van-list>
      </van-pull-refresh>

      <van-empty v-if="!newsStore.loading && !visibleNews.length" description="没有找到相关新闻" />
    </main>

    <button type="button" class="ai-fab" @click="router.push('/aichat')"><van-icon name="chat-o" />AI助手</button>
    <tab-bar />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppSearchHeader from '../components/AppSearchHeader.vue'
import NewsFeedCard from '../components/NewsFeedCard.vue'
import TabBar from '../components/TabBar.vue'
import { useNewsStore } from '../store/modules/news'
import { displayCategoryName, formatCount, matchesKeyword } from '../utils/newsFormat'
import { resolveNewsImage } from '../utils/newsMedia'

const newsStore = useNewsStore()
const router = useRouter()
const route = useRoute()
const activeTab = ref(0)
const keyword = ref('')
const appliedKeyword = ref('')

const displayCategories = computed(() => {
  const source = newsStore.categories.filter((category) => category.name !== '更多')
  return source.length ? source : [
    { id: 1, name: '推荐' },
    { id: 2, name: '热榜' },
    { id: 3, name: '关注' },
    { id: 4, name: '北京' },
    { id: 6, name: '体育' },
    { id: 8, name: '科技' },
    { id: 9, name: '财经' }
  ]
})

const normalizedNews = computed(() => newsStore.newsList)
const featuredNews = computed(() => {
  const filtered = normalizedNews.value.filter((item) => matchesKeyword(item, appliedKeyword.value))
  return filtered[0] || normalizedNews.value[0]
})
const visibleNews = computed(() => normalizedNews.value.filter((item) => item.id !== featuredNews.value?.id).filter((item) => matchesKeyword(item, appliedKeyword.value)))
const recommendItems = computed(() => normalizedNews.value.filter((item) => item.id !== featuredNews.value?.id).slice(0, 6))

// 搜索跳转到独立搜索页：后端全库检索，而不是只过滤当前已加载的新闻
const applySearch = () => {
  const kw = keyword.value.trim()
  if (!kw) return
  router.push({ path: '/search', query: { keyword: kw } })
}
const showPublishTip = () => { router.push('/publish') }
const goToCategory = () => { router.push('/category') }
const goToDetail = (item) => { router.push(`/news/detail/${item.id}`) }
const syncActiveTabFromCategory = (categoryId) => {
  const index = displayCategories.value.findIndex((item) => item.id === categoryId)
  if (index >= 0) activeTab.value = index
}
const switchCategory = async (index) => {
  const category = displayCategories.value[index]
  if (!category) return
  activeTab.value = index
  appliedKeyword.value = ''
  keyword.value = ''
  await newsStore.changeCategory(category.id)
  await nextTick()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
const onRefresh = () => { newsStore.getNewsList(true) }
const onLoad = () => { newsStore.getNewsList() }

watch(() => route.query.categoryId, (value) => {
  if (!value) return
  const categoryId = Number(value)
  syncActiveTabFromCategory(categoryId)
  newsStore.changeCategory(categoryId)
})

onMounted(async () => {
  await newsStore.getCategories()
  const categoryId = route.query.categoryId ? Number(route.query.categoryId) : newsStore.currentCategory
  syncActiveTabFromCategory(categoryId)
  await newsStore.changeCategory(categoryId)
})
</script>

<style scoped>
.home-page { min-height: 100vh; padding-bottom: calc(70px + var(--safe-area-inset-bottom)); background: #fff; }
.channel-strip { position: sticky; top: 58px; z-index: 18; display: flex; gap: 20px; align-items: center; padding: 4px 14px 8px; overflow-x: auto; background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(18px); scrollbar-width: none; }
.channel-strip::-webkit-scrollbar { display: none; }
.channel-tab, .channel-more { position: relative; flex: 0 0 auto; padding: 0; color: #1f2937; font-size: 15px; font-weight: 800; background: transparent; border: 0; }
.channel-tab.active { color: #f04438; }
.channel-tab.active::after { content: ''; position: absolute; left: 50%; bottom: -8px; width: 16px; height: 3px; border-radius: 999px; background: #f04438; transform: translateX(-50%); }
.channel-more { display: inline-flex; gap: 3px; align-items: center; }
.home-content { padding-top: 8px; }
.recommend-section { padding: 14px 0 12px; border-top: 8px solid #f5f6f8; border-bottom: 8px solid #f5f6f8; }
.section-head { display: flex; align-items: baseline; justify-content: space-between; padding: 0 14px 10px; }
.section-head strong { color: #111827; font-size: 15px; font-weight: 900; }
.section-head span { color: #9aa3af; font-size: 12px; }
.recommend-scroll { display: flex; gap: 8px; padding: 0 14px; overflow-x: auto; scrollbar-width: none; }
.recommend-scroll::-webkit-scrollbar { display: none; }
.recommend-card { flex: 0 0 132px; }
.recommend-card img { display: block; width: 132px; height: 74px; object-fit: cover; border-radius: 6px; background: #eef2f7; }
.recommend-card p { margin: 7px 0 3px; color: #111827; font-size: 12px; font-weight: 700; line-height: 1.35; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; line-clamp: 2; overflow: hidden; }
.recommend-card span { color: #9aa3af; font-size: 11px; }
.ai-fab { position: fixed; right: 16px; bottom: calc(82px + var(--safe-area-inset-bottom)); z-index: 25; display: inline-flex; gap: 5px; align-items: center; height: 38px; padding: 0 12px; color: #fff; font-size: 13px; font-weight: 900; background: #2f6bff; border: 0; border-radius: 999px; box-shadow: 0 12px 28px rgba(47, 107, 255, 0.28); }
:deep(.van-list__finished-text), :deep(.van-list__loading) { color: #9aa3af; }
</style>
