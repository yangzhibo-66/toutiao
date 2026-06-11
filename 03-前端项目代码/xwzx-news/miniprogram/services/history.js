const { request } = require('../utils/request')
const { isLoggedIn } = require('../utils/auth')
const { getStoredHistory, saveStoredHistory } = require('../utils/news')

function listLocalHistory() {
  return getStoredHistory()
}

function saveLocalHistory(list) {
  saveStoredHistory(list)
}

function addLocalHistory(news) {
  const list = listLocalHistory()
  const filtered = list.filter((item) => item.id !== news.id)
  const next = [
    {
      ...news,
      viewTime: new Date().toLocaleString(),
    },
    ...filtered,
  ].slice(0, 50)
  saveLocalHistory(next)
  return next
}

function removeLocalHistory(newsId) {
  const next = listLocalHistory().filter((item) => item.id !== newsId)
  saveLocalHistory(next)
  return next
}

function clearLocalHistory() {
  saveLocalHistory([])
  return []
}

async function addHistory(news) {
  if (isLoggedIn()) {
    try {
      await request({
        url: '/api/history/add',
        method: 'POST',
        auth: true,
        data: { newsId: news.id },
      })
    } catch (error) {
      console.error('addHistory remote failed:', error)
    }
  }

  addLocalHistory(news)
  return { success: true }
}

async function getHistoryList() {
  if (!isLoggedIn()) {
    return {
      success: true,
      data: listLocalHistory(),
      isLocal: true,
    }
  }

  try {
    const result = await request({
      url: '/api/history/list',
      auth: true,
    })

    if (result && result.code === 200) {
      const list = result.data.list || []
      saveLocalHistory(list)
      return {
        success: true,
        data: list,
      }
    }
  } catch (error) {
    console.error('getHistoryList failed:', error)
  }

  return {
    success: true,
    data: listLocalHistory(),
    isLocal: true,
  }
}

async function removeHistory(newsId) {
  if (isLoggedIn()) {
    try {
      await request({
        url: `/api/history/delete/${newsId}`,
        method: 'DELETE',
        auth: true,
      })
    } catch (error) {
      console.error('removeHistory remote failed:', error)
    }
  }

  removeLocalHistory(newsId)
  return { success: true }
}

async function clearHistory() {
  if (isLoggedIn()) {
    try {
      await request({
        url: '/api/history/clear',
        method: 'DELETE',
        auth: true,
      })
    } catch (error) {
      console.error('clearHistory remote failed:', error)
    }
  }

  clearLocalHistory()
  return { success: true }
}

module.exports = {
  addHistory,
  getHistoryList,
  removeHistory,
  clearHistory,
}
