import axios from 'axios'
import type { Project, TestDataFile, DBCFile, SignalMapping, CustomSignal, TestCase, ReportTemplate, Report } from '../types'

const API_BASE_URL = (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 项目管理API
export const projectApi = {
  // 获取项目列表
  getProjects: async () => {
    const response = await api.get<Project[]>('/projects')
    return response.data
  },

  // 获取项目详情
  getProject: async (id: string) => {
    const response = await api.get<Project>(`/projects/${id}`)
    return response.data
  },

  // 创建项目
  createProject: async (data: Partial<Project>) => {
    const response = await api.post<Project>('/projects', data)
    return response.data
  },

  // 更新项目
  updateProject: async (id: string, data: Partial<Project>) => {
    const response = await api.put<Project>(`/projects/${id}`, data)
    return response.data
  },

  // 删除项目
  deleteProject: async (id: string) => {
    await api.delete(`/projects/${id}`)
  },
}

// 测试数据管理API
export const testDataApi = {
  // 上传测试数据文件
  uploadTestData: async (projectId: string, formData: FormData) => {
    const response = await api.post<TestDataFile>(`/projects/${projectId}/test-data/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // 获取项目的测试数据列表
  getTestDataList: async (projectId: string) => {
    const response = await api.get<TestDataFile[]>(`/projects/${projectId}/test-data`)
    return response.data
  },

  // 获取测试数据详情
  getTestData: async (id: string) => {
    const response = await api.get<TestDataFile>(`/test-data/${id}`)
    return response.data
  },

  // 删除测试数据
  deleteTestData: async (id: string) => {
    await api.delete(`/test-data/${id}`)
  },
}

// DBC管理API
export const dbcApi = {
  // 上传DBC文件
  uploadDBC: async (projectId: string, formData: FormData) => {
    const response = await api.post<DBCFile>(`/projects/${projectId}/dbc/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // 获取项目的DBC文件列表
  getDBCList: async (projectId: string) => {
    const response = await api.get<DBCFile[]>(`/projects/${projectId}/dbc`)
    return response.data
  },

  // 解析DBC文件
  parseDBC: async (dbcId: string) => {
    const response = await api.post(`/dbc/${dbcId}/parse`)
    return response.data
  },

  // 删除DBC文件
  deleteDBC: async (id: string) => {
    await api.delete(`/dbc/${id}`)
  },
}

// 信号映射API
export const signalMappingApi = {
  // 获取信号映射列表
  getSignalMappings: async (projectId: string) => {
    const response = await api.get<SignalMapping[]>(`/projects/${projectId}/signal-mappings`)
    return response.data
  },

  // 创建信号映射
  createSignalMapping: async (projectId: string, data: Partial<SignalMapping>) => {
    const response = await api.post<SignalMapping>(`/projects/${projectId}/signal-mappings`, data)
    return response.data
  },

  // 更新信号映射
  updateSignalMapping: async (id: string, data: Partial<SignalMapping>) => {
    const response = await api.put<SignalMapping>(`/signal-mappings/${id}`, data)
    return response.data
  },

  // 删除信号映射
  deleteSignalMapping: async (id: string) => {
    await api.delete(`/signal-mappings/${id}`)
  },

  // 导入信号映射配置
  importSignalMappings: async (projectId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post(`/projects/${projectId}/signal-mappings/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // 导出信号映射配置
  exportSignalMappings: async (projectId: string) => {
    const response = await api.get(`/projects/${projectId}/signal-mappings/export`, {
      responseType: 'blob',
    })
    return response.data
  },
}

// 自定义信号API
export const customSignalApi = {
  // 获取自定义信号列表
  getCustomSignals: async (projectId: string) => {
    const response = await api.get<CustomSignal[]>(`/projects/${projectId}/custom-signals`)
    return response.data
  },

  // 创建自定义信号
  createCustomSignal: async (projectId: string, data: Partial<CustomSignal>) => {
    const response = await api.post<CustomSignal>(`/projects/${projectId}/custom-signals`, data)
    return response.data
  },

  // 更新自定义信号
  updateCustomSignal: async (id: string, data: Partial<CustomSignal>) => {
    const response = await api.put<CustomSignal>(`/custom-signals/${id}`, data)
    return response.data
  },

  // 删除自定义信号
  deleteCustomSignal: async (id: string) => {
    await api.delete(`/custom-signals/${id}`)
  },
}

// 测试用例API
export const testCaseApi = {
  // 导入测试用例Excel
  importTestCases: async (projectId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post(`/projects/${projectId}/test-cases/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // 获取测试用例列表
  getTestCases: async (projectId: string) => {
    const response = await api.get<TestCase[]>(`/projects/${projectId}/test-cases`)
    return response.data
  },

  // 导出测试结果
  exportTestResults: async (testDataId: string, format: 'excel' | 'csv') => {
    const response = await api.get(`/test-data/${testDataId}/results/export?format=${format}`, {
      responseType: 'blob',
    })
    return response.data
  },
}

// 数据分析API
export const analysisApi = {
  // 执行数据分析
  executeAnalysis: async (testDataId: string, options: {
    timeSync?: any
    indicators?: string[]
  }) => {
    const response = await api.post(`/test-data/${testDataId}/analyze`, options)
    return response.data
  },

  // 获取分析结果
  getAnalysisResults: async (testDataId: string) => {
    const response = await api.get(`/test-data/${testDataId}/analysis-results`)
    return response.data
  },
}

// 报告API
export const reportApi = {
  // 获取报告模板列表
  getReportTemplates: async () => {
    const response = await api.get<ReportTemplate[]>('/report-templates')
    return response.data
  },

  // 创建报告模板
  createReportTemplate: async (data: Partial<ReportTemplate>) => {
    const response = await api.post<ReportTemplate>('/report-templates', data)
    return response.data
  },

  // 生成报告
  generateReport: async (testDataId: string, options: {
    templateId: string
    reportType: 'standard' | 'traceability'
    format?: 'pdf' | 'word'
  }) => {
    const response = await api.post<Report>(`/test-data/${testDataId}/reports/generate`, options)
    return response.data
  },

  // 下载报告
  downloadReport: async (reportId: string, format: 'pdf' | 'word') => {
    const response = await api.get(`/reports/${reportId}/download?format=${format}`, {
      responseType: 'blob',
    })
    return response.data
  },

  // 获取报告列表
  getReports: async (projectId: string) => {
    const response = await api.get<Report[]>(`/projects/${projectId}/reports`)
    return response.data
  },
}

export default api
