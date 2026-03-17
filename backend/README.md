# 车载控制器测试数据分析系统 - 后端

FastAPI后端API服务

## 安装依赖

```bash
pip install -e ".[dev]"
```

## 运行服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并查看覆盖率
pytest --cov=app --cov-report=html

# 运行特定测试文件
pytest tests/test_projects.py
```

## 项目结构

```
backend/
├── app/
│   ├── main.py           # FastAPI应用入口
│   ├── config.py         # 配置
│   ├── database.py       # 数据库连接
│   ├── models/           # 数据库模型
│   ├── schemas/          # Pydantic模型
│   ├── api/              # API路由
│   ├── services/         # 业务逻辑
│   └── utils/            # 工具函数
├── tests/                # 测试
├── data/                 # 数据存储
│   ├── uploads/          # 上传的文件
│   └── processed/        # 处理后的数据
└── pyproject.toml        # 项目配置
```
