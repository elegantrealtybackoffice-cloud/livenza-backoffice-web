export type StaffAuthMethod = 'password' | 'pattern'

export type StaffCredentialInput = {
  username: string
  method: StaffAuthMethod
  credential: string
  next: string
}

export type StaffSessionResponse = {
  ok: true
  authenticated: boolean
  staff?: { display_name: string; role: string }
}

type StaffAuthSuccess = { ok: true; redirect: string }


export function safeBackofficeNext(value?: string): string {
  let decoded: string
  try {
    decoded = decodeURIComponent(String(value ?? '').trim())
  } catch {
    return '/backoffice'
  }
  if (!decoded || !decoded.startsWith('/') || decoded.startsWith('//') || decoded.includes('\\')) {
    return '/backoffice'
  }
  const parsed = new URL(decoded, 'https://livenza.invalid')
  if (
    parsed.origin !== 'https://livenza.invalid'
    || (parsed.pathname !== '/backoffice' && !parsed.pathname.startsWith('/backoffice/'))
  ) {
    return '/backoffice'
  }
  return `${parsed.pathname}${parsed.search}`
}


async function readStaffJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { credentials: 'include', ...init })
  const body = await response.json().catch(() => ({})) as { error?: string }
  if (!response.ok) {
    throw new Error(body.error || `Staff authentication failed (${response.status})`)
  }
  return body as T
}


function postStaffJson<T>(path: string, body: unknown): Promise<T> {
  return readStaffJson<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}


export function getStaffSession(): Promise<StaffSessionResponse> {
  return readStaffJson<StaffSessionResponse>('/api/staff/session', { cache: 'no-store' })
}


export function authenticateStaff(input: StaffCredentialInput): Promise<StaffAuthSuccess> {
  return postStaffJson<StaffAuthSuccess>('/api/staff/authenticate', {
    ...input,
    next: safeBackofficeNext(input.next),
  })
}


function fromBase64Url(value: string): ArrayBuffer {
  const base64 = value.replace(/-/g, '+').replace(/_/g, '/').padEnd(Math.ceil(value.length / 4) * 4, '=')
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index)
  }
  return bytes.buffer
}


function toBase64Url(value: ArrayBuffer | null): string | null {
  if (value === null) return null
  const bytes = new Uint8Array(value)
  let binary = ''
  bytes.forEach((byte) => { binary += String.fromCharCode(byte) })
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}


type AuthenticationOptionsJson = Omit<PublicKeyCredentialRequestOptions, 'challenge' | 'allowCredentials'> & {
  challenge: string
  allowCredentials?: Array<Omit<PublicKeyCredentialDescriptor, 'id'> & { id: string }>
}


export async function authenticateStaffPasskey(
  username: string,
  next: string,
): Promise<StaffAuthSuccess> {
  if (!navigator.credentials?.get) {
    throw new Error('Fingerprint/passkeys are not supported by this browser.')
  }
  const options = await postStaffJson<AuthenticationOptionsJson>(
    '/api/webauthn/auth/options',
    { username: username.trim(), next: safeBackofficeNext(next) },
  )
  const publicKey = {
    ...options,
    challenge: fromBase64Url(options.challenge),
    allowCredentials: (options.allowCredentials ?? []).map((credential) => ({
      ...credential,
      id: fromBase64Url(credential.id),
    })),
  } satisfies PublicKeyCredentialRequestOptions
  const credential = await navigator.credentials.get({ publicKey })
  if (!credential) throw new Error('Passkey verification was cancelled.')
  const assertion = credential as PublicKeyCredential
  const response = assertion.response as AuthenticatorAssertionResponse
  return postStaffJson<StaffAuthSuccess>('/api/webauthn/auth/verify', {
    id: assertion.id,
    rawId: toBase64Url(assertion.rawId),
    type: assertion.type,
    response: {
      clientDataJSON: toBase64Url(response.clientDataJSON),
      authenticatorData: toBase64Url(response.authenticatorData),
      signature: toBase64Url(response.signature),
      userHandle: toBase64Url(response.userHandle),
    },
    clientExtensionResults: assertion.getClientExtensionResults(),
  })
}
