import type { Metadata } from 'next'
import { StaffLogin } from '@/components/staff/staff-login'
import { safeBackofficeNext } from '@/lib/staff-auth'


export const metadata: Metadata = {
  title: 'Staff Login',
  description: 'Secure staff access to the Livenza backoffice.',
}


export function resolveStaffLoginNext(value?: string): string {
  return safeBackofficeNext(value)
}


export default async function StaffLoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string | string[] }>
}) {
  const query = await searchParams
  const requestedNext = Array.isArray(query.next) ? query.next[0] : query.next
  const nextPath = resolveStaffLoginNext(requestedNext)

  return (
    <main className="ecosystem-page">
      <section className="ecosystem-hero">
        <div className="section-inner">
          <div className="ecosystem-eyebrow">LIVENZA STAFF</div>
          <h1>SECURE BACKOFFICE ACCESS.</h1>
          <p>
            Sign in with the Tesla OS 27 credentials or passkey assigned by your administrator.
          </p>
          <StaffLogin nextPath={nextPath} />
        </div>
      </section>
    </main>
  )
}
