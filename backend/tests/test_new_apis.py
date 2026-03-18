"""
新创建API的测试

测试文件上传、数据导入等新API功能。
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os
from pathlib import Path

from app.main import app
from app.database import get_db, Base


# 创建测试数据库
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库会话依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# 覆盖数据库依赖
app.dependency_overrides[get_db] = override_get_db

# 创建测试客户端
client = TestClient(app)


@pytest.fixture(scope="function")
def db_setup():
    """设置测试数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    yield
    # 清理
    Base.metadata.drop_all(bind=engine)
    # 删除测试数据库文件
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture
def sample_project(db_setup):
    """创建示例项目"""
    from app.schemas import ProjectCreate
    response = client.post(
        "/api/projects",
        json={"name": "Test Project", "description": "Test description"}
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def sample_csv_file():
    """创建示例CSV文件"""
    import pandas as pd
    df = pd.DataFrame({
        'timestamp': [1.0, 2.0, 3.0],
        'signal1': [10, 20, 30],
        'signal2': [100, 200, 300]
    })

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        yield f.name

    os.unlink(f.name)


@pytest.fixture
def sample_excel_file():
    """创建示例Excel文件"""
    import pandas as pd
    df = pd.DataFrame({
        'timestamp': [1.0, 2.0, 3.0],
        'signal1': [10, 20, 30],
        'signal2': [100, 200, 300]
    })

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        df.to_excel(f.name, index=False)
        yield f.name

    os.unlink(f.name)


# ==================== 文件上传API测试 ====================

class TestFileUploadAPI:
    """文件上传API测试"""

    def test_upload_csv_file(self, sample_csv_file):
        """测试上传CSV文件"""
        with open(sample_csv_file, 'rb') as f:
            response = client.post(
                "/api/files/upload",
                files={"file": ("test.csv", f, "text/csv")}
            )

        assert response.status_code == 201
        data = response.json()
        assert "file_id" in data
        assert data["file_type"] == "csv"
        assert data["file_name"] == "test.csv"
        assert data["file_size"] > 0

    def test_upload_excel_file(self, sample_excel_file):
        """测试上传Excel文件"""
        with open(sample_excel_file, 'rb') as f:
            response = client.post(
                "/api/files/upload",
                files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )

        assert response.status_code == 201
        data = response.json()
        assert "file_id" in data
        assert data["file_type"] == "excel"

    def test_upload_unsupported_file_type(self):
        """测试上传不支持的文件类型"""
        # 创建一个临时文件，扩展名为.txt（不支持）
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as f:
            f.write("test content")
            temp_file = f.name

        try:
            with open(temp_file, 'rb') as f:
                response = client.post(
                    "/api/files/upload",
                    files={"file": ("test.txt", f, "text/plain")}
                )

            assert response.status_code == 400
            assert "Unsupported file type" in response.json()["detail"]
        finally:
            os.unlink(temp_file)

    def test_upload_large_file(self):
        """测试上传过大文件（超过500MB）"""
        # 创建一个大文件（模拟）
        large_content = b"0" * (500 * 1024 * 1024 + 1)  # 500MB + 1 byte

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            f.write(large_content)
            temp_file = f.name

        try:
            with open(temp_file, 'rb') as f:
                response = client.post(
                    "/api/files/upload",
                    files={"file": ("large.csv", f, "text/csv")}
                )

            assert response.status_code == 413
            assert "exceeds maximum allowed size" in response.json()["detail"]
        finally:
            os.unlink(temp_file)


# ==================== 数据导入API测试 ====================

class TestDataImportAPI:
    """数据导入API测试"""

    def test_import_csv_to_project(self, db_setup, sample_project, sample_csv_file):
        """测试导入CSV到项目"""
        # 先上传文件
        with open(sample_csv_file, 'rb') as f:
            upload_response = client.post(
                "/api/files/upload",
                files={"file": ("test.csv", f, "text/csv")}
            )

        assert upload_response.status_code == 201
        upload_data = upload_response.json()

        # 导入数据到项目
        import_response = client.post(
            "/api/data/import",
            json={
                "project_id": sample_project["id"],
                "file_id": upload_data["file_id"],
                "file_type": "csv",
                "file_path": upload_data["file_path"],
                "data_type": "MANUAL"
            }
        )

        assert import_response.status_code == 201
        data = import_response.json()
        assert data["success"] is True
        assert "test_data_id" in data
        assert data["import_stats"]["file_type"] == "csv"
        assert data["import_stats"]["total_records"] > 0

    def test_parse_file_only(self, db_setup, sample_csv_file):
        """测试仅解析文件"""
        response = client.post(
            "/api/data/parse",
            json={
                "file_path": sample_csv_file,
                "file_type": "csv"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "parsed_data" in data
        assert data["parsed_data"]["file_type"] == "csv"

    def test_import_nonexistent_project(self, db_setup, sample_csv_file):
        """测试导入到不存在的项目"""
        # 先上传文件
        with open(sample_csv_file, 'rb') as f:
            upload_response = client.post(
                "/api/files/upload",
                files={"file": ("test.csv", f, "text/csv")}
            )

        assert upload_response.status_code == 201
        upload_data = upload_response.json()

        # 尝试导入到不存在的项目
        import_response = client.post(
            "/api/data/import",
            json={
                "project_id": 99999,
                "file_id": upload_data["file_id"],
                "file_type": "csv",
                "file_path": upload_data["file_path"],
                "data_type": "MANUAL"
            }
        )

        assert import_response.status_code == 404
        assert "not found" in import_response.json()["detail"]


# ==================== 项目管理API测试 ====================

class TestProjectAPI:
    """项目管理API测试"""

    def test_create_project(self, db_setup):
        """测试创建项目"""
        response = client.post(
            "/api/projects",
            json={
                "name": "Test Project",
                "description": "Test description"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] > 0
        assert data["name"] == "Test Project"
        assert data["description"] == "Test description"

    def test_get_projects(self, db_setup):
        """测试获取项目列表"""
        # 创建两个项目
        client.post(
            "/api/projects",
            json={"name": "Project 1", "description": "Description 1"}
        )
        client.post(
            "/api/projects",
            json={"name": "Project 2", "description": "Description 2"}
        )

        response = client.get("/api/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_project_detail(self, db_setup):
        """测试获取项目详情"""
        create_response = client.post(
            "/api/projects",
            json={"name": "Test Project", "description": "Test description"}
        )
        project_id = create_response.json()["id"]

        response = client.get(f"/api/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Test Project"

    def test_update_project(self, db_setup):
        """测试更新项目"""
        create_response = client.post(
            "/api/projects",
            json={"name": "Test Project", "description": "Test description"}
        )
        project_id = create_response.json()["id"]

        response = client.put(
            f"/api/projects/{project_id}",
            json={"description": "Updated description"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    def test_delete_project(self, db_setup):
        """测试删除项目"""
        create_response = client.post(
            "/api/projects",
            json={"name": "Test Project", "description": "Test description"}
        )
        project_id = create_response.json()["id"]

        response = client.delete(f"/api/projects/{project_id}")
        assert response.status_code == 204

        # 验证项目已删除
        get_response = client.get(f"/api/projects/{project_id}")
        assert get_response.status_code == 404
