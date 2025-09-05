"""
Unit tests for Project Manager module
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from src.project_manager import (
    ProjectManager,
    ProjectCreate,
    ProjectUpdate,
    ProjectStats
)


class TestProjectManager:
    """Test ProjectManager class"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def sample_project_data(self):
        """Sample project creation data"""
        return ProjectCreate(
            name="Test Project",
            description="Test Description",
            source_type="directory",
            source_path="/test/path"
        )
    
    def test_create_project_success(self, mock_db, sample_project_data):
        """Test successful project creation"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        user_id = 1
        
        # Execute
        result = ProjectManager.create_project(mock_db, user_id, sample_project_data)
        
        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_create_project_duplicate_name(self, mock_db, sample_project_data):
        """Test project creation with duplicate name"""
        # Setup - existing project found
        mock_existing = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing
        
        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            ProjectManager.create_project(mock_db, 1, sample_project_data)
        
        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)
    
    def test_get_project_success(self, mock_db):
        """Test getting existing project"""
        # Setup
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "Test Project"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # Execute
        result = ProjectManager.get_project(mock_db, user_id=1, project_id=1)
        
        # Assert
        assert result == mock_project
    
    def test_get_project_not_found(self, mock_db):
        """Test getting non-existent project"""
        # Setup - no project found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            ProjectManager.get_project(mock_db, user_id=1, project_id=999)
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)
    
    def test_list_projects_with_pagination(self, mock_db):
        """Test listing projects with pagination"""
        # Setup
        mock_projects = [
            MagicMock(to_dict=lambda: {"id": 1, "name": "Project 1"}),
            MagicMock(to_dict=lambda: {"id": 2, "name": "Project 2"})
        ]
        mock_query = mock_db.query.return_value.filter.return_value
        mock_query.count.return_value = 2
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_projects
        
        # Execute
        result = ProjectManager.list_projects(mock_db, user_id=1, page=1, per_page=10)
        
        # Assert
        assert result["total"] == 2
        assert len(result["projects"]) == 2
        assert result["page"] == 1
        assert result["per_page"] == 10
    
    def test_list_projects_with_search(self, mock_db):
        """Test listing projects with search filter"""
        # Setup
        mock_projects = []
        mock_query = mock_db.query.return_value.filter.return_value
        mock_query.filter.return_value = mock_query  # Chain for search filter
        mock_query.count.return_value = 0
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_projects
        
        # Execute
        result = ProjectManager.list_projects(mock_db, user_id=1, search="test")
        
        # Assert
        assert result["total"] == 0
        assert len(result["projects"]) == 0
    
    def test_update_project_success(self, mock_db):
        """Test successful project update"""
        # Setup
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "Old Name"
        
        # Mock get_project to return the project
        with patch.object(ProjectManager, 'get_project', return_value=mock_project):
            # No name conflict
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            update_data = ProjectUpdate(
                name="New Name",
                description="New Description"
            )
            
            # Execute
            result = ProjectManager.update_project(mock_db, 1, 1, update_data)
            
            # Assert
            assert mock_project.name == "New Name"
            assert mock_project.description == "New Description"
            mock_db.commit.assert_called_once()
    
    def test_update_project_name_conflict(self, mock_db):
        """Test project update with name conflict"""
        # Setup
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "Old Name"
        
        mock_existing = MagicMock()
        mock_existing.id = 2
        
        with patch.object(ProjectManager, 'get_project', return_value=mock_project):
            # Name conflict found
            mock_db.query.return_value.filter.return_value.first.return_value = mock_existing
            
            update_data = ProjectUpdate(name="Existing Name")
            
            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                ProjectManager.update_project(mock_db, 1, 1, update_data)
            
            assert exc_info.value.status_code == 400
            assert "already exists" in str(exc_info.value.detail)
    
    def test_delete_project_success(self, mock_db):
        """Test successful project deletion"""
        # Setup
        mock_project = MagicMock()
        mock_project.id = 1
        
        with patch.object(ProjectManager, 'get_project', return_value=mock_project):
            # Execute
            result = ProjectManager.delete_project(mock_db, 1, 1)
            
            # Assert
            assert result == True
            mock_db.delete.assert_called_once_with(mock_project)
            mock_db.commit.assert_called_once()
    
    def test_get_project_stats(self, mock_db):
        """Test getting project statistics"""
        # Setup
        mock_api1 = MagicMock()
        mock_api1.tests = [MagicMock(), MagicMock()]
        mock_api1.security_score = 85.0
        mock_api1.security_issues = ["issue1", "issue2"]
        
        mock_api2 = MagicMock()
        mock_api2.tests = [MagicMock()]
        mock_api2.security_score = 90.0
        mock_api2.security_issues = ["issue3"]
        
        mock_task1 = MagicMock()
        mock_task1.hours_saved = 10.5
        mock_task1.money_saved = 1500.0
        
        mock_task2 = MagicMock()
        mock_task2.hours_saved = 5.5
        mock_task2.money_saved = 750.0
        
        mock_project = MagicMock()
        mock_project.apis = [mock_api1, mock_api2]
        mock_project.tasks = [mock_task1, mock_task2]
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]
        
        # Execute
        result = ProjectManager.get_project_stats(mock_db, user_id=1)
        
        # Assert
        assert result.total_projects == 1
        assert result.total_apis == 2
        assert result.total_tests == 3
        assert result.total_tasks == 2
        assert result.security_issues_found == 3
        assert result.average_security_score == 87.5
        assert result.hours_saved == 16.0
        assert result.money_saved == 2250.0
    
    def test_clone_project_success(self, mock_db):
        """Test successful project cloning"""
        # Setup source project
        mock_api = MagicMock()
        mock_api.path = "/test"
        mock_api.method = "GET"
        mock_api.handler_name = "test_handler"
        mock_api.description = "Test API"
        mock_api.parameters = {}
        mock_api.response_schema = {}
        mock_api.auth_required = False
        mock_api.rate_limit = None
        mock_api.security_score = 85
        mock_api.security_issues = []
        mock_api.optimization_suggestions = []
        mock_api.test_coverage = 0.8
        
        mock_source = MagicMock()
        mock_source.id = 1
        mock_source.name = "Original Project"
        mock_source.source_type = "directory"
        mock_source.source_path = "/test/path"
        mock_source.github_url = None
        mock_source.apis = [mock_api]
        
        # Mock OpenAPISpec query
        mock_spec = MagicMock()
        mock_spec.version = "3.0.0"
        mock_spec.spec_data = {"openapi": "3.0.0"}
        
        with patch.object(ProjectManager, 'get_project', return_value=mock_source):
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_spec]
            
            # Execute
            result = ProjectManager.clone_project(mock_db, 1, 1, "Cloned Project")
            
            # Assert
            mock_db.add.assert_called()  # Should add new project and APIs
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
    
    def test_start_orchestration(self, mock_db):
        """Test starting orchestration task"""
        # Setup
        mock_project = MagicMock()
        mock_project.id = 1
        
        with patch.object(ProjectManager, 'get_project', return_value=mock_project):
            with patch('src.project_manager.uuid.uuid4', return_value='test-uuid'):
                # Execute
                result = ProjectManager.start_orchestration(mock_db, 1, 1)
                
                # Assert
                assert result.id == 'test-uuid'
                assert result.project_id == 1
                assert result.status == "pending"
                assert result.stage == "initialization"
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()


class TestProjectModels:
    """Test Pydantic models for projects"""
    
    def test_project_create_validation(self):
        """Test ProjectCreate model validation"""
        # Valid data
        project = ProjectCreate(
            name="Valid Project",
            description="Valid description",
            source_type="directory",
            source_path="/valid/path"
        )
        assert project.name == "Valid Project"
        
        # Invalid source_type
        with pytest.raises(ValueError):
            ProjectCreate(
                name="Test",
                source_type="invalid_type"
            )
    
    def test_project_update_optional_fields(self):
        """Test ProjectUpdate with optional fields"""
        # All fields optional
        update = ProjectUpdate()
        assert update.name is None
        assert update.description is None
        
        # Some fields set
        update = ProjectUpdate(name="New Name")
        assert update.name == "New Name"
        assert update.description is None
    
    def test_project_stats_model(self):
        """Test ProjectStats model"""
        stats = ProjectStats(
            total_projects=5,
            total_apis=100,
            total_tests=500,
            total_tasks=50,
            security_issues_found=10,
            average_security_score=85.5,
            hours_saved=120.5,
            money_saved=15000.0
        )
        
        assert stats.total_projects == 5
        assert stats.average_security_score == 85.5
        assert stats.money_saved == 15000.0