const { STORAGE_KEYS } = require('./config')

function getToken() {
  return wx.getStorageSync(STORAGE_KEYS.token) || ''
}

function getUserInfo() {
  return wx.getStorageSync(STORAGE_KEYS.userInfo) || null
}

function setAuth(userInfo, token) {
  wx.setStorageSync(STORAGE_KEYS.userInfo, userInfo || null)
  wx.setStorageSync(STORAGE_KEYS.token, token || '')
}

function clearAuth() {
  wx.removeStorageSync(STORAGE_KEYS.userInfo)
  wx.removeStorageSync(STORAGE_KEYS.token)
}

function isLoggedIn() {
  return !!getToken()
}

module.exports = {
  getToken,
  getUserInfo,
  setAuth,
  clearAuth,
  isLoggedIn,
}
