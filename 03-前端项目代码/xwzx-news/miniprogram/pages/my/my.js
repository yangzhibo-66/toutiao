const userService = require('../../services/user')
const { DEFAULT_AVATAR_TEXT } = require('../../utils/config')
const { isLoggedIn } = require('../../utils/auth')

Page({
  data: {
    loggedIn: false,
    userInfo: null,
    avatarText: DEFAULT_AVATAR_TEXT,
  },

  onShow() {
    this.syncUser()
  },

  async syncUser() {
    const loggedIn = isLoggedIn()
    let userInfo = userService.getUserInfo()

    if (loggedIn) {
      const result = await userService.getProfile()
      if (result.success) {
        userInfo = result.data
      }
    }

    this.setData({
      loggedIn,
      userInfo,
      avatarText: userInfo && userInfo.username ? userInfo.username.slice(0, 1).toUpperCase() : DEFAULT_AVATAR_TEXT,
    })
  },

  goLogin() {
    wx.navigateTo({
      url: '/pages/login/login',
    })
  },

  goRegister() {
    wx.navigateTo({
      url: '/pages/register/register',
    })
  },

  requireLogin(url) {
    if (this.data.loggedIn) {
      wx.navigateTo({ url })
      return
    }

    wx.showModal({
      title: '需要登录',
      content: '登录后可以同步收藏和历史记录，现在去登录吗？',
      success: (res) => {
        if (res.confirm) {
          wx.navigateTo({
            url: '/pages/login/login',
          })
        }
      },
    })
  },

  goFavorite() {
    this.requireLogin('/pages/favorite/favorite')
  },

  goHistory() {
    this.requireLogin('/pages/history/history')
  },

  logout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出当前账号吗？',
      success: (res) => {
        if (res.confirm) {
          userService.logout()
          this.syncUser()
          wx.showToast({
            title: '已退出',
            icon: 'none',
          })
        }
      },
    })
  },
})
