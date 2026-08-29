import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import Storefront from '@/components/store/storefront'

describe('Livenza.store', () => {
  it('launches the four curated V1 worlds', () => {
    render(<Storefront products={[]} />)
    for (const label of ['Wear', 'Move', 'Live', 'Accessories']) expect(screen.getByText(label)).toBeInTheDocument()
  })
})
