from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "车载控制器测试数据分析系统"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # API配置
    API_PREFIX: str = "/api"

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/vehicle_test.db"

    # 文件上传配置
    UPLOAD_DIR: str = "./data/uploads"
    PROCESSED_DIR: str = "./data/processed"
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB

    # 允许的文件类型
    ALLOWED_MAT_EXTENSIONS: set = {".mat"}
    ALLOWED_CSV_EXTENSIONS: set = {".csv"}
    ALLOWED_EXCEL_EXTENSIONS: set = {".xlsx", ".xls"}
    ALLOWED_CAN_EXTENSIONS: set = {".log", ".blf", ".asc"}
    ALLOWED_DBC_EXTENSIONS: set = {".dbc", ".arxml", ".xml"}
    ALLOWED_TEST_EXTENSIONS: set = {".xml", ".json"}

    # 报告生成配置
    REPORT_DIR: str = "./data/reports"
    TEMP_DIR: str = "./data/temp"

    # 跨域配置
    CORS_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
