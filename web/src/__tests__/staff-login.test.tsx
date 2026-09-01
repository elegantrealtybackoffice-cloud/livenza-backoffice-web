import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { StaffLogin } from '@/components/staff/staff-login'
import { resolveStaffLoginNext } from '@/app/staff-login/page'
import * as staffAuth from '@/lib/staff-auth'
import {
  authenticateStaff,
  authenticateStaffPasskey,
  safeBackofficeNext,
} from '@/lib/staff-auth'


describe('staff auth client', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('accepts only local backoffice return paths', () => {
    expect(safeBackofficeNext('/backoffice/rooms?tab=available')).toBe(
      '/backoffice/rooms?tab=available',
    )
    expect(safeBackofficeNext('//evil.example/backoffice')).toBe('/backoffice')
    expect(safeBackofficeNext('/my')).toBe('/backoffice')
    expect(safeBackofficeNext('/backoffice-evil')).toBe('/backoffice')
    expect(safeBackofficeNext('/backoffice/../my')).toBe('/backoffice')
    expect(safeBackofficeNext('/backoffice/%252e%252e/my')).toBe('/backoffice')
  })

  it('sends staff credentials only to the staff bridge', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true, redirect: '/backoffice' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    await authenticateStaff({
      username: 'manager',
      method: 'password',
      credential: 'secret',
      next: '/backoffice',
    })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/staff/authenticate',
      expect.objectContaining({ method: 'POST', credentials: 'include' }),
    )
    expect(fetchMock.mock.calls[0][1]?.body).toContain('"method":"password"')
  })

  it('converts WebAuthn options and credential buffers at the browser boundary', async () => {
    const get = vi.fn().mockResolvedValue({
      id: 'credential-id',
      type: 'public-key',
      rawId: new Uint8Array([4, 5, 6]).buffer,
      response: {
        clientDataJSON: new Uint8Array([7]).buffer,
        authenticatorData: new Uint8Array([8]).buffer,
        signature: new Uint8Array([9]).buffer,
        userHandle: null,
      },
      getClientExtensionResults: () => ({ appid: false }),
    })
    Object.defineProperty(navigator, 'credentials', {
      configurable: true,
      value: { get },
    })
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            challenge: 'AQID',
            allowCredentials: [{ id: 'BAUG', type: 'public-key' }],
            timeout: 60_000,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ ok: true, redirect: '/backoffice/rooms' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )

    await authenticateStaffPasskey('manager', '/backoffice/rooms')

    const publicKey = get.mock.calls[0][0].publicKey
    expect(publicKey.challenge).toBeInstanceOf(ArrayBuffer)
    expect(publicKey.allowCredentials[0].id).toBeInstanceOf(ArrayBuffer)
    expect(fetchMock.mock.calls[0][1]?.body).toContain('"next":"/backoffice/rooms"')
    const verification = JSON.parse(String(fetchMock.mock.calls[1][1]?.body))
    expect(verification.rawId).toBe('BAUG')
    expect(verification.response).toMatchObject({
      clientDataJSON: 'Bw',
      authenticatorData: 'CA',
      signature: 'CQ',
      userHandle: null,
    })
  })
})


describe('StaffLogin', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('uses the staff bridge without invoking customer OTP auth', async () => {
    const authenticate = vi
      .spyOn(staffAuth, 'authenticateStaff')
      .mockReturnValue(new Promise(() => undefined))
    render(<StaffLogin nextPath="/backoffice/rooms" />)
    await userEvent.type(screen.getByLabelText(/login id/i), 'manager')
    await userEvent.type(screen.getByLabelText(/^password$/i), 'secret')
    await userEvent.click(screen.getByRole('button', { name: /open backoffice/i }))
    expect(authenticate).toHaveBeenCalledWith({
      username: 'manager',
      method: 'password',
      credential: 'secret',
      next: '/backoffice/rooms',
    })
  })

  it('submits the existing serialized pattern format', async () => {
    const authenticate = vi
      .spyOn(staffAuth, 'authenticateStaff')
      .mockReturnValue(new Promise(() => undefined))
    render(<StaffLogin nextPath="/backoffice" />)
    await userEvent.type(screen.getByLabelText(/login id/i), 'manager')
    await userEvent.click(screen.getByRole('button', { name: /^pattern$/i }))
    await userEvent.type(screen.getByLabelText(/login pattern/i), '0-1-2-5-8')
    await userEvent.click(screen.getByRole('button', { name: /open backoffice/i }))
    expect(authenticate).toHaveBeenCalledWith({
      username: 'manager',
      method: 'pattern',
      credential: '0-1-2-5-8',
      next: '/backoffice',
    })
  })

  it('uses the existing WebAuthn bridge and renders failures accessibly', async () => {
    vi.spyOn(staffAuth, 'authenticateStaffPasskey').mockRejectedValue(
      new Error('No passkey is enrolled for this Login ID.'),
    )
    render(<StaffLogin nextPath="/backoffice/admin" />)
    await userEvent.type(screen.getByLabelText(/login id/i), 'admin')
    await userEvent.click(screen.getByRole('button', { name: /^passkey$/i }))
    await userEvent.click(screen.getByRole('button', { name: /continue with passkey/i }))
    expect(staffAuth.authenticateStaffPasskey).toHaveBeenCalledWith(
      'admin',
      '/backoffice/admin',
    )
    expect(await screen.findByRole('alert')).toHaveTextContent(/no passkey is enrolled/i)
  })
})


describe('staff login route', () => {
  it('normalizes the return path before it reaches the client component', () => {
    expect(resolveStaffLoginNext('/backoffice/rooms')).toBe('/backoffice/rooms')
    expect(resolveStaffLoginNext('https://evil.example/backoffice')).toBe('/backoffice')
  })
})
