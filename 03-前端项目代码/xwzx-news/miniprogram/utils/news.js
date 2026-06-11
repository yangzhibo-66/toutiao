const { STORAGE_KEYS } = require('./config')

const FALLBACK_CATEGORIES = [
  { id: 1, name: '头条' },
  { id: 2, name: '社会' },
  { id: 3, name: '国内' },
  { id: 4, name: '国际' },
  { id: 5, name: '娱乐' },
  { id: 6, name: '体育' },
  { id: 7, name: '科技' },
  { id: 8, name: '军事' },
  { id: 9, name: '财经' },
]

function normalizeNewsItem(item = {}) {
  return {
    ...item,
    categoryId: item.categoryId || item.category_id || 1,
    publishTime: item.publishTime || item.publishedTime || item.publish_time || '',
    image: item.image || '',
    author: item.author || '今日要闻',
    description: item.description || '',
    views: item.views || 0,
  }
}

function getStoredFavorites() {
  return wx.getStorageSync(STORAGE_KEYS.favorite) || []
}

function saveStoredFavorites(list) {
  wx.setStorageSync(STORAGE_KEYS.favorite, list || [])
}

function getStoredHistory() {
  return wx.getStorageSync(STORAGE_KEYS.history) || []
}

function saveStoredHistory(list) {
  wx.setStorageSync(STORAGE_KEYS.history, list || [])
}

function createPlaceholderText(news = {}) {
  const name = String(news.title || 'NEWS').slice(0, 24)
  return name || 'NEWS'
}

function normalizeText(value) {
  return String(value || '')
    .replace(/\s+/g, '')
    .replace(/[，。！？、“”‘’（）()【】\[\]\-—|:：]/g, '')
    .trim()
}

function stripSourceSuffix(value) {
  return String(value || '')
    .replace(/\s*[-|—]\s*[^-|—]+$/, '')
    .trim()
}

function splitLongParagraph(paragraph) {
  const text = String(paragraph || '').trim()
  if (!text) return []
  if (text.length <= 110) return [text]

  const parts = text.match(/[^。！？?]+[。！？?]?/g) || [text]
  const chunks = []
  let buffer = ''

  parts.forEach((part) => {
    const sentence = part.trim()
    if (!sentence) return

    if (!buffer) {
      buffer = sentence
      return
    }

    if ((buffer + sentence).length > 110) {
      chunks.push(buffer.trim())
      buffer = sentence
      return
    }

    buffer += sentence
  })

  if (buffer) {
    chunks.push(buffer.trim())
  }

  return chunks.filter(Boolean)
}

function buildContentParagraphs(detail = {}) {
  const rawContent = String(detail.content || '').trim()
  const title = String(detail.title || '').trim()
  const description = String(detail.description || '').trim()
  const normalizedTitle = normalizeText(title)
  const normalizedShortTitle = normalizeText(stripSourceSuffix(title))
  const normalizedDescription = normalizeText(description)

  if (!rawContent) return []

  return rawContent
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean)
    .filter((item) => !/^来源[:：]/i.test(item))
    .flatMap(splitLongParagraph)
    .filter((item) => {
      const normalized = normalizeText(item)
      if (!normalized) return false
      if (normalized === normalizedTitle || normalized === normalizedShortTitle) return false
      if (normalizedDescription && normalized === normalizedDescription) return false
      if (normalizedShortTitle && normalized.includes(normalizedShortTitle) && normalized.length < 180) return false
      return true
    })
}

function hasReadableContent(detail = {}) {
  const paragraphs = buildContentParagraphs(detail)
  if (!paragraphs.length) return false

  const merged = paragraphs.join('\n\n').trim()
  const mergedLength = normalizeText(merged).length
  const sentenceCount = (merged.match(/[。！？?]/g) || []).length

  if (mergedLength < 180) return false
  if (paragraphs.length === 1) {
    return mergedLength >= 220 && sentenceCount >= 4
  }

  return sentenceCount >= 3 || mergedLength >= 260
}

module.exports = {
  FALLBACK_CATEGORIES,
  normalizeNewsItem,
  createPlaceholderText,
  getStoredFavorites,
  saveStoredFavorites,
  getStoredHistory,
  saveStoredHistory,
  buildContentParagraphs,
  hasReadableContent,
}
