import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import StatusBadge from '../StatusBadge'

describe('StatusBadge Component', () => {
  it('menampilkan label "Draft" untuk status DRAFT', () => {
    render(<StatusBadge status="DRAFT" />)
    expect(screen.getByText('Draft')).toBeInTheDocument()
  })

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
    const { container } = render(<StatusBadge status="UNDER_REVIEW" />)
    const badge = container.querySelector('[data-status="UNDER_REVIEW"]')
    expect(badge).toBeInTheDocument()
  })
})