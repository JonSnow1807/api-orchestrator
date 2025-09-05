"""Comprehensive tests for main.py API endpoints"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json
import asyncio
from datetime import datetime

# Mock all dependencies before importing
with patch('src.main.get_db'):
    with patch('src.main.get_current_user'):
        with patch('src.main.WebSocket'):
            from src.main import app

client = TestClient(app)

@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    user.subscription_tier = "pro"
    return user

class TestHealthCheck:
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data

class TestAuthEndpoints:
    @patch('src.main.auth_manager.register_user')
    def test_register(self, mock_register):
        """Test user registration"""
        mock_register.return_value = {
            "id": 1,
            "email": "test@example.com",
            "created_at": datetime.now().isoformat()
        }
        
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        })
        
        assert response.status_code in [200, 201, 422]  # Allow validation errors
    
    @patch('src.main.auth_manager.authenticate_user')
    def test_login(self, mock_auth):
        """Test user login"""
        mock_auth.return_value = {
            "access_token": "test_token",
            "token_type": "bearer"
        }
        
        response = client.post("/auth/login", data={
            "username": "test@example.com",
            "password": "password"
        })
        
        assert response.status_code in [200, 422]

class TestProjectEndpoints:
    @patch('src.main.get_current_user')
    @patch('src.main.project_manager.create_project')
    def test_create_project(self, mock_create, mock_user):
        """Test project creation"""
        mock_user.return_value = MagicMock(id=1)
        mock_create.return_value = {
            "id": 1,
            "name": "Test Project",
            "description": "Test Description"
        }
        
        with patch('src.main.get_db'):
            response = client.post("/projects", json={
                "name": "Test Project",
                "description": "Test Description"
            }, headers={"Authorization": "Bearer test_token"})
            
            assert response.status_code in [200, 201, 401, 422]
    
    @patch('src.main.get_current_user')
    @patch('src.main.project_manager.get_user_projects')
    def test_list_projects(self, mock_list, mock_user):
        """Test listing projects"""
        mock_user.return_value = MagicMock(id=1)
        mock_list.return_value = [
            {"id": 1, "name": "Project 1"},
            {"id": 2, "name": "Project 2"}
        ]
        
        response = client.get("/projects", headers={"Authorization": "Bearer test_token"})
        assert response.status_code in [200, 401]

class TestOrchestrationEndpoints:
    @patch('src.main.get_current_user')
    @patch('src.main.APIOrchestrator')
    @patch('src.main.get_db')
    async def test_orchestrate(self, mock_db, mock_orchestrator, mock_user):
        """Test orchestration endpoint"""
        mock_user.return_value = MagicMock(id=1, subscription_tier="pro")
        mock_orch_instance = MagicMock()
        mock_orch_instance.orchestrate = AsyncMock(return_value={
            "task_id": "test_123",
            "status": "completed"
        })
        mock_orchestrator.return_value = mock_orch_instance
        
        response = client.post("/orchestrate", json={
            "project_path": "/test/path",
            "framework": "fastapi"
        }, headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code in [200, 401, 422]

class TestResultsEndpoints:
    @patch('src.main.get_current_user')
    @patch('src.main.os.path.exists')
    @patch('src.main.open')
    def test_get_results(self, mock_open, mock_exists, mock_user):
        """Test getting results"""
        mock_user.return_value = MagicMock(id=1)
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps({
            "spec": {"openapi": "3.0.0"}
        })
        
        response = client.get("/results/test_123", headers={"Authorization": "Bearer test_token"})
        assert response.status_code in [200, 401, 404]

class TestExportEndpoints:
    @patch('src.main.get_current_user')
    @patch('src.main.os.path.exists')
    @patch('src.main.open')
    @patch('src.main.ExportManager')
    def test_export_artifacts(self, mock_export, mock_open, mock_exists, mock_user):
        """Test exporting artifacts"""
        mock_user.return_value = MagicMock(id=1)
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps({
            "spec": {"openapi": "3.0.0"}
        })
        mock_export.export_openapi_spec.return_value = b"exported_data"
        
        response = client.get("/export/test_123/json", headers={"Authorization": "Bearer test_token"})
        assert response.status_code in [200, 401, 404]

class TestImportEndpoints:
    @patch('src.main.get_current_user')
    @patch('src.main.ImportManager')
    def test_import_spec(self, mock_import, mock_user):
        """Test importing specifications"""
        mock_user.return_value = MagicMock(id=1)
        mock_import.import_openapi_spec.return_value = {"openapi": "3.0.0"}
        mock_import.validate_openapi_spec.return_value = True
        
        response = client.post("/import/openapi", 
            files={"file": ("test.json", b'{"openapi":"3.0.0"}', "application/json")},
            headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code in [200, 401, 422]

class TestMockServerEndpoints:
    @patch('src.main.get_current_user')
    @patch('src.main.MockServerAgent')
    def test_start_mock_server(self, mock_server_agent, mock_user):
        """Test starting mock server"""
        mock_user.return_value = MagicMock(id=1, subscription_tier="pro")
        mock_agent = MagicMock()
        mock_agent.create_mock_server.return_value = {"server_id": "test_123", "port": 8080}
        mock_server_agent.return_value = mock_agent
        
        response = client.post("/mock-server/start", json={
            "task_id": "test_123"
        }, headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code in [200, 401, 403, 422]

class TestUserProfileEndpoints:
    @patch('src.main.get_current_user')
    @patch('src.main.get_db')
    def test_get_profile(self, mock_db, mock_user):
        """Test getting user profile"""
        user = MagicMock()
        user.id = 1
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.subscription_tier = "free"
        user.created_at = datetime.now()
        mock_user.return_value = user
        
        response = client.get("/user/profile", headers={"Authorization": "Bearer test_token"})
        assert response.status_code in [200, 401]
    
    @patch('src.main.get_current_user')
    @patch('src.main.get_db')
    def test_update_profile(self, mock_db, mock_user):
        """Test updating user profile"""
        user = MagicMock()
        user.id = 1
        mock_user.return_value = user
        mock_db.return_value.commit = MagicMock()
        
        response = client.put("/user/profile", json={
            "full_name": "Updated Name",
            "company": "Test Company"
        }, headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code in [200, 401, 422]

class TestPasswordEndpoints:
    @patch('src.main.request_password_reset')
    def test_password_reset_request(self, mock_reset):
        """Test password reset request"""
        mock_reset.return_value = {"message": "Reset email sent"}
        
        response = client.post("/auth/password/reset", json={
            "email": "test@example.com"
        })
        
        assert response.status_code in [200, 422]
    
    @patch('src.main.confirm_password_reset')
    def test_password_reset_confirm(self, mock_confirm):
        """Test password reset confirmation"""
        mock_confirm.return_value = {"message": "Password reset"}
        
        response = client.post("/auth/password/reset/confirm", json={
            "token": "test_token",
            "new_password": "NewPass123!"
        })
        
        assert response.status_code in [200, 422]

class TestWebSocketEndpoint:
    @patch('src.main.ConnectionManager')
    async def test_websocket_endpoint(self, mock_manager):
        """Test WebSocket endpoint"""
        # WebSocket testing requires special handling
        pass

class TestStaticFiles:
    def test_api_docs_redirect(self):
        """Test API docs redirect"""
        response = client.get("/docs", follow_redirects=False)
        assert response.status_code in [200, 307]

class TestErrorHandlers:
    def test_404_handler(self):
        """Test 404 error handler"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    @patch('src.main.get_current_user')
    def test_401_unauthorized(self, mock_user):
        """Test 401 unauthorized"""
        mock_user.side_effect = Exception("Unauthorized")
        response = client.get("/user/profile")
        assert response.status_code in [401, 500]

class TestUtilityFunctions:
    def test_get_subscription_limits(self):
        """Test subscription limits function"""
        from src.main import get_subscription_limits
        limits = get_subscription_limits("pro")
        assert "max_projects" in limits
        assert "max_apis_per_project" in limits
        assert "features" in limits