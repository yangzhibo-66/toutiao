const app = getApp()
const { fetchCategories } = require('../../services/news')

Page({
  data: {
    categories: [],
  },

  async onLoad() {
    const cached = app.globalData.categories || []
    if (cached.length) {
      this.setData({ categories: cached })
      return
    }

    const categories = await fetchCategories()
    app.globalData.categories = categories
    this.setData({ categories })
  },

  chooseCategory(event) {
    const id = event.currentTarget.dataset.id
    wx.redirectTo({
      url: `/pages/home/home?categoryId=${id}`,
    })
  },
})
