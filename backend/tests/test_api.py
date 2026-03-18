"""
单元测试：API端点

测试API端点的功能，包括项目管理、文件上传和DBC解析。
"""
import pytest
import os
import tempfile
from pathlib import Path
from io import BytesIO
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import Project, TestDataFile, DBCFile


# ==================== 测试数据库设置 ====================

# 使用内存SQLite数据库进行测试
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖，使用测试数据库"""
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
def db():
    """数据库会话fixture"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_project(db):
    """创建测试项目"""
    project = Project(
        name="Test Project",
        description="This is a test project"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def temp_upload_dir(tmp_path):
    """临时上传目录"""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return str(upload_dir)


# ==================== 测试项目管理API ====================

class TestProjectAPI:
    """项目管理API测试"""

    def test_create_project(self):
        """测试创建项目"""
        response = client.post(
            "/api/projects",
            json={
                "name": "New Project",
                "description": "A new test project"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Project"
        assert data["description"] == "A new test project"
        assert "id" in data

    def test_create_project_duplicate_name(self):
        """测试创建重复名称的项目"""
        # 创建第一个项目
        client.post(
            "/api/projects",
            json={"name": "Duplicate Project"}
        )

        # 尝试创建同名项目
        response = client.post(
            "/api/projects",
            json={"name": "Duplicate Project"}
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_create_project_invalid_data(self):
        """测试创建项目时提供无效数据"""
        response = client.post(
            "/api/projects",
            json={
                "name": "A" * 250  # 超过最大长度200
            }
        )
        assert response.status_code == 422  # 验证错误

    def test_get_projects(self, test_project):
        """测试获取项目列表"""
        response = client.get("/api/projects")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_projects_with_filter(self, test_project):
        """测试获取项目列表（带过滤）"""
        response = client.get("/api/projects?name=Test")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 所有结果应包含"Test"

    def test_get_projects_pagination(self):
        """测试项目列表分页"""
        # 创建多个项目
        for i in range(5):
            client.post(
                "/api/projects",
                json={"name": f"Project {i}"}
            )

        response = client.get("/api/projects?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_get_project_by_id(self, test_project):
        """测试获取单个项目"""
        response = client.get(f"/api/projects/{test_project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project.id
        assert data["name"] == test_project.name

    def test_get_project_not_found(self):
        """测试获取不存在的项目"""
        response = client.get("/api/projects/99999")
        assert response.status_code == 404

    def test_update_project(self, test_project):
        """测试更新项目"""
        response = client.put(
            f"/api/projects/{test_project.id}",
            json={
                "name": "Updated Project",
                "description": "Updated description"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Project"
        assert data["description"] == "Updated description"

    def test_update_project_not_found(self):
        """测试更新不存在的项目"""
        response = client.put(
            "/api/projects/99999",
            json={"name": "Updated"}
        )
        assert response.status_code == 404

    def test_update_project_duplicate_name(self, db):
        """测试更新项目时使用重复名称"""
        # 创建两个项目
        project1 = Project(name="Project 1")
        project2 = Project(name="Project 2")
        db.add_all([project1, project2])
        db.commit()

        # 尝试将project1改名为project2的名称
        response = client.put(
            f"/api/projects/{project1.id}",
            json={"name": "Project 2"}
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_delete_project(self, db):
        """测试删除项目"""
        project = Project(name="To Delete")
        db.add(project)
        db.commit()

        response = client.delete(f"/api/projects/{project.id}")
        assert response.status_code == 204

        # 验证项目已删除
        get_response = client.get(f"/api/projects/{project.id}")
        assert get_response.status_code == 404

    def test_delete_project_not_found(self):
        """测试删除不存在的项目"""
        response = client.delete("/api/projects/99999")
        assert response.status_code == 404

    def test_delete_project_with_dependencies(self, db, test_project):
        """测试删除有关联数据的项目"""
        # 添加测试数据文件
        test_data = TestDataFile(
            project_id=test_project.id,
            file_name="test.mat",
            file_path="/fake/path/test.mat",
            file_size=1000,
            format="mat",
            data_type="MANUAL"
        )
        db.add(test_data)
        db.commit()

        # 尝试删除项目
        response = client.delete(f"/api/projects/{test_project.id}")
        assert response.status_code == 409
        assert "cannot delete" in response.json()["detail"].lower()


# ==================== 测试文件上传API ====================

class TestFileUploadAPI:
    """文件上传API测试"""

    def test_upload_test_data_file(self, test_project, temp_upload_dir):
        """测试上传测试数据文件"""
        # 创建测试文件
        file_content = b"test data content"
        files = {
            "file": ("test.csv", BytesIO(file_content), "text/csv")
        }
        data = {
            "data_type": "MANUAL"
        }

        response = client.post(
            f"/api/projects/{test_project.id}/test-data/upload",
            files=files,
            data=data
        )

        assert response.status_code == 201
        result = response.json()
        assert result["file_name"] == "test.csv"
        assert result["project_id"] == test_project.id
        assert result["format"] == "csv"
        assert result["data_type"] == "MANUAL"

    def test_upload_test_data_project_not_found(self):
        """测试上传到不存在的项目"""
        files = {
            "file": ("test.csv", BytesIO(b"content"), "text/csv")
        }

        response = client.post(
            "/api/projects/99999/test-data/upload",
            files=files
        )
        assert response.status_code == 404

    def test_upload_test_data_invalid_format(self, test_project):
        """测试上传不支持的文件格式"""
        files = {
            "file": ("test.xyz", BytesIO(b"content"), "application/octet-stream")
        }

        response = client.post(
            f"/api/projects/{test_project.id}/test-data/upload",
            files=files
        )
        assert response.status_code == 400

    def test_upload_test_data_invalid_data_type(self, test_project):
        """测试上传时使用无效数据类型"""
        files = {
            "file": ("test.csv", BytesIO(b"content"), "text/csv")
        }
        data = {
            "data_type": "INVALID_TYPE"
        }

        response = client.post(
            f"/api/projects/{test_project.id}/test-data/upload",
            files=files,
            data=data
        )
        assert response.status_code == 400

    def test_upload_test_data_file_too_large(self, test_project, monkeypatch):
        """测试上传超过大小限制的文件"""
        # 模拟最大文件大小限制为1字节
        from app import config
        monkeypatch.setattr(config.settings, 'MAX_UPLOAD_SIZE', 1)

        files = {
            "file": ("large.csv", BytesIO(b"x" * 100), "text/csv")
        }

        response = client.post(
            f"/api/projects/{test_project.id}/test-data/upload",
            files=files
        )
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"].lower()

    def test_get_test_data_list(self, db, test_project):
        """测试获取测试数据列表"""
        # 创建测试数据文件
        test_data = TestDataFile(
            project_id=test_project.id,
            file_name="test.mat",
            file_path="/fake/path/test.mat",
            file_size=1000,
            format="mat",
            data_type="MANUAL"
        )
        db.add(test_data)
        db.commit()

        response = client.get(f"/api/projects/{test_project.id}/test-data")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_test_data_list_with_filter(self, db, test_project):
        """测试获取测试数据列表（带数据类型过滤）"""
        # 创建两个不同类型的测试数据
        test_data1 = TestDataFile(
            project_id=test_project.id,
            file_name="test1.mat",
            file_path="/fake/path/test1.mat",
            file_size=1000,
            format="mat",
            data_type="MIL"
        )
        test_data2 = TestDataFile(
            project_id=test_project.id,
            file_name="test2.mat",
            file_path="/fake/path/test2.mat",
            file_size=1000,
            format="mat",
            data_type="HIL"
        )
        db.add_all([test_data1, test_data2])
        db.commit()

        response = client.get(f"/api/projects/{test_project.id}/test-data?data_type=MIL")
        assert response.status_code == 200
        data = response.json()
        assert all(item["data_type"] == "MIL" for item in data)

    def test_get_test_data_by_id(self, db):
        """测试获取单个测试数据"""
        test_data = TestDataFile(
            project_id=1,
            file_name="test.mat",
            file_path="/fake/path/test.mat",
            file_size=1000,
            format="mat",
            data_type="MANUAL"
        )
        db.add(test_data)
        db.commit()

        response = client.get(f"/api/test-data/{test_data.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_data.id

    def test_get_test_data_not_found(self):
        """测试获取不存在的测试数据"""
        response = client.get("/api/test-data/99999")
        assert response.status_code == 404

    def test_delete_test_data(self, db):
        """测试删除测试数据"""
        test_data = TestDataFile(
            project_id=1,
            file_name="test.mat",
            file_path="/fake/path/test.mat",
            file_size=1000,
            format="mat",
            data_type="MANUAL"
        )
        db.add(test_data)
        db.commit()

        response = client.delete(f"/api/test-data/{test_data.id}")
        assert response.status_code == 204

    def test_delete_test_data_not_found(self):
        """测试删除不存在的测试数据"""
        response = client.delete("/api/test-data/99999")
        assert response.status_code == 404


# ==================== 测试DBC上传和解析API ====================

class TestDBCAPI:
    """DBC文件API测试"""

    @pytest.fixture
    def sample_dbc_content(self):
        """示例DBC文件内容"""
        return """VERSION ""

NS_ :
    NS_DESC_
    CM_

BS_:

BU_:

BO_ 100 MSG1: 8 Vector__XXX
 SG_ Signal1 : 0|8@1+ (0.1,0) "V" [0|25.5] "Voltage"
 SG_ Signal2 : 8|8@1+ (1,0) "A" [0|255] "Current"
"""

    def test_upload_dbc_file(self, test_project, sample_dbc_content):
        """测试上传DBC文件"""
        files = {
            "file": ("test.dbc", BytesIO(sample_dbc_content.encode()), "text/plain")
        }

        response = client.post(
            f"/api/projects/{test_project.id}/dbc/upload",
            files=files
        )

        assert response.status_code == 201
        result = response.json()
        assert result["file_name"] == "test.dbc"
        assert result["project_id"] == test_project.id

    def test_upload_dbc_invalid_format(self, test_project):
        """测试上传无效格式的DBC文件"""
        files = {
            "file": ("test.txt", BytesIO(b"not a dbc file"), "text/plain")
        }

        response = client.post(
            f"/api/projects/{test_project.id}/dbc/upload",
            files=files
        )
        assert response.status_code == 400

    def test_upload_dbc_project_not_found(self, sample_dbc_content):
        """测试上传到不存在的项目"""
        files = {
            "file": ("test.dbc", BytesIO(sample_dbc_content.encode()), "text/plain")
        }

        response = client.post(
            "/api/projects/99999/dbc/upload",
            files=files
        )
        assert response.status_code == 404

    def test_get_dbc_list(self, db, test_project):
        """测试获取DBC文件列表"""
        dbc_file = DBCFile(
            project_id=test_project.id,
            file_name="test.dbc",
            file_path="/fake/path/test.dbc"
        )
        db.add(dbc_file)
        db.commit()

        response = client.get(f"/api/projects/{test_project.id}/dbc")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_dbc_by_id(self, db):
        """测试获取单个DBC文件"""
        dbc_file = DBCFile(
            project_id=1,
            file_name="test.dbc",
            file_path="/fake/path/test.dbc"
        )
        db.add(dbc_file)
        db.commit()

        response = client.get(f"/api/dbc/{dbc_file.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == dbc_file.id

    def test_parse_dbc(self, test_project, sample_dbc_content, tmp_path):
        """测试解析DBC文件"""
        # 首先上传DBC文件
        dbc_path = tmp_path / "test.dbc"
        dbc_path.write_text(sample_dbc_content)

        # 创建DBC记录
        dbc_file = DBCFile(
            project_id=test_project.id,
            file_name="test.dbc",
            file_path=str(dbc_path)
        )
        db = TestingSessionLocal()
        db.add(dbc_file)
        db.commit()
        db.refresh(dbc_file)
        db.close()

        # 解析DBC
        response = client.post(
            f"/api/dbc/{dbc_file.id}/parse",
            json={"parse_type": "summary"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message_count" in data
        assert "signal_count" in data

    def test_get_dbc_messages(self, test_project, sample_dbc_content, tmp_path):
        """测试获取DBC消息列表"""
        # 创建并上传DBC文件
        dbc_path = tmp_path / "test.dbc"
        dbc_path.write_text(sample_dbc_content)

        dbc_file = DBCFile(
            project_id=test_project.id,
            file_name="test.dbc",
            file_path=str(dbc_path)
        )
        db = TestingSessionLocal()
        db.add(dbc_file)
        db.commit()
        db.refresh(dbc_file)
        db.close()

        response = client.get(f"/api/dbc/{dbc_file.id}/messages")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)

    def test_get_dbc_signals(self, test_project, sample_dbc_content, tmp_path):
        """测试获取DBC信号列表"""
        # 创建并上传DBC文件
        dbc_path = tmp_path / "test.dbc"
        dbc_path.write_text(sample_dbc_content)

        dbc_file = DBCFile(
            project_id=test_project.id,
            file_name="test.dbc",
            file_path=str(dbc_path)
        )
        db = TestingSessionLocal()
        db.add(dbc_file)
        db.commit()
        db.refresh(dbc_file)
        db.close()

        response = client.get(f"/api/dbc/{dbc_file.id}/signals")
        assert response.status_code == 200
        data = response.json()
        assert "signals" in data
        assert isinstance(data["signals"], list)

    def test_delete_dbc(self, db):
        """测试删除DBC文件"""
        dbc_file = DBCFile(
            project_id=1,
            file_name="test.dbc",
            file_path="/fake/path/test.dbc"
        )
        db.add(dbc_file)
        db.commit()

        response = client.delete(f"/api/dbc/{dbc_file.id}")
        assert response.status_code == 204

    def test_delete_dbc_not_found(self):
        """测试删除不存在的DBC文件"""
        response = client.delete("/api/dbc/99999")
        assert response.status_code == 404


# ==================== 测试健康检查 ====================

class TestHealthCheck:
    """健康检查测试"""

    def test_root_endpoint(self):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data

    def test_health_check(self):
        """测试健康检查端点"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
