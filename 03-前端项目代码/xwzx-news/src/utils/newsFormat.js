export const categoryNameMap = {
  1: '推荐',
  2: '热榜',
  3: '关注',
  4: '北京',
  5: '科技',
  6: '财经',
  7: '军事',
  8: '科技',
  9: '财经'
}

export const categoryIconMap = {
  1: 'fire-o',
  2: 'friends-o',
  3: 'flag-o',
  4: 'location-o',
  5: 'cluster-o',
  6: 'gold-coin-o',
  7: 'apps-o',
  8: 'cluster-o',
  9: 'gold-coin-o'
}

export const displayCategoryName = (category) => {
  if (!category) return '推荐'
  return categoryNameMap[category.id] || category.name || '推荐'
}

export const formatPublishTime = (value) => {
  if (!value) return '刚刚'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  const diff = Date.now() - date.getTime()
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour

  if (diff < minute) return '刚刚'
  if (diff < hour) return `${Math.max(1, Math.floor(diff / minute))}分钟前`
  if (diff < day) return `${Math.floor(diff / hour)}小时前`
  return `${Math.floor(diff / day)}天前`
}

export const formatCount = (value = 0) => {
  const count = Number(value) || 0
  if (count >= 10000) return `${(count / 10000).toFixed(count >= 100000 ? 0 : 1)}万`
  return `${count}`
}

export const normalizeNewsItem = (item) => ({
  ...item,
  categoryId: item.categoryId ?? item.category_id,
  publishTime: item.publishTime ?? item.publishedTime ?? item.publish_time
})

export const matchesKeyword = (item, keyword) => {
  const query = String(keyword || '').trim().toLowerCase()
  if (!query) return true
  return [item.title, item.description, item.author]
    .filter(Boolean)
    .some((value) => String(value).toLowerCase().includes(query))
}

