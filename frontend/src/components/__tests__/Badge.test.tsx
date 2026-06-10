import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Badge from '../Badge'

describe('Badge Component', () => {
  it('menampilkan label yang diberikan', () => {
    render(<Badge label="New" />)
    expect(screen.getByText('New')).toBeInTheDocument()
  })

  it('menerapkan variant default jika tidak diberikan', () => {
    const { container } = render(<Badge label="Default" />)
    const badge = container.firstChild
    expect(badge).toHaveClass('badge badge-default badge-md')
  })

  it('menerapkan variant class ketika variant diberikan', () => {
    const { container } = render(<Badge label="Success" variant="success" />)
    const badge = container.firstChild
    expect(badge).toHaveClass('badge badge-success badge-md')
  })

  it('menerapkan size class yang berbeda', () => {
    const sizes: Array<'sm' | 'md' | 'lg'> = ['sm', 'md', 'lg']
    
    sizes.forEach(size => {
      const { container, unmount } = render(<Badge label="Test" size={size} />)
      const badge = container.firstChild
      expect(badge).toHaveClass(`badge badge-default badge-${size}`)
      unmount()
    })
  })

  it('menerapkan className custom', () => {
    const { container } = render(
      <Badge label="Custom" className="custom-class another-class" />
    )
    const badge = container.firstChild
    expect(badge).toHaveClass('badge badge-default badge-md custom-class another-class')
  })
})