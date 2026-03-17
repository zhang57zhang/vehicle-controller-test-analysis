import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Dashboard from '../pages/Dashboard'

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('Dashboard', () => {
  it('应该渲染仪表盘标题', () => {
    renderWithRouter(<Dashboard />)
    expect(screen.getByText('仪表盘')).toBeInTheDocument()
  })

  it('应该显示统计卡片', () => {
    renderWithRouter(<Dashboard />)
    expect(screen.getByText('项目总数')).toBeInTheDocument()
    expect(screen.getByText('测试数据')).toBeInTheDocument()
    expect(screen.getByText('已通过用例')).toBeInTheDocument()
    expect(screen.getByText('待分析')).toBeInTheDocument()
  })
})
