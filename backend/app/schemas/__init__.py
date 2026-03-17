from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# 项目相关Schema
class ProjectBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    dbc_file: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ProjectBase):
    pass


class Project(ProjectBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 测试数据文件相关Schema
class TestDataFileBase(BaseModel):
    file_name: str
    file_size: int
    format: str
    data_type: str


class TestDataFileCreate(TestDataBase):
    pass


class TestDataFile(TestDataFileBase):
    id: int
    project_id: int
    file_path: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


# DBC文件相关Schema
class DBCFileBase(BaseModel):
    file_name: str
    version: Optional[str] = None


class DBCFileCreate(DBCFileBase):
    pass


class DBCFile(DBCFileBase):
    id: int
    project_id: int
    file_path: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


# 信号映射相关Schema
class UnitConversion(BaseModel):
    from_unit: str
    to_unit: str
    formula: str


class SignalMappingBase(BaseModel):
    signal_alias: str
    dbc_signal: Optional[str] = None
    data_source_signal: Optional[str] = None
    unit_conversion: Optional[UnitConversion] = None
    description: Optional[str] = None


class SignalMappingCreate(SignalMappingBase):
    pass


class SignalMappingUpdate(SignalMappingBase):
    pass


class SignalMapping(SignalMappingBase):
    id: int
    project_id: int

    class Config:
        from_attributes = True


# 自定义信号相关Schema
class CustomSignalBase(BaseModel):
    signal_alias: str
    calculation: str
    input_signals: List[str]
    unit: Optional[str] = None
    description: Optional[str] = None


class CustomSignalCreate(CustomSignalBase):
    pass


class CustomSignalUpdate(CustomSignalBase):
    pass


class CustomSignal(CustomSignalBase):
    id: int
    project_id: int

    class Config:
        from_attributes = True


# 测试用例相关Schema
class TestCaseBase(BaseModel):
    tc_id: str
    tc_name: str
    test_phase: str
    pre_condition: Optional[str] = None
    test_steps: Optional[str] = None
    expected_result: Optional[str] = None
    priority: Optional[str] = None


class TestCase(TestCaseBase):
    id: int
    project_id: int

    class Config:
        from_attributes = True


# 测试结果相关Schema
class TestResultBase(BaseModel):
    tc_id: str
    result: str
    signal_name: Optional[str] = None
    measured_value: Optional[str] = None
    expected_min: Optional[str] = None
    expected_max: Optional[str] = None
    notes: Optional[str] = None


class TestResult(TestResultBase):
    id: int
    test_data_file_id: int
    executed_at: datetime

    class Config:
        from_attributes = True


# 分析结果相关Schema
class AnalysisResultBase(BaseModel):
    indicator_id: str
    result_value: str
    result_status: str
    notes: Optional[str] = None


class AnalysisResult(AnalysisResultBase):
    id: int
    test_data_file_id: int
    calculated_at: datetime

    class Config:
        from_attributes = True


# 报告模板相关Schema
class ReportField(BaseModel):
    field_id: str
    field_name: str
    field_type: str
    required: Optional[bool] = False
    auto_generate: Optional[bool] = False


class ReportSection(BaseModel):
    section_id: str
    section_name: str
    required: bool
    fields: Optional[List[ReportField]] = None


class ReportTemplateBase(BaseModel):
    template_name: str
    template_type: str
    oem_id: Optional[str] = None
    sections: List[ReportSection]


class ReportTemplateCreate(ReportTemplateBase):
    pass


class ReportTemplate(ReportTemplateBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 报告相关Schema
class ReportBase(BaseModel):
    report_type: str
    report_number: str
    report_date: str
    version: str


class ReportCreate(ReportBase):
    template_id: int


class Report(ReportBase):
    id: int
    report_template_id: int
    test_data_file_id: int
    project_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# 时间同步相关Schema
class TimeSyncEvent(BaseModel):
    event_name: str
    signal_name: str
    condition: str


class TimeSyncConfig(BaseModel):
    target_sampling_rate: Optional[float] = None
    interpolation_method: Optional[str] = "linear"
    sync_events: Optional[List[TimeSyncEvent]] = None


# 分析请求Schema
class AnalysisRequest(BaseModel):
    time_sync: Optional[TimeSyncConfig] = None
    indicators: Optional[List[str]] = None


# 通用响应Schema
class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
