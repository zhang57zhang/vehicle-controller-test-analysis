// 项目相关类型
export interface Project {
  id: number
  name: string
  description?: string
  dbc_file?: string
  created_at: string
  updated_at?: string
}

// 测试数据类型
export type TestDataFormat =
  | 'mat'
  | 'csv'
  | 'excel'
  | 'log'
  | 'blf'
  | 'asc'
  | 'xml'
  | 'json'

export interface TestDataType {
  type: 'MIL' | 'HIL' | 'DVP' | 'VEHICLE' | 'MANUAL' | 'AUTO'
}

export interface TestDataFile {
  id: number
  project_id: number
  file_name: string
  file_path: string
  file_size: number
  format: TestDataFormat
  data_type: TestDataType['type']
  uploaded_at: string
}

// DBC相关类型
export interface DBCFile {
  id: number
  project_id: number
  file_name: string
  file_path: string
  version?: string
  uploaded_at: string
}

export interface SignalMapping {
  id: number
  project_id: number
  signal_alias: string
  dbc_signal?: string
  data_source_signal?: string
  unit_conversion?: {
    from_unit: string
    to_unit: string
    formula: string
  }
  description?: string
}

export interface CustomSignal {
  id: number
  project_id: number
  signal_alias: string
  calculation: string
  input_signals: string[]
  unit: string
  description?: string
}

// 测试用例类型
export interface TestCase {
  id?: number
  project_id?: number
  tc_id: string
  tc_name: string
  test_phase: 'MIL' | 'HIL' | 'DVP' | 'VEHICLE' | 'MANUAL' | 'AUTO'
  pre_condition?: string
  test_steps?: string
  expected_result?: string
  priority?: 'High' | 'Medium' | 'Low'
  version?: string
  author?: string
  status?: string
  created_at?: string
}

export interface TestResult {
  id: number
  test_data_file_id: number
  tc_id: string
  tc_name?: string
  result: 'PASS' | 'FAIL' | 'BLOCKED'
  signal_name?: string
  measured_value?: string
  expected_min?: string
  expected_max?: string
  notes?: string
  executed_at: string
}

// 分析指标类型
export interface Indicator {
  id: string
  indicator_name: string
  indicator_type: 'function' | 'performance'
  signal_alias?: string
  check_type?: string
  calculation?: {
    formula: string
    input_signals: string[]
  }
  threshold?: {
    pass: string
    warning?: string
    fail: string
  }
  unit?: string
}

export interface AnalysisResult {
  id: number
  test_data_file_id: number
  indicator_id: string
  result_value: number | string | object
  result_status: 'pass' | 'warning' | 'fail' | 'error'
  notes?: string
  calculated_at: string
}

// 报告相关类型
export interface ReportTemplate {
  id: number
  template_name: string
  template_type: 'full' | 'oem'
  oem_id?: string
  sections: ReportSection[]
  created_at: string
  updated_at?: string
}

export interface ReportSection {
  section_id: string
  section_name: string
  required: boolean
  fields?: ReportField[]
}

export interface ReportField {
  field_id: string
  field_name: string
  field_type: 'text' | 'date' | 'number' | 'image' | 'chart'
  required?: boolean
  auto_generate?: boolean
}

export interface Report {
  id: number
  report_template_id: number
  test_data_file_id: number
  project_id: number
  report_type: 'standard' | 'traceability'
  report_number: string
  report_date: string
  version: string
  status: 'draft' | 'completed'
  created_at: string
}

// 时间同步相关类型
export interface TimeSyncConfig {
  target_sampling_rate?: number
  interpolation_method?: 'linear' | 'spline' | 'step'
  sync_events?: TimeSyncEvent[]
}

export interface TimeSyncEvent {
  event_name: string
  signal_name: string
  condition: string
}

export interface DataSyncInfo {
  source_file: string
  source_type: string
  original_timestamp: number
  aligned_timestamp: number
  time_offset: number
  interpolation_method: string
  data_quality: 'valid' | 'interpolated' | 'extrapolated'
}
