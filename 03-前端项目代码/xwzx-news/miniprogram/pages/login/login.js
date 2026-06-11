const userService = require('../../services/user')

Page({
  data: {
    username: '',
    password: '',
    submitting: false,
  },

  onUsernameInput(event) {
    this.setData({ username: event.detail.value })
  },

  onPasswordInput(event) {
    this.setData({ password: event.detail.value })
  },

  async submit() {
    if (this.data.submitting) return
    if (!this.data.username.trim() || !this.data.password.trim()) {
      wx.showToast({
        title: '请输入用户名和密码',
        icon: 'none',
      })
      return
    }

    this.setData({ submitting: true })
    wx.showLoading({ title: '登录中' })

    try {
      const result = await userService.login(this.data.username.trim(), this.data.password)
      if (result.success) {
        wx.hideLoading()
        wx.showToast({
          title: '登录成功',
          icon: 'success',
        })
        wx.reLaunch({
          url: '/pages/my/my',
        })
        return
      }

      wx.hideLoading()
      wx.showToast({
        title: result.message || '登录失败',
        icon: 'none',
      })
    } catch (error) {
      wx.hideLoading()
      wx.showToast({
        title: error.message || '登录失败',
        icon: 'none',
      })
    } finally {
      this.setData({ submitting: false })
    }
  },

  goRegister() {
    wx.navigateTo({
      url: '/pages/register/register',
    })
  },
})
