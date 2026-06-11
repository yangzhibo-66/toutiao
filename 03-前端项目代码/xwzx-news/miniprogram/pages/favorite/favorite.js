const favoriteService = require('../../services/favorite')

Page({
  data: {
    list: [],
  },

  async onShow() {
    await this.loadList()
  },

  async loadList() {
    const result = await favoriteService.getFavoriteList()
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
      title: '删除收藏',
      content: '确定要删除这条收藏吗？',
      success: async (res) => {
        if (!res.confirm) return
        await favoriteService.removeFavorite(id)
        this.loadList()
      },
    })
  },

  clearAll() {
    wx.showModal({
      title: '清空收藏',
      content: '确定要清空全部收藏吗？',
      success: async (res) => {
        if (!res.confirm) return
        await favoriteService.clearFavorites()
        this.loadList()
      },
    })
  },
})
