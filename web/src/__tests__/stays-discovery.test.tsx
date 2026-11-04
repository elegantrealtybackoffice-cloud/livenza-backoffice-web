import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import { StaysExplorer } from '@/components/stays-explorer'

const push = vi.fn()
vi.mock('next/navigation', () => ({ useRouter: () => ({ push }) }))

afterEach(() => { cleanup(); push.mockClear() })

describe('StaysExplorer', () => {
  it('shows the complete city picker and routes an available city collection', () => {
    render(<StaysExplorer />)
    expect(screen.getByRole('button', { name: /destination ahmedabad/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /destination haridwar/i })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /destination gurugram/i }))
    expect(push).toHaveBeenCalledWith('/stays/gurugram')
  })
})
