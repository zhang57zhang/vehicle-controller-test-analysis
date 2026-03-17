// 项目相关类型
export interface Project {
  id: string
  name: string
  description?: string
  dbc_file?: string
  created_at: string
  updated_at: string
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
  id: string
  project_id: string
  file_name: string
  file_path: string
  file_size: number
  format: TestDataFormat
  data_type: TestDataType['type']
  uploaded_at: string
}

// DBC相关类型
export interface DBCFile {
  id: string
  project_id: string
  file_name: string
  file_path: string
  version?: string
  uploaded_at: string
}

export interface SignalMapping {
  id: string
  project_id: string
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
  id: string
  project_id: string
  signal_alias: string
  calculation: string
  input_signals: string[]
  unit: string
  description?: string
}

// 测试用例类型
export interface TestCase {
  tc_id: string
  tc_name: string
  test_phase: 'MIL' | 'HIL' | 'DVP' | 'VEHICLE' | 'MANUAL' | 'AUTO'
  pre_condition?: string
  test_steps?: string
  expected_result?: string
  priority?: 'High' | 'Medium' | 'Low'
}

export interface TestResult {
  id: string
  test_data_file_id: string
  tc_id: string
  result: 'PASS' | 'FAIL' | 'BLOCKED'
  signal_name?: string
  measured_value?: number
  expected_range?: {
    min: number
    max: number
  }
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
  id: string
  test_data_file_id: string
  indicator_id: string
  result_value: number | string
  result_status: 'pass' | 'warning' | 'fail'
  notes?: string
  calculated_at: string
}

// 报告相关类型
export interface ReportTemplate {
  id: string
  template_name: string
  template_type: 'full' | 'oem'
  oem_id?: string
  sections: ReportSection[]
  created_at: string
  updated_at: string
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
  id: string
  report_template_id: string
  test_data_file_id: string
  project_id: string
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
