const { request } = require('../utils/request')
const { setAuth, clearAuth, getUserInfo, getToken } = require('../utils/auth')
const { BASE_URL } = require('../utils/config')

function normalizeUserInfo(userInfo) {
  if (!userInfo) return null

  const avatar = userInfo.avatar
  return {
    ...userInfo,
    avatar: avatar && avatar.startsWith('/uploads/') ? `${BASE_URL}${avatar}` : avatar,
  }
}

async function login(username, password) {
  const result = await request({
    url: '/api/user/login',
    method: 'POST',
    data: { username, password },
  })

  if (result && result.code === 200) {
    const userInfo = normalizeUserInfo(result.data.userInfo)
    const token = result.data.token
    setAuth(userInfo, token)
    return {
      success: true,
      userInfo,
      token,
    }
  }

  return {
    success: false,
    message: result && result.message ? result.message : '登录失败',
  }
}

async function register(username, password) {
  const result = await request({
    url: '/api/user/register',
    method: 'POST',
    data: { username, password },
  })

  if (result && result.code === 200) {
    const userInfo = normalizeUserInfo(result.data.userInfo)
    const token = result.data.token
    setAuth(userInfo, token)
    return {
      success: true,
      userInfo,
      token,
    }
  }

  return {
    success: false,
    message: result && result.message ? result.message : '注册失败',
  }
}

async function getProfile() {
  if (!getToken()) {
    return {
      success: false,
      message: '未登录',
    }
  }

  try {
    const result = await request({
      url: '/api/user/info',
      auth: true,
    })

    if (result && result.code === 200) {
      const userInfo = normalizeUserInfo(result.data)
      setAuth(userInfo, getToken())
      return {
        success: true,
        data: userInfo,
      }
    }
  } catch (error) {
    console.error('getProfile failed:', error)
  }

  return {
    success: false,
    message: '获取用户信息失败',
  }
}

function logout() {
  clearAuth()
}

module.exports = {
  login,
  register,
  getProfile,
  logout,
  getUserInfo,
  getToken,
}
