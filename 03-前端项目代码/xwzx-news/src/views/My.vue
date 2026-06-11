<template>
  <div class="my-container">
    <van-nav-bar :title="$t('my.title')" />

    <div class="user-info" @click="goToProfile" v-if="isLogin">
      <div class="avatar">
        <van-image round width="82" height="82" :src="userAvatar" />
      </div>
      <div class="info">
        <span class="profile-kicker">ACCOUNT</span>
        <div class="username">{{ userInfo.username }}</div>
        <div class="desc">{{ userBio || $t('profile.bio') }}</div>
      </div>
      <van-icon name="arrow" class="arrow-icon" />
    </div>

    <div class="user-info guest" v-else>
      <div class="avatar">
        <van-image round width="82" height="82" :src="userAvatar" />
      </div>
      <div class="info">
        <span class="profile-kicker">WELCOME</span>
        <div class="username">{{ $t('my.notLoggedIn') }}</div>
        <div class="desc">登录后即可开启你的专属阅读空间。</div>
        <div class="action-row">
          <van-button type="primary" size="small" class="profile-action" @click="goToLogin">{{ $t('my.goToLogin') }}</van-button>
          <van-button type="default" size="small" class="profile-action ghost" @click="goToRegister">{{ $t('my.goToRegister') }}</van-button>
        </div>
      </div>
    </div>

    <div class="menu-list">
      <van-cell-group inset>
        <van-cell :title="$t('my.myFavorite')" is-link @click="goToFavorite">
          <template #icon><van-icon name="star-o" class="menu-icon" /></template>
        </van-cell>
        <van-cell :title="$t('my.browsingHistory')" is-link @click="goToHistory">
          <template #icon><van-icon name="clock-o" class="menu-icon" /></template>
        </van-cell>
        <van-cell :title="$t('my.notifications')" is-link>
          <template #icon><van-icon name="bell" class="menu-icon" /></template>
        </van-cell>
        <van-cell :title="$t('my.settings')" is-link @click="goToSettings">
          <template #icon><van-icon name="setting-o" class="menu-icon" /></template>
        </van-cell>
        <van-cell v-if="isLogin" :title="$t('my.logout')" class="logout-cell" @click="handleLogout">
          <template #icon><van-icon name="revoke" class="menu-icon" /></template>
        </van-cell>
      </van-cell-group>
    </div>

    <tab-bar />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showDialog, showToast } from 'vant'
import { useI18n } from 'vue-i18n'
import TabBar from '../components/TabBar.vue'
import { useUserStore } from '../store/user'

const userStore = useUserStore()
const router = useRouter()
const { t } = useI18n()

const defaultAvatar = 'https://s1.aigei.com/src/img/png/c0/c00e707792c049dc9240b741ad268afa.png?imageMogr2/auto-orient/thumbnail/!282x320r/gravity/Center/crop/282x320/quality/85/%7CimageView2/2/w/282&e=2051020800&token=P7S2Xpzfz11vAkASLTkfHN7Fw-oOZBecqeJaxypL:4kQ494a9fTxVX6GoUHgRJQlKm5Y='

const userInfo = computed(() => userStore.userInfo)
const isLogin = computed(() => userStore.getLoginStatus)
const userBio = computed(() => userStore.getUserBio || t('profile.bio'))
const userAvatar = computed(() => userStore.userInfo?.avatar || defaultAvatar)

const goToLogin = () => {
  router.push('/login')
}

const goToRegister = () => {
  router.push('/register')
}

const goToProfile = () => {
  if (isLogin.value) {
    router.push('/profile')
  }
}

const goToHistory = () => {
  if (isLogin.value) {
    router.push('/history')
  } else {
    showToast(t('common.login'))
    router.push('/login')
  }
}

const goToFavorite = () => {
  if (isLogin.value) {
    router.push('/favorite')
  } else {
    showToast(t('common.login'))
    router.push('/login')
  }
}

const goToSettings = () => {
  router.push('/settings')
}

const handleLogout = () => {
  showDialog({
    title: t('common.confirm'),
    message: `${t('my.logout')}?`,
    showCancelButton: true
  }).then((action) => {
    if (action === 'confirm') {
      userStore.logout()
      router.push('/login')
    }
  })
}

onMounted(async () => {
  try {
    await userStore.getUserInfoDetail()
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
})
</script>

<style scoped>
.my-container {
  min-height: 100vh;
  padding-top: 46px;
  padding-bottom: calc(72px + var(--safe-area-inset-bottom));
  background: var(--page-gradient);
}

:deep(.van-nav-bar) {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 999;
  background: var(--nav-color);
  backdrop-filter: blur(18px);
  box-shadow: 0 10px 26px var(--shadow-color);
}

:deep(.van-nav-bar__title) {
  color: var(--text-color);
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.user-info {
  display: flex;
  align-items: center;
  margin: 16px;
  padding: 18px;
  background: var(--card-color);
  border: 1px solid rgba(221, 230, 241, 0.84);
  border-radius: 24px;
  box-shadow: 0 16px 36px var(--shadow-color);
}

.user-info.guest {
  align-items: flex-start;
}

.arrow-icon {
  margin-left: 8px;
  color: var(--text-color-lighter);
  font-size: 18px;
}

.avatar {
  flex-shrink: 0;
  margin-right: 16px;
  padding: 4px;
  background: #fff;
  border: 3px solid rgba(22, 119, 255, 0.18);
  border-radius: 50%;
  box-shadow: 0 10px 24px var(--shadow-color);
}

.info {
  flex: 1;
  min-width: 0;
}

.profile-kicker {
  display: block;
  margin-bottom: 6px;
  color: var(--primary-color);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.16em;
}

.username {
  margin-bottom: 6px;
  color: var(--text-color);
  font-size: 21px;
  font-weight: 900;
  line-height: 1.2;
}

.desc {
  color: var(--text-color-light);
  font-size: 13px;
  line-height: 1.55;
}

.action-row {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.profile-action {
  height: 34px;
  padding: 0 14px;
  border: 0;
  border-radius: 999px;
  font-weight: 800;
}

.profile-action.ghost {
  color: var(--primary-color);
  background: #fff;
  border: 1px solid var(--border-color);
}

.menu-list {
  margin: 0 16px;
}

:deep(.menu-list .van-cell-group) {
  margin: 0;
  padding: 6px;
  background: var(--card-color);
  border: 1px solid rgba(221, 230, 241, 0.84);
  border-radius: 24px;
  box-shadow: 0 16px 36px var(--shadow-color);
  overflow: hidden;
}

:deep(.menu-list .van-cell) {
  align-items: center;
  min-height: 56px;
  color: var(--text-color);
  background: transparent;
  border-radius: 16px;
  transition: background 0.18s ease, transform 0.18s ease;
}

:deep(.menu-list .van-cell:active) {
  background: var(--secondary-color);
  transform: scale(0.99);
}

:deep(.menu-list .van-cell::after) {
  border-color: rgba(221, 230, 241, 0.9);
}

:deep(.menu-list .van-cell__title) {
  color: var(--text-color);
  font-weight: 700;
}

:deep(.menu-list .van-cell__right-icon) {
  color: var(--text-color-lighter);
}

.menu-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  margin-right: 10px;
  color: var(--primary-color);
  background: var(--primary-color-soft);
  border-radius: 10px;
  font-size: 18px;
}

:deep(.logout-cell .van-cell__title) {
  color: var(--danger-color);
}

.logout-cell .menu-icon {
  color: var(--danger-color);
  background: rgba(238, 90, 82, 0.1);
}
</style>
