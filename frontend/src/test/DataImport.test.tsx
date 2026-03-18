import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import DataImport from '../pages/DataImport'
import * as api from '../services/api'

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  }
})

// Mock API
vi.mock('../services/api', () => ({
  testDataApi: {
    uploadTestData: vi.fn(),
    getTestDataList: vi.fn(),
    deleteTestData: vi.fn(),
  },
  dbcApi: {
    uploadDBC: vi.fn(),
    getDBCList: vi.fn(),
    deleteDBC: vi.fn(),
  },
  testCaseApi: {
    importTestCases: vi.fn(),
  },
}))

// Mock Zustand store
const mockCurrentProject = {
  id: '1',
  name: '测试项目',
  description: '测试描述',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

vi.mock('../stores/project', () => ({
  useProjectStore: vi.fn(() => ({
    currentProject: mockCurrentProject,
    setCurrentProject: vi.fn(),
  })),
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('DataImport', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.testDataApi.getTestDataList).mockResolvedValue([])
    vi.mocked(api.dbcApi.getDBCList).mockResolvedValue([])
  })

  describe('页面渲染', () => {
    it('应该渲染数据导入标题', () => {
      renderWithRouter(<DataImport />)

      expect(screen.getByText('数据导入')).toBeInTheDocument()
    })

    it('应该显示当前项目信息', () => {
      renderWithRouter(<DataImport />)

      expect(screen.getByText('当前项目：')).toBeInTheDocument()
      expect(screen.getByText('测试项目')).toBeInTheDocument()
    })

    it('应该显示上传测试数据卡片', () => {
      renderWithRouter(<DataImport />)

      expect(screen.getByText('上传测试数据')).toBeInTheDocument()
    })

    it('应该显示上传DBC文件卡片', () => {
      renderWithRouter(<DataImport />)

      expect(screen.getByText('上传DBC文件')).toBeInTheDocument()
    })

    it('应该显示导入测试用例卡片', () => {
      renderWithRouter(<DataImport />)

      expect(screen.getByText('导入测试用例')).toBeInTheDocument()
    })

    it('应该显示已上传的测试数据卡片', () => {
      renderWithRouter(<DataImport />)

      expect(screen.getByText('已上传的测试数据')).toBeInTheDocument()
    })

    it('应该显示已上传的DBC文件卡片', () => {
      renderWithRouter(<DataImport />)

      expect(screen.getByText('已上传的DBC文件')).toBeInTheDocument()
    })
  })

  describe('文件上传组件', () => {
    it('应该显示测试数据拖拽上传区域', () => {
      renderWithRouter(<DataImport />)

      expect(screen.getByText('点击或拖拽文件到此区域上传')).toBeInTheDocument()
    })

    it('应该显示支持的测试数据格式', () => {
      renderWithRouter(<DataImport />)

      expect(screen.getByText('支持格式：.mat, .csv, .xlsx, .log, .blf, .asc, .xml, .json')).toBeInTheDocument()
    })

    it('应该显示支持的DBC文件格式', () => {
      renderWithRouter(<DataImport />)

      const dbcUploaders = screen.getAllByText('点击或拖拽文件到此区域上传')
      expect(dbcUploaders.length).toBeGreaterThanOrEqual(2)
    })

    it('应该显示DBC文件格式提示', () => {
      renderWithRouter(<DataImport />)

      expect(screen.getByText('支持格式：.dbc, .arxml, .xml')).toBeInTheDocument()
    })
  })

  describe('数据类型选择', () => {
    it('应该显示数据类型下拉选择', () => {
      renderWithRouter(<DataImport />)

      expect(screen.getByText('数据类型')).toBeInTheDocument()
    })

    it('应该显示所有可用的数据类型选项', () => {
      renderWithRouter(<DataImport />)

      expect(screen.getByText('请选择数据类型')).toBeInTheDocument()
    })
  })

  describe('测试用例导入', () => {
    it('应该显示测试用例上传按钮', () => {
      renderWithRouter(<DataImport />)

      expect(screen.getByText('选择Excel文件')).toBeInTheDocument()
    })

    it('应该显示支持的Excel格式提示', () => {
      renderWithRouter(<DataImport />)

      expect(screen.getByText('支持 .xlsx, .xls 格式的测试用例Excel文件')).toBeInTheDocument()
    })
  })

  describe('已上传文件列表', () => {
    it('应该加载并显示已上传的测试数据', async () => {
      const mockTestData = [
        {
          id: '1',
          project_id: '1',
          file_name: 'test_data.mat',
          file_path: '/path/to/test_data.mat',
          file_size: 1024 * 1024,
          format: 'mat',
          data_type: 'MANUAL',
          uploaded_at: '2024-01-01 00:00:00',
        },
      ]

      vi.mocked(api.testDataApi.getTestDataList).mockResolvedValue(mockTestData)

      renderWithRouter(<DataImport />)

      await waitFor(() => {
        expect(screen.getByText('test_data.mat')).toBeInTheDocument()
      })
    })

    it('应该显示测试数据的格式标签', async () => {
      const mockTestData = [
        {
          id: '1',
          project_id: '1',
          file_name: 'test_data.mat',
          file_path: '/path/to/test_data.mat',
          file_size: 1024 * 1024,
          format: 'mat',
          data_type: 'MANUAL',
          uploaded_at: '2024-01-01 00:00:00',
        },
      ]

      vi.mocked(api.testDataApi.getTestDataList).mockResolvedValue(mockTestData)

      renderWithRouter(<DataImport />)

      await waitFor(() => {
        expect(screen.getByText('MAT')).toBeInTheDocument()
      })
    })

    it('应该显示测试数据的数据类型标签', async () => {
      const mockTestData = [
        {
          id: '1',
          project_id: '1',
          file_name: 'test_data.mat',
          file_path: '/path/to/test_data.mat',
          file_size: 1024 * 1024,
          format: 'mat',
          data_type: 'MANUAL',
          uploaded_at: '2024-01-01 00:00:00',
        },
      ]

      vi.mocked(api.testDataApi.getTestDataList).mockResolvedValue(mockTestData)

      renderWithRouter(<DataImport />)

      await waitFor(() => {
        expect(screen.getByText('MANUAL')).toBeInTheDocument()
      })
    })

    it('应该显示测试数据的文件大小', async () => {
      const mockTestData = [
        {
          id: '1',
          project_id: '1',
          file_name: 'test_data.mat',
          file_path: '/path/to/test_data.mat',
          file_size: 1024 * 1024 * 2.5,
          format: 'mat',
          data_type: 'MANUAL',
          uploaded_at: '2024-01-01 00:00:00',
        },
      ]

      vi.mocked(api.testDataApi.getTestDataList).mockResolvedValue(mockTestData)

      renderWithRouter(<DataImport />)

      await waitFor(() => {
        expect(screen.getByText('2.50 MB')).toBeInTheDocument()
      })
    })

    it('应该加载并显示已上传的DBC文件', async () => {
      const mockDBCFiles = [
        {
          id: '1',
          project_id: '1',
          file_name: 'test.dbc',
          file_path: '/path/to/test.dbc',
          version: '1.0',
          uploaded_at: '2024-01-01 00:00:00',
        },
      ]

      vi.mocked(api.dbcApi.getDBCList).mockResolvedValue(mockDBCFiles)

      renderWithRouter(<DataImport />)

      await waitFor(() => {
        expect(screen.getByText('test.dbc')).toBeInTheDocument()
      })
    })

    it('应该显示DBC文件的版本', async () => {
      const mockDBCFiles = [
        {
          id: '1',
          project_id: '1',
          file_name: 'test.dbc',
          file_path: '/path/to/test.dbc',
          version: '1.0',
          uploaded_at: '2024-01-01 00:00:00',
        },
      ]

      vi.mocked(api.dbcApi.getDBCList).mockResolvedValue(mockDBCFiles)

      renderWithRouter(<DataImport />)

      await waitFor(() => {
        expect(screen.getByText('1.0')).toBeInTheDocument()
      })
    })
  })

  describe('删除文件功能', () => {
    it('点击删除测试数据应该显示确认对话框', async () => {
      const mockTestData = [
        {
          id: '1',
          project_id: '1',
          file_name: 'test_data.mat',
          file_path: '/path/to/test_data.mat',
          file_size: 1024 * 1024,
          format: 'mat',
          data_type: 'MANUAL',
          uploaded_at: '2024-01-01 00:00:00',
        },
      ]

      vi.mocked(api.testDataApi.getTestDataList).mockResolvedValue(mockTestData)

      renderWithRouter(<DataImport />)

      await waitFor(() => {
        expect(screen.getByText('test_data.mat')).toBeInTheDocument()
      })

      const deleteButton = screen.getByText('删除')
      fireEvent.click(deleteButton)

      await waitFor(() => {
        expect(screen.getByText('确认删除')).toBeInTheDocument()
      })
    })

    it('确认删除测试数据应该调用删除API', async () => {
      const mockTestData = [
        {
          id: '1',
          project_id: '1',
          file_name: 'test_data.mat',
          file_path: '/path/to/test_data.mat',
          file_size: 1024 * 1024,
          format: 'mat',
          data_type: 'MANUAL',
          uploaded_at: '2024-01-01 00:00:00',
        },
      ]

      vi.mocked(api.testDataApi.getTestDataList).mockResolvedValue(mockTestData)
      vi.mocked(api.testDataApi.deleteTestData).mockResolvedValue(undefined)

      renderWithRouter(<DataImport />)

      await waitFor(() => {
        expect(screen.getByText('test_data.mat')).toBeInTheDocument()
      })

      const deleteButton = screen.getByText('删除')
      fireEvent.click(deleteButton)

      await waitFor(() => {
        expect(screen.getByText('确定')).toBeInTheDocument()
      })

      const confirmButton = screen.getByText('确定')
      fireEvent.click(confirmButton)

      await waitFor(() => {
        expect(api.testDataApi.deleteTestData).toHaveBeenCalledWith('1')
      })
    })
  })

  describe('空状态处理', () => {
    it('没有测试数据时应显示空状态', async () => {
      vi.mocked(api.testDataApi.getTestDataList).mockResolvedValue([])

      renderWithRouter(<DataImport />)

      await waitFor(() => {
        expect(screen.getByText('暂无测试数据')).toBeInTheDocument()
      })
    })

    it('没有DBC文件时应显示空状态', async () => {
      vi.mocked(api.dbcApi.getDBCList).mockResolvedValue([])

      renderWithRouter(<DataImport />)

      await waitFor(() => {
        expect(screen.getByText('暂无DBC文件')).toBeInTheDocument()
      })
    })
  })
})
