import { render, screen } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import { MyDashboard } from '@/components/my/my-dashboard'

vi.mock('@/lib/api', () => ({
  getMe: vi.fn(async () => ({ok:true,customer:{id:'c1',full_name:'Store Customer',primary_mobile:'+919876543210',primary_email:'',status:'active'}})),
  getMyStays: vi.fn(async () => ({items:[]})),
  getMyPayments: vi.fn(async () => ({items:[]})),
  getMyDocuments: vi.fn(async () => ({items:[]})),
  getMySupport: vi.fn(async () => ({items:[]})),
}))

it('does not invent a current stay for a customer without stays', async () => {
  render(<MyDashboard />)
  expect(await screen.findByText(/No active stay yet/i)).toBeInTheDocument()
  expect(screen.queryByText(/CURRENT STAY/i)).not.toBeInTheDocument()
})
