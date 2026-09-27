import { defineStore } from 'pinia'
import request from '../../services/request'

const PAGE_SIZE = 10

export const useNewsStore = defineStore('news', {
  state: () => ({
    newsList: [],
    newsDetail: {},
    categories: [],
    currentCategory: 1,
    loading: false,
    refreshing: false,
    finished: false,
    categoriesLoading: false,
    requesting: false,
    requestToken: 0
  }),

  actions: {
    async getCategories() {
      if (this.categories.length || this.categoriesLoading) return

      this.categoriesLoading = true

      try {
        const response = await request.get('/api/news/categories')

        if (response.data && response.data.code === 200) {
          this.categories = [...response.data.data, { id: 10, name: '更多' }]

          if (!this.currentCategory && this.categories.length > 0) {
            this.currentCategory = this.categories[0].id
          }
        }
      } catch (error) {
        console.error('获取新闻分类失败:', error)
        this.categories = [
          { id: 1, name: '头条' },
          { id: 2, name: '社会' },
          { id: 3, name: '国内' },
          { id: 4, name: '国际' },
          { id: 5, name: '娱乐' },
          { id: 6, name: '体育' },
          { id: 7, name: '科技' }
        ]
      } finally {
        this.categoriesLoading = false
      }
    },

    changeCategory(categoryId) {
      if (this.currentCategory === categoryId && this.newsList.length) return

      this.currentCategory = categoryId
      this.newsList = []
      this.finished = false
      return this.getNewsList(true)
    },

    async getNewsList(isRefresh = false) {
      if (!isRefresh && (this.requesting || this.finished)) return

      if (isRefresh) {
        this.refreshing = true
        this.newsList = []
        this.finished = false
      }

      this.loading = true
      this.requesting = true
      const requestToken = ++this.requestToken
      const page = isRefresh ? 1 : Math.floor(this.newsList.length / PAGE_SIZE) + 1
      const categoryId = this.currentCategory

      try {
        const response = await request.get('/api/news/list', {
          params: {
            categoryId,
            page,
            pageSize: PAGE_SIZE
          }
        })

        if (categoryId !== this.currentCategory || requestToken !== this.requestToken) return

        if (response.data && response.data.code === 200) {
          const newsData = (response.data.data.list || []).map(item => ({
            ...item,
            categoryId: item.categoryId ?? item.category_id,
            publishTime: item.publishTime ?? item.publishedTime ?? item.publish_time
          }))

          if (isRefresh) {
            this.newsList = newsData
          } else {
            const existingIds = new Set(this.newsList.map(item => item.id))
            this.newsList = [
              ...this.newsList,
              ...newsData.filter(item => !existingIds.has(item.id))
            ]
          }

          this.finished = !response.data.data.hasMore || newsData.length < PAGE_SIZE
        }
      } catch (error) {
        console.error('获取新闻列表失败:', error)
      } finally {
        if (requestToken === this.requestToken) {
          this.loading = false
          this.refreshing = false
          this.requesting = false
        } else if (!this.requesting) {
          this.loading = false
          this.refreshing = false
        }
      }
    },

    async getNewsDetail(id) {
      try {
        const response = await request.get('/api/news/detail', {
          params: { id }
        })

        if (response.data && response.data.code === 200) {
          this.newsDetail = response.data.data
          return
        }

        console.error('获取新闻详情失败: 接口返回错误')
      } catch (error) {
        console.error('获取新闻详情失败:', error)
      }
    },

    getCategoryName(categoryId) {
      const category = this.categories.find(item => item.id === categoryId)
      return category ? category.name : '未知'
    }
  }
})
