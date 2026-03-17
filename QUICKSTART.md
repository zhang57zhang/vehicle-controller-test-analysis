# 快速开始指南

## 前置要求

- **Node.js**: >= 18.0.0
- **Python**: >= 3.10
- **Git**: 最新版本

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd vehicle-controller-test-analysis
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 安装后端依赖

```bash
cd ../backend
pip install -e ".[dev]"
```

### 4. 创建数据目录

```bash
cd backend
mkdir -p data/uploads data/processed data/reports data/temp
```

## 启动开发环境

### 启动后端服务

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 http://localhost:8000 启动

- API文档: http://localhost:8000/api/docs
- 健康检查: http://localhost:8000/api/health

### 启动前端服务

**新开一个终端：**

```bash
cd frontend
npm run dev
```

前端服务将在 http://localhost:3000 启动

## 运行测试

### 前端测试

```bash
cd frontend

# 运行测试
npm run test

# 测试并查看UI
npm run test:ui

# 测试覆盖率
npm run test:coverage
```

### 后端测试

```bash
cd backend

# 运行所有测试
pytest

# 运行测试并查看覆盖率
pytest --cov=app --cov-report=html

# 运行特定测试文件
pytest tests/test_main.py

# 显示详细输出
pytest -v
```

## 开发工作流

### 1. 创建新功能分支

```bash
git checkout -b feature/your-feature-name
```

### 2. 开发和测试

- 编写代码
- 编写测试
- 运行测试确保通过
- 提交代码

### 3. 提交代码

```bash
git add .
git commit -m "feat: your feature description"
```

### 4. 推送到远程仓库

```bash
git push origin feature/your-feature-name
```

## 项目结构

```
vehicle-controller-test-analysis/
├── frontend/              # 前端应用
│   ├── src/
│   │   ├── components/    # React组件
│   │   ├── pages/         # 页面组件
│   │   ├── services/      # API服务
│   │   ├── stores/        # 状态管理
│   │   ├── types/         # TypeScript类型
│   │   └── utils/         # 工具函数
│   ├── package.json
│   └── vite.config.ts
├── backend/               # 后端应用
│   ├── app/
│   │   ├── api/           # API路由
│   │   ├── models/        # 数据库模型
│   │   ├── schemas/       # Pydantic模型
│   │   ├── services/      # 业务逻辑
│   │   └── utils/         # 工具函数
│   ├── tests/             # 测试
│   ├── data/              # 数据目录
│   └── pyproject.toml
├── docs/                  # 文档
└── DEVELOPMENT_PLAN.md    # 开发计划
```

## 常见问题

### 1. 端口被占用

如果8000或3000端口被占用，可以修改端口：

**后端：**
```bash
uvicorn app.main:app --reload --port 8001
```

**前端：**
修改 `frontend/vite.config.ts` 中的 `server.port`

### 2. Python依赖安装失败

使用国内镜像：
```bash
pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. Node.js依赖安装失败

使用国内镜像：
```bash
npm install --registry=https://registry.npmmirror.com
```

## 下一步

1. 查看 [REQUIREMENTS_FINAL.md](REQUIREMENTS_FINAL.md) 了解详细需求
2. 查看 [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) 了解开发计划
3. 开始开发第一个功能

## 获取帮助

如果遇到问题：
1. 查看文档
2. 查看代码注释
3. 查看测试用例
4. 联系团队

---

**祝开发顺利！** 🚀
