<template>
  <div class="home">
    <van-nav-bar :title="$t('home.title')" fixed />

    <div class="more-options">
      <div class="more-tab" @click="goToCategory">
        {{ $t('home.more') }} <van-icon name="arrow" />
      </div>
    </div>

    <div class="home-hero">
      <span class="hero-kicker">TODAY</span>
      <strong>{{ getCategoryTranslation(displayCategories[activeTab]?.name || '头条') }}</strong>
      <span>精选要闻，快速浏览</span>
    </div>

    <div class="category-tabs">
      <van-tabs v-model:active="activeTab" sticky swipeable animated>
        <van-tab
          v-for="(category, index) in displayCategories"
          :key="category.id"
          :title="getCategoryTranslation(category.name)"
        >
          <van-pull-refresh v-if="index === activeTab" v-model="newsStore.refreshing" @refresh="onRefresh">
            <van-list
              v-model:loading="newsStore.loading"
              :finished="newsStore.finished"
              :finished-text="$t('home.noMore')"
              @load="onLoad"
            >
              <news-item
                v-for="item in newsStore.newsList"
                :key="item.id"
                :news="item"
              />
            </van-list>
          </van-pull-refresh>
        </van-tab>
      </van-tabs>
    </div>

    <tab-bar />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, onActivated, onDeactivated, onBeforeUnmount, nextTick } from 'vue'
import { useNewsStore } from '../store/modules/news'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import NewsItem from '../components/NewsItem.vue'
import TabBar from '../components/TabBar.vue'

const newsStore = useNewsStore()
const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const activeTab = ref(0)
const tabsTop = ref(0)
const moreTop = computed(() => `${tabsTop.value + 7}px`)
let scrollListening = false

const displayCategories = computed(() => {
  return newsStore.categories.filter(category => category.name !== '更多')
})

const getCategoryTranslation = (categoryName) => {
  const categoryMap = {
    '头条': 'headline',
    '社会': 'society',
    '国内': 'domestic',
    '国际': 'international',
    '娱乐': 'entertainment',
    '体育': 'sports',
    '军事': 'military',
    '科技': 'technology',
    '财经': 'finance',
    '更多': 'more'
  }

  const key = categoryMap[categoryName]
  return key ? t(`home.categories.${key}`) : categoryName
}

const goToCategory = () => {
  router.push('/category')
}

const updateTabsPosition = () => {
  const tabsElement = document.querySelector('.van-tabs__wrap')
  if (tabsElement) {
    tabsTop.value = tabsElement.getBoundingClientRect().top
  }
}

const handleScroll = () => {
  updateTabsPosition()
}

const addScrollListener = () => {
  if (scrollListening) return
  window.addEventListener('scroll', handleScroll)
  scrollListening = true
}

const removeScrollListener = () => {
  if (!scrollListening) return
  window.removeEventListener('scroll', handleScroll)
  scrollListening = false
}

const syncActiveTabFromCategory = (categoryId) => {
  const index = displayCategories.value.findIndex(cat => cat.id === categoryId)
  if (index === -1) return false

  if (activeTab.value !== index) {
    activeTab.value = index
    return true
  }

  return false
}

watch(
  () => route.query.categoryId,
  (newCategoryId) => {
    if (!newCategoryId) return

    const categoryId = Number(newCategoryId)
    const tabChanged = syncActiveTabFromCategory(categoryId)
    if (!tabChanged) {
      newsStore.changeCategory(categoryId)
    }
  }
)

watch(activeTab, (newVal) => {
  const category = displayCategories.value[newVal]
  if (!category) return

  newsStore.changeCategory(category.id)
})

onMounted(async () => {
  await newsStore.getCategories()

  const categoryId = route.query.categoryId ? Number(route.query.categoryId) : newsStore.currentCategory
  const tabChanged = syncActiveTabFromCategory(categoryId)
  if (!tabChanged) {
    await newsStore.changeCategory(categoryId)
  }

  await nextTick()
  updateTabsPosition()
})

onActivated(() => {
  addScrollListener()
  nextTick(updateTabsPosition)
})

onDeactivated(() => {
  removeScrollListener()
})

onBeforeUnmount(() => {
  removeScrollListener()
})

const onRefresh = () => {
  newsStore.getNewsList(true)
}

const onLoad = () => {
  newsStore.getNewsList()
}
</script>

<style scoped>
.home {
  padding-top: 46px;
  padding-bottom: calc(58px + var(--safe-area-inset-bottom));
  background: var(--page-gradient);
  min-height: 100vh;
}

.home::before {
  content: '';
  position: fixed;
  top: 0;
  left: 50%;
  width: min(750px, 100vw);
  height: 210px;
  pointer-events: none;
  transform: translateX(-50%);
  background: radial-gradient(circle at 18% 18%, var(--primary-color-soft), transparent 36%),
    radial-gradient(circle at 85% 8%, rgba(255, 184, 77, 0.16), transparent 28%);
}

.home-hero {
  position: relative;
  margin: 12px 16px 10px;
  padding: 18px 18px 16px;
  color: var(--text-color);
  background: linear-gradient(135deg, var(--card-color), var(--secondary-color));
  border: 1px solid color-mix(in srgb, var(--border-color) 78%, transparent);
  border-radius: 22px;
  box-shadow: 0 12px 32px var(--shadow-color);
  overflow: hidden;
}

.home-hero::after {
  content: '';
  position: absolute;
  right: -28px;
  top: -34px;
  width: 110px;
  height: 110px;
  border-radius: 50%;
  background: var(--primary-color-soft);
}

.home-hero strong,
.home-hero span {
  position: relative;
  z-index: 1;
  display: block;
}

.hero-kicker {
  margin-bottom: 4px;
  color: var(--primary-color);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.18em;
}

.home-hero strong {
  font-size: 24px;
  line-height: 1.15;
  letter-spacing: -0.03em;
}

.home-hero span:last-child {
  margin-top: 6px;
  color: var(--text-color-light);
  font-size: 13px;
}

.category-tabs {
  position: relative;
  margin-bottom: 10px;
}

:deep(.van-nav-bar) {
  background: var(--nav-color);
  backdrop-filter: blur(18px);
  box-shadow: 0 8px 24px var(--shadow-color);
}

:deep(.van-nav-bar__title) {
  color: var(--text-color);
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

:deep(.van-tabs__wrap) {
  height: 48px;
  padding-right: 70px;
  background: var(--nav-color);
  backdrop-filter: blur(16px);
  box-shadow: 0 8px 22px var(--shadow-color);
}

:deep(.van-tabs__nav) {
  background: transparent;
}

:deep(.van-tab) {
  color: var(--text-color-light);
  font-size: 14px;
  font-weight: 600;
}

:deep(.van-tab--active) {
  color: var(--primary-color);
  font-weight: 800;
}

:deep(.van-tabs__line) {
  bottom: 8px;
  width: 18px;
  height: 4px;
  border-radius: 999px;
  background: var(--primary-color);
}

:deep(.van-list) {
  padding: 2px 12px 8px;
}

:deep(.van-list__finished-text),
:deep(.van-list__loading) {
  color: var(--text-color-lighter);
}

.more-options {
  position: fixed;
  right: 10px;
  z-index: 1000;
  top: v-bind(moreTop);
  display: flex;
  align-items: center;
}

.more-tab {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 34px;
  padding: 0 10px 0 12px;
  color: var(--primary-color);
  font-size: 13px;
  font-weight: 800;
  background: var(--card-color);
  border: 1px solid var(--border-color);
  border-radius: 999px;
  box-shadow: 0 8px 22px var(--shadow-color);
  cursor: pointer;
}
</style>
