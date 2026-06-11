const { request } = require('../utils/request')
const { PAGE_SIZE } = require('../utils/config')
const { FALLBACK_CATEGORIES, normalizeNewsItem } = require('../utils/news')

async function fetchCategories() {
  try {
    const result = await request({
      url: '/api/news/categories',
    })

    if (result && result.code === 200 && Array.isArray(result.data)) {
      return result.data
    }
  } catch (error) {
    console.error('fetchCategories failed:', error)
  }

  return FALLBACK_CATEGORIES
}

async function fetchNewsList({ categoryId, page = 1, pageSize = PAGE_SIZE }) {
  const result = await request({
    url: '/api/news/list',
    data: {
      categoryId,
      page,
      pageSize,
    },
  })

  if (result && result.code === 200) {
    const list = (result.data.list || []).map(normalizeNewsItem)
    return {
      list,
      hasMore: !!result.data.hasMore && list.length >= 1,
    }
  }

  throw new Error(result && result.message ? result.message : '获取新闻列表失败')
}

async function fetchNewsDetail(id) {
  const result = await request({
    url: '/api/news/detail',
    data: { id },
  })

  if (result && result.code === 200) {
    const detail = normalizeNewsItem(result.data || {})
    detail.relatedNews = (detail.relatedNews || []).map(normalizeNewsItem)
    return detail
  }

  throw new Error(result && result.message ? result.message : '获取新闻详情失败')
}

module.exports = {
  fetchCategories,
  fetchNewsList,
  fetchNewsDetail,
}
