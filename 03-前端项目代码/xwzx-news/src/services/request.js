import axios from 'axios'
import { apiConfig } from '../config/api'

/**
 * 统一 axios 实例：
 * - baseURL 统一从 apiConfig 读取，调用处不再拼接地址
 * - 请求拦截器自动携带登录 token，调用处不再手动传 Authorization 头
 * - 响应拦截器统一处理 401（清空登录态），调用处只需提示用户
 */
const request = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: 15000,
})

request.interceptors.request.use(async (config) => {
  // 动态引入，避免与 store 之间形成静态循环依赖
  const { useUserStore } = await import('../store/user')
  const userStore = useUserStore()
  if (userStore.token) {
    config.headers.Authorization = userStore.token
  }
  return config
})

request.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // token 失效：清空登录态，后续由路由守卫引导重新登录
      const { useUserStore } = await import('../store/user')
      useUserStore().handleUnauthorized()
    }
    return Promise.reject(error)
  }
)

export default request
