<template>
  <div class="hot-page">
    <header class="hot-header">
      <van-icon name="arrow-left" @click="router.back()" />
      <strong>头条热榜</strong>
      <van-icon name="search" @click="router.push('/search')" />
    </header>

    <div class="hot-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        :class="{ active: activeTab === tab.id }"
        @click="changeTab(tab.id)"
      >
        {{ tab.name }}
      </button>
    </div>

    <section class="rank-card">
      <div class="rank-title">
        <span>{{ activeTabName }}</span>
        <small>{{ loading ? '更新中...' : '实时更新' }}</small>
      </div>
      <hot-rank-list :items="rankItems" @select="goToDetail" />
    </section>

    <van-empty v-if="!loading && !rankItems.length" description="暂无热榜内容" />

    <tab-bar />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import HotRankList from '../components/HotRankList.vue'
import TabBar from '../components/TabBar.vue'
import { fetchHotNews } from '../services/newsService'
import { normalizeNewsItem } from '../utils/newsFormat'

const router = useRouter()
const activeTab = ref('hot')
const allItems = ref([])
const loading = ref(false)

const tabs = [
  { id: 'hot', name: '热榜' },
  { id: 'society', name: '社会' },
  { id: 'tech', name: '科技' },
  { id: 'entertainment', name: '娱乐' },
  { id: 'sports', name: '体育' },
  { id: 'finance', name: '财经' }
]

// hot 标签不传 categoryId，即全库热榜；其余标签为对应分类热榜
const categoryByTab = {
  society: 2,
  tech: 8,
  entertainment: 5,
  sports: 6,
  finance: 9
}

const activeTabName = computed(() => tabs.find((tab) => tab.id === activeTab.value)?.name || '热榜')

const rankItems = computed(() => allItems.value)

const loadRank = async () => {
  loading.value = true
  try {
    const result = await fetchHotNews({
      categoryId: categoryByTab[activeTab.value],
      page: 1,
      pageSize: 10
    })
    allItems.value = result.list.map(normalizeNewsItem)
  } finally {
    loading.value = false
  }
}

const changeTab = async (tabId) => {
  activeTab.value = tabId
  await loadRank()
}

const goToDetail = (item) => {
  router.push(`/news/detail/${item.id}`)
}

onMounted(loadRank)
</script>

<style scoped>
.hot-page {
  min-height: 100vh;
  padding-bottom: calc(70px + var(--safe-area-inset-bottom));
  background: #f7f8fa;
}

.hot-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 16px;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(18px);
}

.hot-header strong {
  color: #111827;
  font-size: 17px;
  font-weight: 900;
}

.hot-header .van-icon {
  color: #111827;
  font-size: 20px;
}

.hot-tabs {
  display: flex;
  gap: 18px;
  padding: 10px 16px 8px;
  overflow-x: auto;
  background: #fff;
  scrollbar-width: none;
}

.hot-tabs::-webkit-scrollbar {
  display: none;
}

.hot-tabs button {
  flex: 0 0 auto;
  padding: 0;
  color: #4b5563;
  font-size: 15px;
  font-weight: 800;
  background: transparent;
  border: 0;
}

.hot-tabs button.active {
  color: #f04438;
}

.rank-card {
  margin: 12px;
  overflow: hidden;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 10px 24px rgba(17, 24, 39, 0.05);
}

.rank-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 12px 8px;
}

.rank-title span {
  color: #f04438;
  font-size: 16px;
  font-weight: 900;
}

.rank-title small {
  color: #9aa3af;
  font-size: 12px;
}
</style>
