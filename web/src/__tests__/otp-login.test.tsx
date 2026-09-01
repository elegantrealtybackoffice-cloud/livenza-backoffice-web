import { render, screen } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import { OtpLogin } from '@/components/my/otp-login'

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

it('identifies WhatsApp as the customer OTP delivery channel', () => {
  render(<OtpLogin />)

  expect(screen.getByText(/code.*WhatsApp|WhatsApp.*code/i)).toBeInTheDocument()
})
