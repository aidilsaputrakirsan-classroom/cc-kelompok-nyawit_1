import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import StatusBadge from '../StatusBadge'

describe('StatusBadge Component', () => {
  it('menampilkan label "Submitted" untuk status SUBMITTED', () => {
    render(<StatusBadge status="SUBMITTED" />)
    expect(screen.getByText('Submitted')).toBeInTheDocument()
  })

  it('menampilkan label "Approved" untuk status APPROVED', () => {
    render(<StatusBadge status="APPROVED" />)
    expect(screen.getByText('Approved')).toBeInTheDocument()
  })

  it('menampilkan label "Rejected" untuk status REJECTED', () => {
    render(<StatusBadge status="REJECTED" />)
    expect(screen.getByText('Rejected')).toBeInTheDocument()
  })

  it('memiliki attribute data-status yang sesuai', () => {
    const { container } = render(<StatusBadge status="PO_ISSUED" />)
    const badge = container.querySelector('[data-status="PO_ISSUED"]')
    expect(badge).toBeInTheDocument()
  })
})