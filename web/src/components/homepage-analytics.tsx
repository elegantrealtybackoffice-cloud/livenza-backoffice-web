'use client'
import { useEffect } from 'react'
import { track } from '@/lib/analytics'
export function HomepageAnalytics() {
  useEffect(() => { track('homepage_view') }, [])
  return null
}
