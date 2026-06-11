const historyService = require('../../services/history')

Page({
  data: {
    list: [],
  },

  async onShow() {
    await this.loadList()
  },

  async loadList() {
    const result = await historyService.getHistoryList()
    this.setData({
      list: result.data || [],
    })
  },

  goToDetail(event) {
    const { id } = event.detail
    wx.navigateTo({
      url: `/pages/detail/detail?id=${id}`,
    })
  },

  removeItem(event) {
    const id = Number(event.currentTarget.dataset.id)
    wx.showModal({
      title: '删除记录',
      content: '确定要删除这条浏览记录吗？',
      success: async (res) => {
        if (!res.confirm) return
        await historyService.removeHistory(id)
        this.loadList()
      },
    })
  },

  clearAll() {
    wx.showModal({
      title: '清空历史',
      content: '确定要清空全部浏览记录吗？',
      success: async (res) => {
        if (!res.confirm) return
        await historyService.clearHistory()
        this.loadList()
      },
    })
  },
})
