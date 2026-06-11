const { request } = require('../utils/request')
const { isLoggedIn } = require('../utils/auth')
const { getStoredFavorites, saveStoredFavorites } = require('../utils/news')

function listLocalFavorites() {
  return getStoredFavorites()
}

function saveLocalFavorites(list) {
  saveStoredFavorites(list)
}

function isFavorite(newsId) {
  return listLocalFavorites().some((item) => item.id === newsId)
}

function addLocalFavorite(news) {
  const list = listLocalFavorites()
  if (list.some((item) => item.id === news.id)) return list

  const next = [
    {
      ...news,
      favoriteTime: new Date().toLocaleString(),
    },
    ...list,
  ]
  saveLocalFavorites(next)
  return next
}

function removeLocalFavorite(newsId) {
  const next = listLocalFavorites().filter((item) => item.id !== newsId)
  saveLocalFavorites(next)
  return next
}

function clearLocalFavorites() {
  saveLocalFavorites([])
  return []
}

async function checkFavorite(newsId) {
  if (!isLoggedIn()) {
    return {
      success: true,
      isFavorite: isFavorite(newsId),
      isLocal: true,
    }
  }

  try {
    const result = await request({
      url: '/api/favorite/check',
      auth: true,
      data: { newsId },
    })

    if (result && result.code === 200) {
      return {
        success: true,
        isFavorite: !!result.data.isFavorite,
      }
    }
  } catch (error) {
    console.error('checkFavorite failed:', error)
  }

  return {
    success: true,
    isFavorite: isFavorite(newsId),
    isLocal: true,
  }
}

async function addFavorite(news) {
  if (isLoggedIn()) {
    const result = await request({
      url: '/api/favorite/add',
      method: 'POST',
      auth: true,
      data: { newsId: news.id },
    })

    if (!(result && result.code === 200)) {
      return {
        success: false,
        message: result && result.message ? result.message : '收藏失败',
      }
    }
  }

  addLocalFavorite(news)
  return { success: true }
}

async function removeFavorite(newsId) {
  if (isLoggedIn()) {
    const result = await request({
      url: `/api/favorite/remove?newsId=${newsId}`,
      method: 'DELETE',
      auth: true,
    })

    if (!(result && result.code === 200)) {
      return {
        success: false,
        message: result && result.message ? result.message : '取消收藏失败',
      }
    }
  }

  removeLocalFavorite(newsId)
  return { success: true }
}

async function getFavoriteList() {
  if (!isLoggedIn()) {
    return {
      success: true,
      data: listLocalFavorites(),
      isLocal: true,
    }
  }

  try {
    const result = await request({
      url: '/api/favorite/list',
      auth: true,
      data: { page: 1, pageSize: 100 },
    })

    if (result && result.code === 200) {
      const list = result.data.list || []
      saveLocalFavorites(list)
      return {
        success: true,
        data: list,
      }
    }
  } catch (error) {
    console.error('getFavoriteList failed:', error)
  }

  return {
    success: true,
    data: listLocalFavorites(),
    isLocal: true,
  }
}

async function clearFavorites() {
  if (isLoggedIn()) {
    const result = await request({
      url: '/api/favorite/clear',
      method: 'DELETE',
      auth: true,
    })

    if (!(result && result.code === 200)) {
      return {
        success: false,
        message: result && result.message ? result.message : '清空收藏失败',
      }
    }
  }

  clearLocalFavorites()
  return { success: true }
}

module.exports = {
  listLocalFavorites,
  isFavorite,
  checkFavorite,
  addFavorite,
  removeFavorite,
  getFavoriteList,
  clearFavorites,
}
