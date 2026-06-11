const app = getApp()
const { fetchCategories, fetchNewsList } = require('../../services/news')
const { PAGE_SIZE } = require('../../utils/config')

Page({
  data: {
    categories: [],
    currentCategoryId: 1,
    currentCategoryName: '头条',
    newsList: [],
    page: 1,
    loading: false,
    finished: false,
    initialized: false,
  },

  async onLoad(options) {
    await this.bootstrap(options)
  },

  async onPullDownRefresh() {
    await this.refreshList()
    wx.stopPullDownRefresh()
  },

  async onReachBottom() {
    await this.loadNewsList(false)
  },

  async bootstrap(options = {}) {
    const categories = await fetchCategories()
    app.globalData.categories = categories

    const firstCategory = categories.length ? categories[0] : { id: 1, name: '头条' }
    const categoryId = Number(options.categoryId) || firstCategory.id || 1
    const currentCategory = categories.find((item) => item.id === categoryId) || firstCategory

    this.setData({
      categories,
      currentCategoryId: currentCategory.id,
      currentCategoryName: currentCategory.name,
      initialized: true,
      newsList: [],
      page: 1,
      finished: false,
    })

    await this.loadNewsList(true)
  },

  async refreshList() {
    this.setData({
      page: 1,
      newsList: [],
      finished: false,
    })

    await this.loadNewsList(true)
  },

  async loadNewsList(isRefresh) {
    if (this.data.loading || (!isRefresh && this.data.finished)) {
      return
    }

    this.setData({ loading: true })

    try {
      const page = isRefresh ? 1 : this.data.page
      const result = await fetchNewsList({
        categoryId: this.data.currentCategoryId,
        page,
        pageSize: PAGE_SIZE,
      })

      const nextList = isRefresh ? result.list : this.data.newsList.concat(result.list)
      this.setData({
        newsList: nextList,
        page: page + 1,
        finished: !result.hasMore || result.list.length < PAGE_SIZE,
      })
    } catch (error) {
      wx.showToast({
        title: error.message || '加载失败',
        icon: 'none',
      })
    } finally {
      this.setData({ loading: false })
    }
  },

  async switchCategory(event) {
    const categoryId = Number(event.currentTarget.dataset.id)
    if (categoryId === this.data.currentCategoryId) return

    const currentCategory = this.data.categories.find((item) => item.id === categoryId)
    this.setData({
      currentCategoryId: categoryId,
      currentCategoryName: currentCategory ? currentCategory.name : '头条',
      newsList: [],
      page: 1,
      finished: false,
    })

    await this.loadNewsList(true)
  },

  goToCategoryPage() {
    wx.navigateTo({
      url: '/pages/category/category',
    })
  },

  goToDetail(event) {
    const { id } = event.detail
    wx.navigateTo({
      url: `/pages/detail/detail?id=${id}`,
    })
  },
})
