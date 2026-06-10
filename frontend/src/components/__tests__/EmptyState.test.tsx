import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import EmptyState from '../EmptyState'

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>{children}</BrowserRouter>
)

describe('EmptyState Component', () => {
  it('menampilkan icon default jika tidak diberikan', () => {
    render(
      <EmptyState
        title="No Data"
        description="There are no items to display"
      />,
      { wrapper }
    )
    expect(screen.getByText('📋')).toBeInTheDocument()
  })

  it('menampilkan icon custom jika diberikan', () => {
    render(
      <EmptyState
        icon="🔍"
        title="Not Found"
        description="No results found"
      />,
      { wrapper }
    )
    expect(screen.getByText('🔍')).toBeInTheDocument()
  })

  it('menampilkan title dan description', () => {
    render(
      <EmptyState
        title="No Purchase Requisitions"
        description="You haven't created any PR yet"
      />,
      { wrapper }
    )
    expect(screen.getByText('No Purchase Requisitions')).toBeInTheDocument()
    expect(screen.getByText("You haven't created any PR yet")).toBeInTheDocument()
  })

  it('menampilkan action button dengan link ketika actionLink diberikan', () => {
    render(
      <EmptyState
        title="No Items"
        description="Create your first item"
        actionLabel="Create New"
        actionLink="/pr/new"
      />,
      { wrapper }
    )
    const button = screen.getByText('Create New')
    expect(button).toBeInTheDocument()
    expect(button.closest('a')).toHaveAttribute('href', '/pr/new')
  })

  it('memanggil onAction ketika button diklik dan onAction diberikan', () => {
    const handleAction = vi.fn()
    render(
      <EmptyState
        title="No Items"
        description="Create your first item"
        actionLabel="Refresh"
        onAction={handleAction}
      />,
      { wrapper }
    )
    const button = screen.getByText('Refresh')
    fireEvent.click(button)
    expect(handleAction).toHaveBeenCalledTimes(1)
  })

  it('tidak menampilkan button ketika actionLabel tidak diberikan', () => {
    render(
      <EmptyState
        title="No Items"
        description="Nothing to show"
      />,
      { wrapper }
    )
    const buttons = screen.queryAllByRole('button')
    const links = screen.queryAllByRole('link')
    expect(buttons.length).toBe(0)
    expect(links.length).toBe(0)
  })
})