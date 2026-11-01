'use client'

import { useEffect, useRef } from 'react'

export function AmbientCursor() {
  const cursor = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    const element = cursor.current
    const canAnimate = window.matchMedia('(pointer: fine)').matches && !window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (!element || !canAnimate) return

    let frame = 0
    let x = -100
    let y = -100
    const move = (event: PointerEvent) => {
      if (event.pointerType !== 'mouse') return
      x = event.clientX
      y = event.clientY
      element.style.opacity = '1'
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(() => { element.style.transform = `translate3d(${x}px, ${y}px, 0)` })
    }
    const hide = () => { element.style.opacity = '0' }
    const down = () => element.classList.add('ambient-cursor-active')
    const up = () => element.classList.remove('ambient-cursor-active')
    window.addEventListener('pointermove', move, { passive: true })
    document.addEventListener('pointerleave', hide)
    window.addEventListener('pointerdown', down)
    window.addEventListener('pointerup', up)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('pointermove', move)
      document.removeEventListener('pointerleave', hide)
      window.removeEventListener('pointerdown', down)
      window.removeEventListener('pointerup', up)
    }
  }, [])

  return <span ref={cursor} className="ambient-cursor" aria-hidden="true" />
}
