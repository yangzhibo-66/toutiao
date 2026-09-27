import { apiConfig } from '../config/api'

const categoryPalette = {
  1: ['#ff8a00', '#ffd166'],
  2: ['#ff5a5f', '#ffb88c'],
  3: ['#2274a5', '#88c0ff'],
  4: ['#0b6e4f', '#72d6a0'],
  5: ['#9b5de5', '#f15bb5'],
  6: ['#2a9d8f', '#8ecae6'],
  7: ['#6a4c93', '#adb5ff'],
  8: ['#1d3557', '#5fa8d3'],
  9: ['#b5651d', '#ffd6a5']
}

const categoryLabel = {
  1: 'TOP',
  2: 'SOCIETY',
  3: 'CHINA',
  4: 'WORLD',
  5: 'FUN',
  6: 'SPORT',
  7: 'DEFENSE',
  8: 'TECH',
  9: 'FINANCE'
}

const buildFallbackSvg = (title = 'NEWS', categoryId = 1) => {
  const [start, end] = categoryPalette[categoryId] || categoryPalette[1]
  const safeTitle = String(title).slice(0, 22).replace(/[<>&"]/g, '')
  const label = categoryLabel[categoryId] || 'NEWS'
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="640" height="420" viewBox="0 0 640 420">
      <defs>
        <linearGradient id="g" x1="0%" x2="100%" y1="0%" y2="100%">
          <stop offset="0%" stop-color="${start}" />
          <stop offset="100%" stop-color="${end}" />
        </linearGradient>
      </defs>
      <rect width="640" height="420" rx="28" fill="url(#g)" />
      <circle cx="520" cy="92" r="86" fill="rgba(255,255,255,.15)" />
      <circle cx="108" cy="344" r="118" fill="rgba(255,255,255,.12)" />
      <text x="44" y="72" fill="rgba(255,255,255,.9)" font-family="Arial, sans-serif" font-size="34" font-weight="700">${label}</text>
      <text x="44" y="160" fill="#fff" font-family="Arial, sans-serif" font-size="40" font-weight="700">${safeTitle || 'Latest News'}</text>
      <text x="44" y="364" fill="rgba(255,255,255,.88)" font-family="Arial, sans-serif" font-size="24">Live update</text>
    </svg>
  `
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
}

export const resolveNewsImage = (news) => {
  if (news?.image) {
    return news.image.startsWith('/uploads/') ? `${apiConfig.baseURL}${news.image}` : news.image
  }
  return buildFallbackSvg(news?.title, news?.categoryId)
}
