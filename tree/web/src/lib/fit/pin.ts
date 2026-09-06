export type PinCredential = { salt: string; digest: string };

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('');
}

export async function hashPin(pin: string, salt: string): Promise<string> {
  const payload = new TextEncoder().encode(`${salt}:${pin}`);
  const digest = await crypto.subtle.digest('SHA-256', payload);
  return bytesToHex(new Uint8Array(digest));
}

export async function createPinCredential(pin: string): Promise<PinCredential> {
  const saltBytes = new Uint8Array(16);
  crypto.getRandomValues(saltBytes);
  const salt = bytesToHex(saltBytes);
  return { salt, digest: await hashPin(pin, salt) };
}

export async function verifyPin(pin: string, credential: PinCredential): Promise<boolean> {
  return (await hashPin(pin, credential.salt)) === credential.digest;
}
