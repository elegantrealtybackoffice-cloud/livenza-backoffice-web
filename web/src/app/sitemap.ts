import type { MetadataRoute } from 'next'
import { SITE_ORIGIN } from '@/lib/seo'
export default function sitemap(): MetadataRoute.Sitemap {
  const routes = ['/', '/stays', '/store', '/fit', '/groom', '/skin', '/media', '/life', '/about', '/contact']
  return routes.map(path => ({ url: `${SITE_ORIGIN}${path === '/' ? '' : path}`, lastModified: new Date(), changeFrequency: path === '/' ? 'weekly' : 'monthly', priority: path === '/' ? 1 : path === '/stays' ? .9 : .6 }))
}
