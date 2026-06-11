Page({
  copyTip() {
    wx.setClipboardData({
      data: '请将 AI 能力改为后端代理接口后，再在小程序中启用。',
    })
  },
})
