import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { GurugramMap } from './gurugram-map'

describe('Gurugram property map', () => {
  it('links every named sector marker to its dedicated property page', () => {
    render(<GurugramMap />)
    expect(screen.getByRole('heading', { name: /explore gurugram/i })).toBeInTheDocument()
    for (const name of ['The Sienna', 'The Azure', 'G 38 Getaway', 'The Elara', 'The Maralia', 'The Avelia']) {
      expect(screen.getByRole('link', { name: new RegExp(name) })).toHaveAttribute('href', expect.stringMatching(/^\/stays\/gurugram\//))
    }
    expect(screen.getByText(/sector locations are approximate/i)).toBeInTheDocument()
  })
})
