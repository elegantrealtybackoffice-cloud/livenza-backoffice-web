import Link from 'next/link'
export function StickyAction({ href, label = 'CHECK AVAILABILITY' }: { href: string; label?: string }) {
  return <div className="sticky-action"><span>Ready to explore this stay?</span><Link href={href}>{label}</Link></div>
}
