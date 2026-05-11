import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import FormattedCurrency from '../FormattedCurrency'

describe('FormattedCurrency Component', () => {
  it('memformat angka sebagai Rupiah (IDR) secara default', () => {
    render(<FormattedCurrency amount={15000000} />)
    expect(screen.getByText('Rp 15.000.000')).toBeInTheDocument()
  })

  it('memformat angka desimal dengan benar', () => {
    render(<FormattedCurrency amount={250000} />)
    expect(screen.getByText('Rp 250.000')).toBeInTheDocument()
  })

  it('menampilkan currency symbol yang berbeda ketika currency diubah', () => {
    render(<FormattedCurrency amount={100} currency="USD" locale="en-US" />)
    expect(screen.getByText('$100')).toBeInTheDocument()
  })

  it('menerapkan className custom', () => {
    const { container } = render(
      <FormattedCurrency amount={50000} className="text-bold highlight" />
    )
    const span = container.querySelector('span')
    expect(span).toHaveClass('font-mono text-bold highlight')
  })

  it('menangani angka negatif dengan benar', () => {
    render(<FormattedCurrency amount={-50000} />)
    expect(screen.getByText('-Rp 50.000')).toBeInTheDocument()
  })

  it('menampilkan nol dengan format yang benar', () => {
    render(<FormattedCurrency amount={0} />)
    expect(screen.getByText('Rp 0')).toBeInTheDocument()
  })
})