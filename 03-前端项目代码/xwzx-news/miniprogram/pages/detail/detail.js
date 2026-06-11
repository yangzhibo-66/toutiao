const { fetchNewsDetail } = require('../../services/news')
const favoriteService = require('../../services/favorite')
const historyService = require('../../services/history')
const { buildContentParagraphs, hasReadableContent } = require('../../utils/news')

Page({
  data: {
    newsId: 0,
    detail: null,
    paragraphs: [],
    hasReadableContent: false,
    isFavorite: false,
    loading: true,
  },

  async onLoad(options) {
    const newsId = Number(options.id)
    this.setData({ newsId })
    await this.loadDetail(newsId)
  },

  async loadDetail(newsId) {
    this.setData({ loading: true })

    try {
      const detail = await fetchNewsDetail(newsId)
      const paragraphs = buildContentParagraphs(detail)
      const favoriteResult = await favoriteService.checkFavorite(newsId)

      this.setData({
        detail,
        paragraphs,
        hasReadableContent: hasReadableContent(detail),
        isFavorite: !!favoriteResult.isFavorite,
      })

      historyService.addHistory(detail)
    } catch (error) {
      wx.showToast({
        title: error.message || '加载失败',
        icon: 'none',
      })
    } finally {
      this.setData({ loading: false })
    }
  },

  async toggleFavorite() {
    if (!this.data.detail) return

    let result
    if (this.data.isFavorite) {
      result = await favoriteService.removeFavorite(this.data.detail.id)
    } else {
      result = await favoriteService.addFavorite(this.data.detail)
    }

    if (result.success) {
      const next = !this.data.isFavorite
      this.setData({ isFavorite: next })
      wx.showToast({
        title: next ? '已加入收藏' : '已取消收藏',
        icon: 'none',
      })
      return
    }

    wx.showToast({
      title: result.message || '操作失败',
      icon: 'none',
    })
  },

  goToRelated(event) {
    const { id } = event.detail
    wx.redirectTo({
      url: `/pages/detail/detail?id=${id}`,
    })
  },

  copySourceLink() {
    const url = this.data.detail && this.data.detail.sourceUrl
    if (!url) return

    wx.setClipboardData({
      data: url,
    })
  },
})
