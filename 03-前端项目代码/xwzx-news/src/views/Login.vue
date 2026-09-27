<template>
  <div class="login-page">
    <van-nav-bar
      title="用户登录"
      left-arrow
      fixed
      @click-left="onClickLeft"
    />

    <div class="login-container">
      <div class="login-hero">
        <div class="hero-badge">NEWS HUB</div>
        <h1>欢迎回来</h1>
        <p>登录后即可同步你的收藏、历史记录和个性化内容。</p>
      </div>

      <div class="login-card">
        <div class="login-logo">
          <van-image
            width="82"
            height="82"
            round
            src="https://s1.aigei.com/src/img/png/c0/c00e707792c049dc9240b741ad268afa.png?imageMogr2/auto-orient/thumbnail/!282x320r/gravity/Center/crop/282x320/quality/85/%7CimageView2/2/w/282&e=2051020800&token=P7S2Xpzfz11vAkASLTkfHN7Fw-oOZBecqeJaxypL:4kQ494a9fTxVX6GoUHgRJQlKm5Y="
          />
          <div class="logo-copy">
            <strong>新闻资讯</strong>
            <span>清爽阅读，实时更新</span>
          </div>
        </div>

        <van-form class="login-form" @submit="onSubmit">
          <van-cell-group inset>
            <van-field
              v-model="username"
              name="username"
              label="用户名"
              placeholder="请输入用户名"
              :rules="[{ required: true, message: '请填写用户名' }]"
            />
            <van-field
              v-model="password"
              type="password"
              name="password"
              label="密码"
              placeholder="请输入密码"
              :rules="[{ required: true, message: '请填写密码' }]"
            />
          </van-cell-group>

          <div class="submit-btn">
            <van-button round block type="primary" native-type="submit" size="large">
              登录
            </van-button>
          </div>

          <div class="login-tips">
            <p>测试账号：admin</p>
            <p>测试密码：123456</p>
          </div>
        </van-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '../store/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const username = ref('')
const password = ref('')

const onSubmit = async () => {
  showToast({
    type: 'loading',
    message: '登录中...',
    forbidClick: true,
    duration: 0
  })

  try {
    const result = await userStore.login({
      username: username.value,
      password: password.value
    })

    if (result.success) {
      showToast({
        type: 'success',
        message: result.message
      })
      // 被守卫拦截而来时回跳原页面，否则回首页
      router.push(typeof route.query.redirect === 'string' ? route.query.redirect : '/')
      return
    }

    showToast({
      type: 'fail',
      message: result.message
    })
  } catch (error) {
    showToast({
      type: 'fail',
      message: '登录失败，请稍后再试'
    })
  }
}

const onClickLeft = () => {
  router.back()
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  padding-top: 46px;
  background: var(--page-gradient);
}

.login-container {
  padding: 18px 16px 32px;
}

.login-hero {
  position: relative;
  margin-bottom: 18px;
  padding: 22px 22px 18px;
  color: #fff;
  background: linear-gradient(135deg, #1f5eff, #4aa8ff 68%, #7dc4ff);
  border-radius: 28px;
  box-shadow: 0 18px 36px rgba(22, 119, 255, 0.24);
  overflow: hidden;
}

.login-hero::after {
  content: '';
  position: absolute;
  right: -36px;
  top: -44px;
  width: 140px;
  height: 140px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.14);
}

.hero-badge {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 12px;
  margin-bottom: 12px;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.16em;
  background: rgba(255, 255, 255, 0.16);
  border-radius: 999px;
}

.login-hero h1,
.login-hero p {
  position: relative;
  z-index: 1;
}

.login-hero h1 {
  margin: 0 0 8px;
  font-size: 28px;
  line-height: 1.15;
}

.login-hero p {
  margin: 0;
  max-width: 280px;
  color: rgba(255, 255, 255, 0.88);
  font-size: 14px;
  line-height: 1.6;
}

.login-card {
  padding: 18px 16px 22px;
  background: var(--card-color);
  border: 1px solid rgba(221, 230, 241, 0.82);
  border-radius: 26px;
  box-shadow: 0 18px 40px var(--shadow-color);
  backdrop-filter: blur(16px);
}

.login-logo {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 18px;
}

.logo-copy strong {
  display: block;
  margin-bottom: 6px;
  color: var(--text-color);
  font-size: 22px;
  font-weight: 900;
}

.logo-copy span {
  color: var(--text-color-light);
  font-size: 13px;
}

.submit-btn {
  margin: 22px 16px 0;
}

.submit-btn :deep(.van-button) {
  height: 46px;
  font-size: 16px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--primary-color), #4aa8ff);
  border: 0;
  box-shadow: 0 14px 30px rgba(22, 119, 255, 0.2);
}

.login-tips {
  margin-top: 18px;
  padding: 14px;
  color: var(--text-color-light);
  font-size: 13px;
  line-height: 1.7;
  background: var(--secondary-color);
  border-radius: 16px;
}

.login-tips p + p {
  margin-top: 4px;
}
</style>
