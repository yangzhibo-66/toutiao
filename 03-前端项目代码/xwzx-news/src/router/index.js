import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../store/user'
import pinia from '../store'

const routes = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: {
      title: '登录',
      keepAlive: false
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: {
      title: '注册',
      keepAlive: false
    }
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: {
      title: '首页',
      keepAlive: true
    }
  },
  {
    path: '/news/detail/:id',
    name: 'NewsDetail',
    component: () => import('../views/NewsDetail.vue'),
    meta: {
      title: '新闻详情',
      keepAlive: false
    }
  },
  {
    path: '/publish',
    name: 'PublishNews',
    component: () => import('../views/PublishNews.vue'),
    meta: {
      title: '发布新闻',
      keepAlive: false,
      requiresAuth: true
    }
  },
  {
    path: '/my-news',
    name: 'MyNews',
    component: () => import('../views/MyNews.vue'),
    meta: {
      title: '已发布新闻',
      keepAlive: false,
      requiresAuth: true
    }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/History.vue'),
    meta: {
      title: '浏览历史',
      keepAlive: false
    }
  },
  {
    path: '/favorite',
    name: 'Favorite',
    component: () => import('../views/Favorite.vue'),
    meta: {
      title: '我的收藏',
      keepAlive: false
    }
  },
  {
    path: '/category',
    name: 'Category',
    component: () => import('../views/Category.vue'),
    meta: {
      title: '分类',
      keepAlive: true
    }
  },
  {
    path: '/hot',
    name: 'HotRank',
    component: () => import('../views/HotRank.vue'),
    meta: {
      title: '头条热榜',
      keepAlive: true
    }
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('../views/Search.vue'),
    meta: {
      title: '搜索',
      keepAlive: false
    }
  },
  {
    path: '/aichat',
    name: 'AIChat',
    component: () => import('../views/AIChat.vue'),
    meta: {
      title: 'AI问答',
      keepAlive: true
    }
  },
  {
    path: '/my',
    name: 'My',
    component: () => import('../views/My.vue'),
    meta: {
      title: '我的',
      keepAlive: true
    }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: {
      title: '个人信息',
      keepAlive: false,
      requiresAuth: true
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue'),
    meta: {
      title: '设置',
      keepAlive: false
    }
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 全局前置守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title || '新闻资讯'

  // 需要登录的页面：未登录时跳转登录页，登录成功后回跳（redirect 参数）
  if (to.meta.requiresAuth) {
    // main.js 中 router 先于 pinia 安装，这里显式传入 pinia 实例
    const userStore = useUserStore(pinia)
    if (!userStore.getLoginStatus) {
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }
  }

  next()
})

export default router
