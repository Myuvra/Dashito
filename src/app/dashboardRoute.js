export function hashSlug(hash = '') {
  try {
    return decodeURIComponent(String(hash))
      .replace(/^#\/?/, '')
      .replace(/^\/+|\/+$/g, '')
      .trim()
  } catch {
    return ''
  }
}

export function dashboardFromHash(hash, dashboardList) {
  const slug = hashSlug(hash)
  if (!slug) return dashboardList[0]
  return dashboardList.find((item) => item.slug === slug || item.id === slug || item.aliases?.includes(slug)) || dashboardList[0]
}

export function dashboardHash(dashboard) {
  return `#/${dashboard.slug}`
}
