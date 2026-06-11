<template>
  <div class="category">
    <van-nav-bar
      :title="$t('common.allCategories')"
      :left-text="$t('common.back')"
      left-arrow
      fixed
      @click-left="onClickLeft"
    />

    <div class="category-hero">
      <span class="hero-tag">DISCOVER</span>
      <h1>浏览全部分类</h1>
      <p>从热点到科技，快速进入你想看的内容频道。</p>
    </div>

    <div class="category-container">
      <van-grid :column-num="2" :border="false" :gutter="12">
        <van-grid-item
          v-for="category in displayCategories"
          :key="category.id"
          class="category-item"
          :text="getCategoryTranslation(category.name)"
          icon="newspaper-o"
          @click="goToCategoryNews(category.id)"
        />
      </van-grid>
    </div>

    <tab-bar />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import TabBar from '../components/TabBar.vue'
import { useNewsStore } from '../store/modules/news'

const newsStore = useNewsStore()
const router = useRouter()
const { t } = useI18n()

const displayCategories = computed(() => {
  return newsStore.categories.filter(category => category.name !== '更多')
})

const onClickLeft = () => {
  router.back()
}

const goToCategoryNews = (categoryId) => {
  router.push({
    path: '/home',
    query: { categoryId }
  })
}

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
</script>

<style scoped>
.category {
  min-height: 100vh;
  padding: 46px 16px calc(72px + var(--safe-area-inset-bottom));
  background: var(--page-gradient);
}

.category-hero {
  position: relative;
  margin: 14px 0 16px;
  padding: 22px 20px 18px;
  color: var(--text-color);
  background: linear-gradient(135deg, var(--card-color), var(--secondary-color));
  border: 1px solid rgba(221, 230, 241, 0.82);
  border-radius: 26px;
  box-shadow: 0 16px 36px var(--shadow-color);
  overflow: hidden;
}

.category-hero::after {
  content: '';
  position: absolute;
  right: -32px;
  top: -42px;
  width: 126px;
  height: 126px;
  border-radius: 50%;
  background: var(--primary-color-soft);
}

.hero-tag,
.category-hero h1,
.category-hero p {
  position: relative;
  z-index: 1;
}

.hero-tag {
  display: inline-block;
  margin-bottom: 8px;
  color: var(--primary-color);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.16em;
}

.category-hero h1 {
  margin: 0 0 8px;
  font-size: 24px;
  line-height: 1.2;
}

.category-hero p {
  margin: 0;
  color: var(--text-color-light);
  font-size: 14px;
  line-height: 1.6;
}

.category-container {
  padding: 14px;
  background: var(--card-color);
  border: 1px solid rgba(221, 230, 241, 0.82);
  border-radius: 24px;
  box-shadow: 0 16px 36px var(--shadow-color);
}

:deep(.van-grid-item__content) {
  min-height: 108px;
  background: linear-gradient(180deg, #fbfdff, #f1f7ff);
  border: 1px solid rgba(221, 230, 241, 0.76);
  border-radius: 22px;
  box-shadow: 0 10px 24px rgba(31, 59, 89, 0.06);
}

:deep(.van-grid-item__icon) {
  font-size: 30px;
  color: var(--primary-color);
}

:deep(.van-grid-item__text) {
  margin-top: 10px;
  color: var(--text-color);
  font-size: 15px;
  font-weight: 700;
}
</style>
