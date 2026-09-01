'use client'

import { useState } from 'react'
import {
  authenticateStaff,
  authenticateStaffPasskey,
  type StaffAuthMethod,
} from '@/lib/staff-auth'


type StaffLoginMethod = StaffAuthMethod | 'passkey'


export function StaffLogin({ nextPath }: { nextPath: string }) {
  const [method, setMethod] = useState<StaffLoginMethod>('password')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [pattern, setPattern] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit() {
    if (busy || !username.trim()) return
    setBusy(true)
    setError('')
    try {
      const result = method === 'passkey'
        ? await authenticateStaffPasskey(username, nextPath)
        : await authenticateStaff({
            username,
            method,
            credential: method === 'password' ? password : pattern,
            next: nextPath,
          })
      window.location.assign(result.redirect)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Staff sign-in was unavailable.')
      setBusy(false)
    }
  }

  return (
    <div className="booking-panel staff-login-card">
      <div className="staff-login-methods" aria-label="Staff sign-in method">
        {(['password', 'pattern', 'passkey'] as const).map((option) => (
          <button
            aria-pressed={method === option}
            className={method === option ? 'is-active' : ''}
            key={option}
            onClick={() => { setMethod(option); setError('') }}
            type="button"
          >
            {option[0].toUpperCase() + option.slice(1)}
          </button>
        ))}
      </div>

      {error ? <p role="alert">{error}</p> : null}

      <label>
        Login ID
        <input
          autoComplete="username webauthn"
          onChange={(event) => setUsername(event.target.value)}
          required
          value={username}
        />
      </label>

      {method === 'password' ? (
        <label>
          Password
          <input
            autoComplete="current-password"
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
        </label>
      ) : null}

      {method === 'pattern' ? (
        <label>
          Login pattern
          <input
            inputMode="numeric"
            onChange={(event) => setPattern(event.target.value)}
            pattern="[0-8](?:-[0-8]){3,8}"
            placeholder="0-1-2-5-8"
            required
            value={pattern}
          />
          <small>Enter at least four saved pattern points, separated by hyphens.</small>
        </label>
      ) : null}

      {method === 'passkey' ? (
        <p>Use the fingerprint, face, security key, or device passkey enrolled for this Login ID.</p>
      ) : null}

      <button
        disabled={
          busy
          || !username.trim()
          || (method === 'password' && !password)
          || (method === 'pattern' && !pattern)
        }
        onClick={submit}
        type="button"
      >
        {busy
          ? 'VERIFYING…'
          : method === 'passkey'
            ? 'CONTINUE WITH PASSKEY'
            : 'OPEN BACKOFFICE'}
      </button>
    </div>
  )
}
