import request from './request'

// AI 问答记录（登录用户自动保存，匿名不保存）
export const fetchAiHistory = async ({ page = 1, pageSize = 20 } = {}) => {
  const response = await request.get('/api/ai/history', {
    params: { page, pageSize }
  })

  const data = response.data?.data || {}
  return {
    list: data.list || [],
    total: data.total || 0,
    hasMore: Boolean(data.hasMore)
  }
}

export const deleteAiHistory = async (id) => {
  const response = await request.delete(`/api/ai/history/${id}`)
  return response.data
}
