const userService = require('../../services/user')

Page({
  data: {
    username: '',
    password: '',
    confirmPassword: '',
    submitting: false,
  },

  onUsernameInput(event) {
    this.setData({ username: event.detail.value })
  },

  onPasswordInput(event) {
    this.setData({ password: event.detail.value })
  },

  onConfirmPasswordInput(event) {
    this.setData({ confirmPassword: event.detail.value })
  },

  async submit() {
    if (this.data.submitting) return
    if (!this.data.username.trim() || !this.data.password.trim()) {
      wx.showToast({
        title: '请填写完整信息',
        icon: 'none',
      })
      return
    }

    if (this.data.password !== this.data.confirmPassword) {
      wx.showToast({
        title: '两次密码不一致',
        icon: 'none',
      })
      return
    }

    this.setData({ submitting: true })
    wx.showLoading({ title: '注册中' })

    try {
      const result = await userService.register(this.data.username.trim(), this.data.password)
      if (result.success) {
        wx.hideLoading()
        wx.showToast({
          title: '注册成功',
          icon: 'success',
        })
        wx.reLaunch({
          url: '/pages/my/my',
        })
        return
      }

      wx.hideLoading()
      wx.showToast({
        title: result.message || '注册失败',
        icon: 'none',
      })
    } catch (error) {
      wx.hideLoading()
      wx.showToast({
        title: error.message || '注册失败',
        icon: 'none',
      })
    } finally {
      this.setData({ submitting: false })
    }
  },

  goLogin() {
    wx.navigateBack({
      delta: 1,
      fail: () => {
        wx.redirectTo({
          url: '/pages/login/login',
        })
      },
    })
  },
})
