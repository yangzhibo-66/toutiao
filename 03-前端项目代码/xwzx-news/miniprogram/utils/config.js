const BASE_URL = 'http://127.0.0.1:8000'
const PAGE_SIZE = 10
const DEFAULT_AVATAR_TEXT = '游'
const STORAGE_KEYS = {
  token: 'mini_news_token',
  userInfo: 'mini_news_user_info',
  favorite: 'mini_news_favorites',
  history: 'mini_news_history',
}

module.exports = {
  BASE_URL,
  PAGE_SIZE,
  DEFAULT_AVATAR_TEXT,
  STORAGE_KEYS,
}
