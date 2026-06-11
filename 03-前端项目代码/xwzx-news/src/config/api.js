/**
 * API 配置文件
 * 优先使用 Vite 环境变量；未配置时自动使用当前页面主机名访问 8000 端口后端。
 */

const trimTrailingSlash = (value) => value.replace(/\/+$/, '')

const resolveApiBaseURL = () => {
  const envBaseURL = import.meta.env.VITE_API_BASE_URL?.trim()
  if (envBaseURL) {
    return trimTrailingSlash(envBaseURL)
  }

  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location
    return `${protocol}//${hostname}:8000`
  }

  return 'http://127.0.0.1:8000'
}

export const apiConfig = {
  baseURL: resolveApiBaseURL(),
}

export const aiChatConfig = {
  apiEndpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
  apiKey: 'sk-a83568578df343fb8092cfdcbbaa2491',
  model: 'qwen-max',
}
