from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    dbc_file = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    test_data_files = relationship("TestDataFile", back_populates="project")
    dbc_files = relationship("DBCFile", back_populates="project")
    signal_mappings = relationship("SignalMapping", back_populates="project")
    custom_signals = relationship("CustomSignal", back_populates="project")
    reports = relationship("Report", back_populates="project")


class TestDataFile(Base):
    __tablename__ = "test_data_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    format = Column(String(50), nullable=False)  # mat, csv, excel, log, blf, asc, xml, json
    data_type = Column(String(50), nullable=False)  # MIL, HIL, DVP, VEHICLE, MANUAL, AUTO
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    project = relationship("Project", back_populates="test_data_files")
    test_results = relationship("TestResult", back_populates="test_data_file")
    analysis_results = relationship("AnalysisResult", back_populates="test_data_file")
    reports = relationship("Report", back_populates="test_data_file")


class DBCFile(Base):
    __tablename__ = "dbc_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    version = Column(String(50), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    project = relationship("Project", back_populates="dbc_files")


class SignalMapping(Base):
    __tablename__ = "signal_mappings"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    signal_alias = Column(String(200), nullable=False, index=True)
    dbc_signal = Column(String(200), nullable=True)
    data_source_signal = Column(String(200), nullable=True)
    unit_conversion_from_unit = Column(String(50), nullable=True)
    unit_conversion_to_unit = Column(String(50), nullable=True)
    unit_conversion_formula = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)

    # 关系
    project = relationship("Project", back_populates="signal_mappings")


class CustomSignal(Base):
    __tablename__ = "custom_signals"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    signal_alias = Column(String(200), nullable=False, index=True)
    calculation = Column(Text, nullable=False)
    input_signals = Column(Text, nullable=True)  # JSON array of signal names
    unit = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    # 关系
    project = relationship("Project", back_populates="custom_signals")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    tc_id = Column(String(100), nullable=False, index=True)
    tc_name = Column(String(500), nullable=False)
    test_phase = Column(String(50), nullable=False)  # MIL, HIL, DVP, VEHICLE, MANUAL, AUTO
    pre_condition = Column(Text, nullable=True)
    test_steps = Column(Text, nullable=True)
    expected_result = Column(Text, nullable=True)
    priority = Column(String(20), nullable=True)  # High, Medium, Low

    # 关系
    test_results = relationship("TestResult", back_populates="test_case")


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    test_data_file_id = Column(Integer, ForeignKey("test_data_files.id"), nullable=False, index=True)
    tc_id = Column(String(100), nullable=False, index=True)
    result = Column(String(20), nullable=False)  # PASS, FAIL, BLOCKED
    signal_name = Column(String(200), nullable=True)
    measured_value = Column(String(200), nullable=True)
    expected_min = Column(String(50), nullable=True)
    expected_max = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    test_data_file = relationship("TestDataFile", back_populates="test_results")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    test_data_file_id = Column(Integer, ForeignKey("test_data_files.id"), nullable=False, index=True)
    indicator_id = Column(String(100), nullable=False)
    result_value = Column(String(500), nullable=False)
    result_status = Column(String(20), nullable=False)  # pass, warning, fail
    notes = Column(Text, nullable=True)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    test_data_file = relationship("TestDataFile", back_populates="analysis_results")


class ReportTemplate(Base):
    __tablename__ = "report_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(200), nullable=False)
    template_type = Column(String(50), nullable=False)  # full, oem
    oem_id = Column(String(100), nullable=True)
    sections = Column(Text, nullable=False)  # JSON array of sections
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    reports = relationship("Report", back_populates="report_template")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    report_template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=False)
    test_data_file_id = Column(Integer, ForeignKey("test_data_files.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    report_type = Column(String(50), nullable=False)  # standard, traceability
    report_number = Column(String(100), nullable=False, unique=True)
    report_date = Column(String(50), nullable=False)
    version = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)  # draft, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    project = relationship("Project", back_populates="reports")
    test_data_file = relationship("TestDataFile", back_populates="reports")
    report_template = relationship("ReportTemplate", back_populates="reports")
