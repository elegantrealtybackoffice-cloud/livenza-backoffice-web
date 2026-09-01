import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { BookingWizard } from '@/components/booking/booking-wizard'

const push = vi.fn()
vi.mock('next/navigation', () => ({ useRouter: () => ({ push }) }))
vi.mock('@/lib/analytics', () => ({ track: vi.fn() }))
vi.mock('@/lib/api', () => ({
  ApiError: class ApiError extends Error {},
  getMe: vi.fn(async () => ({ ok: true, customer: { id: 'c1', full_name: '', primary_mobile: '+919876543210', primary_email: '', status: 'active' } })),
  getBookingAddons: vi.fn(async () => []),
  getProperty: vi.fn(async () => ({ id:1,slug:'oasis-test',name:'Oasis Test',city:'Jaipur',area:'Sitapura',summary:'',stay_types:['student'],room_categories:[{slug:'deluxe-twin',name:'Deluxe Twin',occupancy:2,summary:'',rate_plans:[{code:'academic',stay_type:'student',billing_period:'academic_year',currency:'INR',amount_minor:16000000,security_deposit_minor:500000,reservation_amount_minor:1000000}]}] })),
  getAvailability: vi.fn(async () => ({property:'oasis-test',room_category:'deluxe-twin',start:'2026-09-01',end:'2026-10-01',available_count:1,availability_state:'available',allocatable_unit_type:'room'})),
  requestOtp: vi.fn(), verifyOtp: vi.fn(), createHold: vi.fn(), createBooking: vi.fn(), createPayment: vi.fn(),
}))

describe('BookingWizard', () => {
  beforeEach(() => push.mockReset())
  it('does not advance until dates and rate plan are ready', async () => {
    render(<BookingWizard initialProperty="oasis-test" initialRoomCategory="deluxe-twin" />)
    const button = await screen.findByRole('button', { name: /check live availability/i })
    await userEvent.click(button)
    expect(await screen.findByRole('alert')).toHaveTextContent(/choose a property, room, rate plan and dates/i)
  })

  it('shows reserve amount separately from the full total', async () => {
    render(<BookingWizard initialProperty="oasis-test" initialRoomCategory="deluxe-twin" />)
    await screen.findByRole('option', { name: /academic_year/i })
    await userEvent.type(screen.getByLabelText('Move-in'), '2026-09-01')
    await userEvent.type(screen.getByLabelText('Move-out'), '2026-10-01')
    await userEvent.click(screen.getByRole('button', { name: /check live availability/i }))
    await userEvent.click(await screen.findByRole('button', { name: /^continue$/i }))
    await userEvent.type(screen.getByLabelText('Resident name'), 'Resident')
    await userEvent.click(screen.getByRole('button', { name: /^continue$/i }))
    await userEvent.type(screen.getByLabelText('Guardian name'), 'Guardian')
    await userEvent.type(screen.getByLabelText('Guardian mobile'), '9876543211')
    await userEvent.click(screen.getByRole('button', { name: /^continue$/i }))
    await userEvent.click(screen.getByRole('button', { name: /^continue$/i }))
    await userEvent.click(screen.getByRole('button', { name: /^reserve$/i }))
    expect(screen.getByText(/reservation due now/i)).toBeInTheDocument()
  })
})
