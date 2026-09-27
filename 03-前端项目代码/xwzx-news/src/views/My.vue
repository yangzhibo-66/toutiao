<template>
  <div class="my-page">
    <header class="my-topbar">
      <span></span>
      <div class="top-actions">
        <van-icon name="bell" />
        <van-icon name="setting-o" @click="goToSettings" />
      </div>
    </header>

    <section class="profile-card" @click="goToProfile">
      <van-image round width="64" height="64" :src="userAvatar" />
      <div class="profile-main">
        <h2>{{ isLogin ? userInfo.username : '头条用户' }}</h2>
        <p>{{ isLogin ? '查看并编辑个人资料' : '登录后同步收藏、历史和个性化推荐' }}</p>
      </div>
      <van-icon name="arrow" />
    </section>

    <section class="stats-card">
      <div v-for="item in stats" :key="item.label" class="stat-item">
        <strong>{{ item.value }}</strong>
        <span>{{ item.label }}</span>
      </div>
    </section>

    <section v-if="!isLogin" class="login-actions">
      <van-button type="primary" block round @click="goToLogin">登录 / 注册</van-button>
    </section>

    <section class="shortcut-panel">
      <div
        v-for="item in shortcuts"
        :key="item.label"
        class="shortcut-item"
        @click="item.action"
      >
        <van-icon :name="item.icon" :style="{ color: item.color }" />
        <span>{{ item.label }}</span>
      </div>
    </section>

    <section class="creator-panel">
      <div class="panel-title">
        <strong>创作中心</strong>
        <span @click="goToMyNews">进入 <van-icon name="arrow" /></span>
      </div>
      <div class="creator-grid">
        <div v-for="item in creatorTools" :key="item.label" class="creator-tool" @click="item.action">
          <van-icon :name="item.icon" />
          <span>{{ item.label }}</span>
        </div>
      </div>
    </section>

    <section class="menu-panel">
      <van-cell title="内容偏好" is-link @click="showComingSoon" />
      <van-cell title="清理缓存" is-link @click="showComingSoon" />
      <van-cell title="用户反馈" is-link @click="showComingSoon" />
      <van-cell title="系统设置" is-link @click="goToSettings" />
      <van-cell v-if="isLogin" title="退出登录" class="logout-cell" @click="handleLogout" />
    </section>

    <tab-bar />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showDialog, showToast } from 'vant'
import TabBar from '../components/TabBar.vue'
import { useFavoriteStore } from '../store/modules/favorite'
import { useHistoryStore } from '../store/modules/history'
import { useUserStore } from '../store/user'

const userStore = useUserStore()
const favoriteStore = useFavoriteStore()
const historyStore = useHistoryStore()
const router = useRouter()

const defaultAvatar = 'https://s1.aigei.com/src/img/png/c0/c00e707792c049dc9240b741ad268afa.png?imageMogr2/auto-orient/thumbnail/!282x320r/gravity/Center/crop/282x320/quality/85/%7CimageView2/2/w/282&e=2051020800&token=P7S2Xpzfz11vAkASLTkfHN7Fw-oOZBecqeJaxypL:4kQ494a9fTxVX6GoUHgRJQlKm5Y='

const userInfo = computed(() => userStore.userInfo || {})
const isLogin = computed(() => userStore.getLoginStatus)
const userAvatar = computed(() => userStore.userInfo?.avatar || defaultAvatar)

const stats = computed(() => [
  { label: '阅读', value: historyStore.getHistory.length || 128 },
  { label: '收藏', value: favoriteStore.getFavorites.length },
  { label: '历史', value: historyStore.getHistory.length }
])

const requireLogin = (callback) => {
  if (!isLogin.value) {
    showToast('请先登录')
    router.push('/login')
    return
  }
  callback()
}

const goToLogin = () => router.push('/login')
const goToSettings = () => router.push('/settings')
const goToProfile = () => {
  if (isLogin.value) router.push('/profile')
  else router.push('/login')
}
const goToFavorite = () => requireLogin(() => router.push('/favorite'))
const goToHistory = () => requireLogin(() => router.push('/history'))
const goToPublish = () => requireLogin(() => router.push('/publish'))
const goToMyNews = () => requireLogin(() => router.push('/my-news'))
const showComingSoon = () => showToast('功能已预留，后续可接入')

const shortcuts = [
  { label: '头条通知', icon: 'bell', color: '#f04438', action: showComingSoon },
  { label: '收藏', icon: 'star-o', color: '#f7b500', action: goToFavorite },
  { label: '浏览历史', icon: 'clock-o', color: '#12b76a', action: goToHistory },
  { label: '系统设置', icon: 'setting-o', color: '#0ea5e9', action: goToSettings }
]

const creatorTools = [
  { label: '发布新闻', icon: 'wap-home-o', action: goToPublish },
  { label: '已发布新闻', icon: 'description-o', action: goToMyNews },
  { label: '管理新闻', icon: 'records-o', action: goToMyNews }
]

const handleLogout = () => {
  showDialog({
    title: '确认',
    message: '确定退出登录吗？',
    showCancelButton: true
  }).then((action) => {
    if (action === 'confirm') {
      userStore.logout()
      router.push('/login')
    }
  })
}

onMounted(async () => {
  favoriteStore.loadFavorites()
  historyStore.loadHistory()
  if (isLogin.value) {
    try {
      await userStore.getUserInfoDetail()
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }
})
</script>

<style scoped>
.my-page {
  min-height: 100vh;
  padding: 12px 12px calc(76px + var(--safe-area-inset-bottom));
  background: #f7f8fa;
}

.my-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 42px;
}

.top-actions {
  display: flex;
  gap: 18px;
  color: #111827;
  font-size: 22px;
}

.profile-card,
.stats-card,
.shortcut-panel,
.creator-panel,
.menu-panel {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 10px 24px rgba(17, 24, 39, 0.04);
}

.profile-card {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 16px;
}

.profile-main {
  flex: 1;
  min-width: 0;
}

.profile-main h2 {
  margin: 0 0 4px;
  color: #111827;
  font-size: 18px;
  font-weight: 900;
}

.profile-main p {
  margin: 0;
  color: #8a93a3;
  font-size: 13px;
}

.stats-card {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  margin-top: 10px;
  padding: 16px 0;
}

.stat-item {
  text-align: center;
}

.stat-item strong {
  display: block;
  color: #111827;
  font-size: 18px;
  font-weight: 900;
}

.stat-item span {
  color: #667085;
  font-size: 12px;
}

.login-actions {
  margin-top: 10px;
}

.shortcut-panel {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  margin-top: 10px;
  padding: 14px 0;
}

.shortcut-item,
.creator-tool {
  display: flex;
  flex-direction: column;
  gap: 7px;
  align-items: center;
  color: #1f2937;
  font-size: 12px;
  font-weight: 700;
}

.shortcut-item .van-icon {
  font-size: 24px;
}

.creator-panel {
  margin-top: 10px;
  padding: 14px;
}

.panel-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.panel-title strong {
  color: #111827;
  font-size: 15px;
  font-weight: 900;
}

.panel-title span {
  display: inline-flex;
  align-items: center;
  color: #8a93a3;
  font-size: 12px;
}

.creator-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
}

.creator-tool .van-icon {
  color: #1d4ed8;
  font-size: 24px;
}

.menu-panel {
  margin-top: 10px;
  overflow: hidden;
}

:deep(.menu-panel .van-cell) {
  min-height: 50px;
}

:deep(.menu-panel .van-cell__title) {
  color: #111827;
  font-weight: 700;
}

:deep(.logout-cell .van-cell__title) {
  color: #f04438;
}
</style>


