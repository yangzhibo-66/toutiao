<template>
  <div class="my-news-page">
    <van-nav-bar title="已发布新闻" left-arrow fixed @click-left="router.back()" />

    <main class="my-news-content">
      <section class="summary-card">
        <div>
          <span>已发布</span>
          <strong>{{ total }}</strong>
          <p>管理自己发布的新闻内容</p>
        </div>
        <van-button size="small" round type="primary" icon="plus" @click="router.push('/publish')">
          发布新闻
        </van-button>
      </section>

      <van-pull-refresh v-model="refreshing" @refresh="loadMyNews">
        <van-list
          v-model:loading="loading"
          :finished="finished"
          :immediate-check="false"
          finished-text="没有更多了"
          @load="loadMyNews"
        >
          <article v-for="item in newsList" :key="item.id" class="news-card">
            <div class="news-main">
              <div class="news-copy">
                <div class="news-category">{{ categoryName(item.categoryId) }}</div>
                <h3>{{ item.title }}</h3>
                <p>{{ item.description || item.content }}</p>
                <div class="news-meta">
                  <span>{{ item.author || userStore.userInfo?.username || '我' }}</span>
                  <span>{{ formatPublishTime(item.publishTime) }}</span>
                  <span>{{ formatCount(item.views) }}阅读</span>
                </div>
              </div>
              <img :src="resolveNewsImage(item)" :alt="item.title">
            </div>

            <div class="news-actions">
              <button type="button" @click="router.push(`/news/detail/${item.id}`)">查看</button>
              <button type="button" @click="router.push(`/publish?id=${item.id}`)">编辑</button>
              <button type="button" class="danger" @click="confirmDelete(item)">删除</button>
            </div>
          </article>
        </van-list>

        <van-empty v-if="!loading && !newsList.length" description="还没有发布新闻">
          <van-button round type="primary" @click="router.push('/publish')">去发布</van-button>
        </van-empty>
      </van-pull-refresh>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showFailToast, showSuccessToast, showToast } from 'vant'
import { deleteNews, fetchCategories, fetchMyNews } from '../services/newsService'
import { useUserStore } from '../store/user'
import { formatCount, formatPublishTime, normalizeNewsItem } from '../utils/newsFormat'
import { resolveNewsImage } from '../utils/newsMedia'

const PAGE_SIZE = 20

const router = useRouter()
const userStore = useUserStore()
const newsList = ref([])
const categories = ref([])
const page = ref(1)
const total = ref(0)
const loading = ref(false)
const refreshing = ref(false)
const finished = ref(false)

const categoryMap = computed(() => new Map(categories.value.map((item) => [item.id, item.name])))

const categoryName = (categoryId) => categoryMap.value.get(categoryId) || '未分类'

const getErrorMessage = (error) =>
  error.response?.data?.detail || error.response?.data?.message || '操作失败，请稍后再试'

const ensureLogin = () => {
  if (userStore.getLoginStatus) return true
  showToast('请先登录')
  router.replace('/login')
  return false
}

const loadCategories = async () => {
  categories.value = await fetchCategories()
}

const loadMyNews = async () => {
  if (!ensureLogin() || loading.value) return

  loading.value = true
  try {
    const currentPage = refreshing.value ? 1 : page.value
    const data = await fetchMyNews({
      page: currentPage,
      pageSize: PAGE_SIZE
    })
    const items = (data.list || []).map(normalizeNewsItem)

    if (refreshing.value || currentPage === 1) {
      newsList.value = items
      page.value = 2
    } else {
      newsList.value = [...newsList.value, ...items]
      page.value += 1
    }

    total.value = data.total || newsList.value.length
    finished.value = !data.hasMore
  } catch (error) {
    console.error('获取已发布新闻失败:', error)
    showFailToast(getErrorMessage(error))
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

const confirmDelete = async (item) => {
  try {
    await showConfirmDialog({
      title: '删除新闻',
      message: `确定删除《${item.title}》吗？删除后无法恢复。`
    })
    const response = await deleteNews(item.id)
    if (response?.code === 200) {
      newsList.value = newsList.value.filter((news) => news.id !== item.id)
      total.value = Math.max(0, total.value - 1)
      showSuccessToast('新闻已删除')
    } else {
      showFailToast(response?.message || '删除失败')
    }
  } catch (error) {
    if (error === 'cancel') return
    console.error('删除新闻失败:', error)
    showFailToast(getErrorMessage(error))
  }
}

onMounted(async () => {
  if (!ensureLogin()) return
  await loadCategories()
  await loadMyNews()
})
</script>

<style scoped>
.my-news-page {
  min-height: 100vh;
  background: #f6f7f9;
}

.my-news-content {
  padding: 58px 12px 24px;
}

.summary-card,
.news-card {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 10px 24px rgba(17, 24, 39, 0.04);
}

.summary-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 16px;
}

.summary-card span {
  color: #f04438;
  font-size: 12px;
  font-weight: 900;
}

.summary-card strong {
  display: block;
  margin: 4px 0;
  color: #111827;
  font-size: 28px;
  font-weight: 900;
}

.summary-card p {
  margin: 0;
  color: #8a93a3;
  font-size: 13px;
}

.news-card {
  margin-bottom: 10px;
  padding: 12px;
}

.news-main {
  display: flex;
  gap: 12px;
}

.news-copy {
  flex: 1;
  min-width: 0;
}

.news-category {
  display: inline-flex;
  margin-bottom: 6px;
  padding: 2px 6px;
  color: #f04438;
  font-size: 11px;
  font-weight: 900;
  background: #fff1f0;
  border-radius: 999px;
}

.news-copy h3 {
  margin: 0 0 6px;
  color: #111827;
  font-size: 16px;
  font-weight: 900;
  line-height: 1.35;
}

.news-copy p {
  margin: 0 0 8px;
  color: #667085;
  font-size: 13px;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.news-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  color: #9aa3af;
  font-size: 12px;
}

.news-main img {
  flex: 0 0 96px;
  width: 96px;
  height: 72px;
  object-fit: cover;
  background: #eef2f7;
  border-radius: 6px;
}

.news-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #f1f3f5;
}

.news-actions button {
  height: 30px;
  padding: 0 12px;
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 800;
  background: #eff6ff;
  border: 0;
  border-radius: 999px;
}

.news-actions .danger {
  color: #f04438;
  background: #fff1f0;
}
</style>

