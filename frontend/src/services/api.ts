import axios from 'axios'
import type { Project, TestDataFile, DBCFile, SignalMapping, CustomSignal, TestCase, ReportTemplate, Report } from '../types'

const API_BASE_URL = (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

type ID = string | number

// 项目管理API
export const projectApi = {
  getProjects: async () => {
    const response = await api.get<Project[]>('/projects')
    return response.data
  },

  getProject: async (id: ID) => {
    const response = await api.get<Project>(`/projects/${id}`)
    return response.data
  },

  createProject: async (data: Partial<Project>) => {
    const response = await api.post<Project>('/projects', data)
    return response.data
  },

  updateProject: async (id: ID, data: Partial<Project>) => {
    const response = await api.put<Project>(`/projects/${id}`, data)
    return response.data
  },

  deleteProject: async (id: ID) => {
    await api.delete(`/projects/${id}`)
  },
}

// 测试数据管理API
export const testDataApi = {
  uploadTestData: async (projectId: ID, formData: FormData) => {
    const response = await api.post<TestDataFile>(`/projects/${projectId}/test-data/upload`, formData)
    return response.data
  },

  getTestDataList: async (projectId: ID) => {
    const response = await api.get<TestDataFile[]>(`/projects/${projectId}/test-data`)
    return response.data
  },

  getTestData: async (id: ID) => {
    const response = await api.get<TestDataFile>(`/test-data/${id}`)
    return response.data
  },

  deleteTestData: async (id: ID) => {
    await api.delete(`/test-data/${id}`)
  },
}

// DBC管理API
export const dbcApi = {
  uploadDBC: async (projectId: ID, formData: FormData) => {
    const response = await api.post<DBCFile>(`/projects/${projectId}/dbc/upload`, formData)
    return response.data
  },

  getDBCList: async (projectId: ID) => {
    const response = await api.get<DBCFile[]>(`/projects/${projectId}/dbc`)
    return response.data
  },

  parseDBC: async (dbcId: ID) => {
    const response = await api.post(`/dbc/${dbcId}/parse`)
    return response.data
  },

  deleteDBC: async (id: ID) => {
    await api.delete(`/dbc/${id}`)
  },
}

// 信号映射API
export const signalMappingApi = {
  getSignalMappings: async (projectId: ID) => {
    const response = await api.get<SignalMapping[]>(`/projects/${projectId}/signal-mappings`)
    return response.data
  },

  createSignalMapping: async (projectId: ID, data: Partial<SignalMapping>) => {
    const response = await api.post<SignalMapping>(`/projects/${projectId}/signal-mappings`, data)
    return response.data
  },

  updateSignalMapping: async (id: ID, data: Partial<SignalMapping>) => {
    const response = await api.put<SignalMapping>(`/signal-mappings/${id}`, data)
    return response.data
  },

  deleteSignalMapping: async (id: ID) => {
    await api.delete(`/signal-mappings/${id}`)
  },

  importSignalMappings: async (projectId: ID, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post(`/projects/${projectId}/signal-mappings/import`, formData)
    return response.data
  },

  exportSignalMappings: async (projectId: ID) => {
    const response = await api.get(`/projects/${projectId}/signal-mappings/export`, {
      responseType: 'blob',
    })
    return response.data
  },
}

// 自定义信号API
export const customSignalApi = {
  getCustomSignals: async (projectId: ID) => {
    const response = await api.get<CustomSignal[]>(`/projects/${projectId}/custom-signals`)
    return response.data
  },

  createCustomSignal: async (projectId: ID, data: Partial<CustomSignal>) => {
    const response = await api.post<CustomSignal>(`/projects/${projectId}/custom-signals`, data)
    return response.data
  },

  updateCustomSignal: async (id: ID, data: Partial<CustomSignal>) => {
    const response = await api.put<CustomSignal>(`/custom-signals/${id}`, data)
    return response.data
  },

  deleteCustomSignal: async (id: ID) => {
    await api.delete(`/custom-signals/${id}`)
  },
}

// 测试用例API
export const testCaseApi = {
  importTestCases: async (projectId: ID, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post(`/projects/${projectId}/test-cases/import`, formData)
    return response.data
  },

  getTestCases: async (projectId: ID) => {
    const response = await api.get<TestCase[]>(`/projects/${projectId}/test-cases`)
    return response.data
  },

  exportTestResults: async (testDataId: ID, format: 'excel' | 'csv') => {
    const response = await api.get(`/test-data/${testDataId}/results/export?format=${format}`, {
      responseType: 'blob',
    })
    return response.data
  },
}

// 数据分析API
export const analysisApi = {
  executeAnalysis: async (testDataId: ID, options: {
    time_sync?: any
    indicators?: any[]
  }) => {
    const response = await api.post(`/test-data/${testDataId}/analyze`, options)
    return response.data
  },

  getAnalysisResults: async (testDataId: ID) => {
    const response = await api.get(`/test-data/${testDataId}/analysis-results`)
    return response.data
  },

  getAvailableSignals: async (testDataId: ID) => {
    const response = await api.get(`/test-data/${testDataId}/signals`)
    return response.data
  },

  getSignalTimeSeries: async (testDataId: ID, signalNames: string[], options?: {
    startTime?: number
    endTime?: number
    maxPoints?: number
  }) => {
    const response = await api.post(`/test-data/${testDataId}/signal-timeseries`, {
      signal_names: signalNames,
      start_time: options?.startTime,
      end_time: options?.endTime,
      max_points: options?.maxPoints
    })
    return response.data
  }
}

// 报告API
export const reportApi = {
  getReportTemplates: async () => {
    const response = await api.get<ReportTemplate[]>('/report-templates')
    return response.data
  },

  createReportTemplate: async (data: Partial<ReportTemplate>) => {
    const response = await api.post<ReportTemplate>('/report-templates', data)
    return response.data
  },

  generateReport: async (testDataId: ID, options: {
    templateId?: ID
    reportType: 'standard' | 'traceability'
    format?: 'pdf' | 'word'
    author?: string
    reviewer?: string
    approver?: string
  }) => {
    const response = await api.post<Report>(`/test-data/${testDataId}/reports/generate`, options)
    return response.data
  },

  downloadReport: async (reportId: ID, format: 'pdf' | 'word') => {
    const response = await api.get(`/reports/${reportId}/download?format=${format}`, {
      responseType: 'blob',
    })
    return response.data
  },

  getReports: async (projectId: ID) => {
    const response = await api.get<Report[]>(`/projects/${projectId}/reports`)
    return response.data
  },
}

export default api
