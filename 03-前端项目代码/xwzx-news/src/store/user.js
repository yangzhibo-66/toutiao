import { defineStore } from 'pinia'
import { apiConfig } from '../config/api'
import request from '../services/request'

const normalizeUserInfo = (userInfo) => {
  if (!userInfo) return userInfo

  const avatar = userInfo.avatar
  return {
    ...userInfo,
    avatar: avatar && avatar.startsWith('/uploads/') ? `${apiConfig.baseURL}${avatar}` : avatar,
  }
}

const getErrorMessage = (error, fallbackMessage) =>
  error.response?.data?.detail || error.response?.data?.message || fallbackMessage

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null,
    token: '',
    isLogin: false,
    userBio: 'This is my profile.',
  }),

  getters: {
    getUserInfo: (state) => state.userInfo,
    getToken: (state) => state.token,
    getLoginStatus: (state) => state.isLogin && !!state.token,
    getUserBio: (state) => state.userInfo?.bio || state.userBio,
  },

  actions: {
    setAuthState(userInfo, token) {
      this.userInfo = normalizeUserInfo(userInfo)
      this.token = token
      this.isLogin = !!token
    },

    logout() {
      this.userInfo = null
      this.token = ''
      this.isLogin = false
    },

    handleUnauthorized() {
      this.logout()
      return {
        success: false,
        message: '登录状态已失效，请重新登录',
      }
    },

    async login(userData) {
      try {
        const response = await request.post('/api/user/login', {
          username: userData.username,
          password: userData.password,
        })

        if (response.data?.code === 200) {
          const userInfo = response.data.data.userInfo
          const token = response.data.data.token
          this.setAuthState(userInfo, token)

          return {
            success: true,
            message: '登录成功',
          }
        }

        return {
          success: false,
          message: response.data?.message || '登录失败',
        }
      } catch (error) {
        console.error('Login request failed:', error)
        return {
          success: false,
          message: getErrorMessage(error, '登录请求失败，请稍后再试'),
        }
      }
    },

    async register(userData) {
      try {
        const response = await request.post('/api/user/register', {
          username: userData.username,
          password: userData.password,
        })

        if (response.data?.code === 200) {
          const userInfo = response.data.data.userInfo
          const token = response.data.data.token
          this.setAuthState(userInfo, token)

          return {
            success: true,
            message: '注册成功',
          }
        }

        return {
          success: false,
          message: response.data?.message || '注册失败',
        }
      } catch (error) {
        console.error('Register request failed:', error)
        return {
          success: false,
          message: getErrorMessage(error, '注册请求失败，请稍后再试'),
        }
      }
    },

    async getUserInfoDetail() {
      if (!this.token) {
        this.logout()
        return {
          success: false,
          message: '未登录',
        }
      }

      try {
        const response = await request.get('/api/user/info')

        if (response.data?.code === 200) {
          this.userInfo = normalizeUserInfo(response.data.data)
          this.isLogin = true

          return {
            success: true,
            message: '获取用户信息成功',
            data: response.data.data,
          }
        }

        return {
          success: false,
          message: response.data?.message || '获取用户信息失败',
        }
      } catch (error) {
        console.error('Get user info failed:', error)
        if (error.response?.status === 401) {
          return this.handleUnauthorized()
        }

        return {
          success: false,
          message: getErrorMessage(error, '获取用户信息请求失败，请稍后再试'),
        }
      }
    },

    async updateUserBio(bio) {
      if (!this.token) {
        this.logout()
        return {
          success: false,
          message: '未登录',
        }
      }

      try {
        const response = await request.put('/api/user/update', { bio })

        if (response.data?.code === 200) {
          this.userInfo = normalizeUserInfo(response.data.data)
          return {
            success: true,
            message: '个人简介更新成功',
          }
        }

        return {
          success: false,
          message: response.data?.message || '个人简介更新失败',
        }
      } catch (error) {
        console.error('Update bio failed:', error)
        if (error.response?.status === 401) {
          return this.handleUnauthorized()
        }

        return {
          success: false,
          message: getErrorMessage(error, '个人简介更新失败，请稍后再试'),
        }
      }
    },

    async uploadAvatar(file) {
      if (!this.token) {
        this.logout()
        return {
          success: false,
          message: '未登录',
        }
      }

      try {
        const formData = new FormData()
        formData.append('file', file)

        const response = await request.post('/api/user/avatar', formData)

        if (response.data?.code === 200) {
          this.userInfo = normalizeUserInfo(response.data.data)
          return {
            success: true,
            message: '头像修改成功',
            data: this.userInfo,
          }
        }

        return {
          success: false,
          message: response.data?.message || '头像修改失败',
        }
      } catch (error) {
        console.error('Upload avatar failed:', error)
        if (error.response?.status === 401) {
          return this.handleUnauthorized()
        }

        return {
          success: false,
          message: getErrorMessage(error, '头像上传失败，请稍后再试'),
        }
      }
    },

    async updatePassword(oldPassword, newPassword) {
      if (!this.token) {
        this.logout()
        return {
          success: false,
          message: '未登录',
        }
      }

      try {
        const response = await request.put('/api/user/password', {
          oldPassword,
          newPassword,
        })

        if (response.data?.code === 200) {
          return {
            success: true,
            message: '密码修改成功',
          }
        }

        return {
          success: false,
          message: response.data?.message || '密码修改失败',
        }
      } catch (error) {
        console.error('Update password failed:', error)
        if (error.response?.status === 401) {
          return this.handleUnauthorized()
        }

        return {
          success: false,
          message: getErrorMessage(error, '密码修改失败，请稍后再试'),
        }
      }
    },
  },

  persist: {
    key: 'user-store',
    storage: localStorage,
  },
})
