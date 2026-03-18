import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import ProjectManager from '../pages/ProjectManager'
import * as api from '../services/api'

// 创建 navigate mock
const navigateMock = vi.fn()

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

// Mock API
vi.mock('../services/api', () => ({
  projectApi: {
    getProjects: vi.fn(),
    createProject: vi.fn(),
    updateProject: vi.fn(),
    deleteProject: vi.fn(),
  },
}))

// Mock Zustand store
const setProjectsMock = vi.fn()
const addProjectMock = vi.fn()
const updateProjectMock = vi.fn()
const removeProjectMock = vi.fn()

vi.mock('../stores/project', () => ({
  useProjectStore: vi.fn(() => ({
    projects: [],
    setProjects: setProjectsMock,
    addProject: addProjectMock,
    updateProject: updateProjectMock,
    removeProject: removeProjectMock,
  })),
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('ProjectManager', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('项目列表渲染', () => {
    it('应该渲染项目管理页面标题', async () => {
      vi.mocked(api.projectApi.getProjects).mockResolvedValue([])

      renderWithRouter(<ProjectManager />)

      expect(screen.getByText('项目管理')).toBeInTheDocument()
    })

    it('应该显示新建项目按钮', async () => {
      vi.mocked(api.projectApi.getProjects).mockResolvedValue([])

      renderWithRouter(<ProjectManager />)

      expect(screen.getByText('新建项目')).toBeInTheDocument()
    })

    it('应该成功加载并显示项目列表', async () => {
      const mockProjects = [
        {
          id: '1',
          name: '测试项目1',
          description: '这是测试项目1的描述',
          dbc_file: 'test.dbc',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        {
          id: '2',
          name: '测试项目2',
          description: '这是测试项目2的描述',
          created_at: '2024-01-02T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      ]

      vi.mocked(api.projectApi.getProjects).mockResolvedValue(mockProjects)

      renderWithRouter(<ProjectManager />)

      await waitFor(() => {
        expect(screen.getByText('测试项目1')).toBeInTheDocument()
        expect(screen.getByText('测试项目2')).toBeInTheDocument()
      })
    })

    it('应该显示已配置DBC标签', async () => {
      const mockProjects = [
        {
          id: '1',
          name: '测试项目1',
          description: '测试描述',
          dbc_file: 'test.dbc',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      vi.mocked(api.projectApi.getProjects).mockResolvedValue(mockProjects)

      renderWithRouter(<ProjectManager />)

      await waitFor(() => {
        expect(screen.getByText('已配置')).toBeInTheDocument()
      })
    })

    it('应该显示未配置DBC标签', async () => {
      const mockProjects = [
        {
          id: '1',
          name: '测试项目1',
          description: '测试描述',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      vi.mocked(api.projectApi.getProjects).mockResolvedValue(mockProjects)

      renderWithRouter(<ProjectManager />)

      await waitFor(() => {
        expect(screen.getByText('未配置')).toBeInTheDocument()
      })
    })
  })

  describe('创建项目功能', () => {
    it('点击新建项目按钮应该打开模态框', async () => {
      vi.mocked(api.projectApi.getProjects).mockResolvedValue([])

      renderWithRouter(<ProjectManager />)

      const createButton = screen.getByText('新建项目')
      fireEvent.click(createButton)

      await waitFor(() => {
        expect(screen.getByText('新建项目')).toBeInTheDocument()
      })
    })

    it('应该显示创建项目表单字段', async () => {
      vi.mocked(api.projectApi.getProjects).mockResolvedValue([])

      renderWithRouter(<ProjectManager />)

      const createButton = screen.getByText('新建项目')
      fireEvent.click(createButton)

      await waitFor(() => {
        expect(screen.getByText('项目名称')).toBeInTheDocument()
        expect(screen.getByText('项目描述')).toBeInTheDocument()
      })
    })

    it('应该成功创建项目', async () => {
      const newProject = {
        id: '3',
        name: '新项目',
        description: '新项目描述',
        created_at: '2024-01-03T00:00:00Z',
        updated_at: '2024-01-03T00:00:00Z',
      }

      vi.mocked(api.projectApi.getProjects).mockResolvedValue([])
      vi.mocked(api.projectApi.createProject).mockResolvedValue(newProject)

      renderWithRouter(<ProjectManager />)

      // 打开创建模态框
      fireEvent.click(screen.getByText('新建项目'))

      await waitFor(() => {
        expect(screen.getByText('新建项目')).toBeInTheDocument()
      })

      // 填写表单
      const nameInput = screen.getByPlaceholderText('请输入项目名称')
      fireEvent.change(nameInput, { target: { value: '新项目' } })

      const descriptionInput = screen.getByPlaceholderText('请输入项目描述（可选）')
      fireEvent.change(descriptionInput, { target: { value: '新项目描述' } })

      // 提交表单
      const submitButton = screen.getByText('确定')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(api.projectApi.createProject).toHaveBeenCalledWith({
          name: '新项目',
          description: '新项目描述',
        })
      })
    })
  })

  describe('编辑项目功能', () => {
    it('点击编辑按钮应该打开编辑模态框', async () => {
      const mockProjects = [
        {
          id: '1',
          name: '测试项目1',
          description: '测试描述',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      vi.mocked(api.projectApi.getProjects).mockResolvedValue(mockProjects)

      renderWithRouter(<ProjectManager />)

      await waitFor(() => {
        expect(screen.getByText('测试项目1')).toBeInTheDocument()
      })

      const editButtons = screen.getAllByText('编辑')
      fireEvent.click(editButtons[0])

      await waitFor(() => {
        expect(screen.getByText('编辑项目')).toBeInTheDocument()
      })
    })

    it('应该成功更新项目', async () => {
      const mockProjects = [
        {
          id: '1',
          name: '测试项目1',
          description: '测试描述',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      const updatedProject = {
        id: '1',
        name: '更新后的项目',
        description: '更新后的描述',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-04T00:00:00Z',
      }

      vi.mocked(api.projectApi.getProjects).mockResolvedValue(mockProjects)
      vi.mocked(api.projectApi.updateProject).mockResolvedValue(updatedProject)

      renderWithRouter(<ProjectManager />)

      await waitFor(() => {
        expect(screen.getByText('测试项目1')).toBeInTheDocument()
      })

      // 点击编辑按钮
      const editButtons = screen.getAllByText('编辑')
      fireEvent.click(editButtons[0])

      await waitFor(() => {
        expect(screen.getByText('编辑项目')).toBeInTheDocument()
      })

      // 修改项目名称
      const nameInput = screen.getByDisplayValue('测试项目1')
      fireEvent.change(nameInput, { target: { value: '更新后的项目' } })

      // 提交表单
      const submitButton = screen.getByText('确定')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(api.projectApi.updateProject).toHaveBeenCalledWith('1', {
          name: '更新后的项目',
          description: '测试描述',
        })
      })
    })
  })

  describe('删除项目功能', () => {
    it('点击删除按钮应该显示确认对话框', async () => {
      const mockProjects = [
        {
          id: '1',
          name: '测试项目1',
          description: '测试描述',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      vi.mocked(api.projectApi.getProjects).mockResolvedValue(mockProjects)

      renderWithRouter(<ProjectManager />)

      await waitFor(() => {
        expect(screen.getByText('测试项目1')).toBeInTheDocument()
      })

      const deleteButton = screen.getByText('删除')
      fireEvent.click(deleteButton)

      await waitFor(() => {
        expect(screen.getByText('删除项目')).toBeInTheDocument()
        expect(screen.getByText('确定要删除这个项目吗？')).toBeInTheDocument()
      })
    })

    it('确认删除应该调用删除API', async () => {
      const mockProjects = [
        {
          id: '1',
          name: '测试项目1',
          description: '测试描述',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      vi.mocked(api.projectApi.getProjects).mockResolvedValue(mockProjects)
      vi.mocked(api.projectApi.deleteProject).mockResolvedValue(undefined)

      renderWithRouter(<ProjectManager />)

      await waitFor(() => {
        expect(screen.getByText('测试项目1')).toBeInTheDocument()
      })

      // 点击删除按钮
      const deleteButton = screen.getByText('删除')
      fireEvent.click(deleteButton)

      await waitFor(() => {
        expect(screen.getByText('确定要删除这个项目吗？')).toBeInTheDocument()
      })

      // 确认删除
      const confirmButton = screen.getByText('确定')
      fireEvent.click(confirmButton)

      await waitFor(() => {
        expect(api.projectApi.deleteProject).toHaveBeenCalledWith('1')
      })
    })
  })

  describe('查看项目功能', () => {
    it('点击查看按钮应该导航到项目详情页', async () => {
      const mockNavigate = vi.fn()
      vi.mock('react-router-dom', async () => {
        const actual = await vi.importActual('react-router-dom')
        return {
          ...actual,
          useNavigate: () => mockNavigate,
        }
      })

      const mockProjects = [
        {
          id: '1',
          name: '测试项目1',
          description: '测试描述',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      vi.mocked(api.projectApi.getProjects).mockResolvedValue(mockProjects)

      renderWithRouter(<ProjectManager />)

      await waitFor(() => {
        expect(screen.getByText('测试项目1')).toBeInTheDocument()
      })

      // 点击查看按钮
      const viewButton = screen.getByText('查看')
      fireEvent.click(viewButton)

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/projects/1')
      })
    })
  })
})
