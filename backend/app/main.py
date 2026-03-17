from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api import projects, test_data, dbc, signal_mappings, custom_signals, test_cases, analysis, reports

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(test_data.router, prefix="/api", tags=["test_data"])
app.include_router(dbc.router, prefix="/api", tags=["dbc"])
app.include_router(signal_mappings.router, prefix="/api", tags=["signal_mappings"])
app.include_router(custom_signals.router, prefix="/api", tags=["custom_signals"])
app.include_router(test_cases.router, prefix="/api", tags=["test_cases"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(reports.router, prefix="/api", tags=["reports"])


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
