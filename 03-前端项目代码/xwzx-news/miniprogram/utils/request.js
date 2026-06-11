const { BASE_URL } = require('./config')
const { getToken, clearAuth } = require('./auth')

function request({ url, method = 'GET', data, auth = false, header = {} }) {
  return new Promise((resolve, reject) => {
    const requestHeader = {
      'content-type': 'application/json',
      ...header,
    }

    if (auth) {
      const token = getToken()
      if (token) {
        requestHeader.Authorization = token
      }
    }

    wx.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header: requestHeader,
      success: (response) => {
        if (response.statusCode === 401) {
          clearAuth()
          reject(new Error('登录状态已失效，请重新登录'))
          return
        }

        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(response.data)
          return
        }

        reject(new Error(`请求失败: ${response.statusCode}`))
      },
      fail: (error) => {
        reject(new Error(error.errMsg || '网络请求失败'))
      },
    })
  })
}

module.exports = {
  request,
}
