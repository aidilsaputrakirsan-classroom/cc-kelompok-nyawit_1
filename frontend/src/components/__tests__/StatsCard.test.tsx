import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import StatsCard from '../StatsCard'

describe('StatsCard Component', () => {
  it('menampilkan label dan value', () => {
    render(<StatsCard label="Total PR" value={42} />)
    expect(screen.getByText('Total PR')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('menampilkan icon ketika diberikan', () => {
    render(
      <StatsCard 
        label="Approved" 
        value={10} 
        icon={<span data-testid="icon">✅</span>} 
      />
    )
    expect(screen.getByTestId('icon')).toBeInTheDocument()
  })

  it('menampilkan change text ketika diberikan', () => {
    render(
      <StatsCard 
        label="Revenue" 
        value={5000000} 
        change="+12% from last month" 
      />
    )
    expect(screen.getByText('+12% from last month')).toBeInTheDocument()
  })

  it('tidak menampilkan change ketika tidak diberikan', () => {
    render(<StatsCard label="Count" value={100} />)
    const changeElements = screen.queryAllByText(/\+/)
    expect(changeElements.length).toBe(0)
  })

  it('menerapkan variant class yang benar', () => {
    const { container, rerender } = render(
      <StatsCard label="Test" value={1} variant="default" />
    )
    expect(container.firstChild).toHaveClass('stat-card default')

    rerender(<StatsCard label="Test" value={1} variant="success" />)
    expect(container.firstChild).toHaveClass('stat-card success')

    rerender(<StatsCard label="Test" value={1} variant="warning" />)
    expect(container.firstChild).toHaveClass('stat-card warning')

    rerender(<StatsCard label="Test" value={1} variant="danger" />)
    expect(container.firstChild).toHaveClass('stat-card danger')
  })
})