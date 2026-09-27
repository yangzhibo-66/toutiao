import request from './request'

export const fetchCategories = async () => {
  const response = await request.get('/api/news/categories')
  return response.data?.data || []
}

export const fetchNewsList = async ({ categoryId = 1, page = 1, pageSize = 10 } = {}) => {
  const response = await request.get('/api/news/list', {
    params: {
      categoryId,
      page,
      pageSize
    }
  })

  const data = response.data?.data || {}
  return {
    list: data.list || [],
    total: data.total || 0,
    hasMore: Boolean(data.hasMore)
  }
}

export const fetchSyncStatus = async () => {
  const response = await request.get('/api/news/sync/status')
  return response.data?.data || null
}

// 全库（categoryId 缺省）或指定分类的真热榜：后端按阅读量排序
export const fetchHotNews = async ({ categoryId, page = 1, pageSize = 10 } = {}) => {
  const response = await request.get('/api/news/hot', {
    params: {
      categoryId,
      page,
      pageSize
    }
  })

  const data = response.data?.data || {}
  return {
    list: data.list || [],
    total: data.total || 0,
    hasMore: Boolean(data.hasMore)
  }
}

export const searchNews = async ({ keyword, page = 1, pageSize = 10 } = {}) => {
  const response = await request.get('/api/news/search', {
    params: {
      keyword,
      page,
      pageSize
    }
  })

  const data = response.data?.data || {}
  return {
    list: data.list || [],
    total: data.total || 0,
    hasMore: Boolean(data.hasMore)
  }
}

const buildNewsFormData = (payload) => {
  const formData = new FormData()
  formData.append('title', payload.title)
  formData.append('description', payload.description || '')
  formData.append('content', payload.content)
  formData.append('categoryId', payload.categoryId)
  formData.append('author', payload.author || '')
  formData.append('imageUrl', payload.imageUrl || '')

  if (payload.imageFile) {
    formData.append('image', payload.imageFile)
  }

  return formData
}

// token 由 request 实例的请求拦截器统一携带，调用处不再显式传入
export const publishNews = async (payload) => {
  const formData = buildNewsFormData(payload)
  const response = await request.post('/api/news/upload', formData)
  return response.data
}

export const fetchMyNews = async ({ page = 1, pageSize = 20 } = {}) => {
  const response = await request.get('/api/news/mine', {
    params: { page, pageSize }
  })

  return response.data?.data || { list: [], total: 0, hasMore: false }
}

export const fetchMyNewsDetail = async (id) => {
  const response = await request.get(`/api/news/mine/${id}`)
  return response.data?.data || null
}

export const updateNews = async (id, payload) => {
  const formData = buildNewsFormData(payload)
  const response = await request.put(`/api/news/${id}`, formData)
  return response.data
}

export const deleteNews = async (id) => {
  const response = await request.delete(`/api/news/${id}`)
  return response.data
}
