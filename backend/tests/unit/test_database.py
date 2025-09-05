"""
Unit tests for Database models and operations
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.database import (
    Base, User, Project, API, MockServer,
    Task, OpenAPISpec, Test, AIAnalysis,
    get_db, init_db
)


class TestDatabaseModels:
    """Test database models"""

    def setup_method(self):
        """Setup test database"""
        # Create in-memory SQLite database for testing
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.session = self.SessionLocal()

    def teardown_method(self):
        """Cleanup after tests"""
        self.session.close()

    def test_user_model(self):
        """Test User model creation and attributes"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed123",
            is_active=True,
            subscription_tier="pro",
            api_calls_limit=1000
        )
        
        self.session.add(user)
        self.session.commit()
        
        retrieved_user = self.session.query(User).filter_by(email="test@example.com").first()
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
        assert retrieved_user.subscription_tier == "pro"
        assert retrieved_user.api_calls_limit == 1000
        assert retrieved_user.is_active is True

    def test_project_model(self):
        """Test Project model with user relationship"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed123"
        )
        self.session.add(user)
        self.session.commit()
        
        project = Project(
            name="Test Project",
            description="A test project",
            user_id=user.id,
            source_path="/test/path",
            framework="fastapi"
        )
        
        self.session.add(project)
        self.session.commit()
        
        retrieved_project = self.session.query(Project).filter_by(name="Test Project").first()
        assert retrieved_project is not None
        assert retrieved_project.user_id == user.id
        assert retrieved_project.framework == "fastapi"
        assert retrieved_project.status == "created"

    def test_api_model(self):
        """Test API model"""
        # Create project first
        project = Project(
            name="Test Project",
            source_path="/test"
        )
        self.session.add(project)
        self.session.commit()
        
        api = API(
            project_id=project.id,
            path="/api/users",
            method="GET",
            handler="get_users",
            parameters='[{"name": "limit", "type": "int"}]',
            response='{"type": "array"}',
            description="Get all users"
        )
        
        self.session.add(api)
        self.session.commit()
        
        retrieved = self.session.query(API).filter_by(path="/api/users").first()
        assert retrieved is not None
        assert retrieved.method == "GET"
        assert retrieved.handler == "get_users"

    def test_task_model(self):
        """Test Task model"""
        # Create user first
        user = User(email="test@example.com", username="test", hashed_password="hash")
        self.session.add(user)
        self.session.commit()
        
        task = Task(
            task_id="task-123",
            user_id=user.id,
            status="pending",
            result=None
        )
        
        self.session.add(task)
        self.session.commit()
        
        # Update status
        task.status = "completed"
        task.result = '{"success": true}'
        task.completed_at = datetime.utcnow()
        self.session.commit()
        
        retrieved = self.session.query(Task).filter_by(task_id="task-123").first()
        assert retrieved is not None
        assert retrieved.status == "completed"
        assert retrieved.result == '{"success": true}'
        assert retrieved.completed_at is not None

    def test_mock_server_model(self):
        """Test MockServer model"""
        project = Project(name="Test", source_path="/test")
        self.session.add(project)
        self.session.commit()
        
        mock_server = MockServer(
            project_id=project.id,
            name="Test Mock Server",
            port=3000,
            base_url="http://localhost:3000",
            spec_path="/specs/test.json",
            status="running"
        )
        
        self.session.add(mock_server)
        self.session.commit()
        
        retrieved = self.session.query(MockServer).filter_by(name="Test Mock Server").first()
        assert retrieved is not None
        assert retrieved.port == 3000
        assert retrieved.status == "running"

    def test_openapi_spec_model(self):
        """Test OpenAPISpec model"""
        project = Project(name="Test", source_path="/test")
        self.session.add(project)
        self.session.commit()
        
        spec = OpenAPISpec(
            project_id=project.id,
            version="3.0.0",
            spec='{"openapi": "3.0.0"}'
        )
        
        self.session.add(spec)
        self.session.commit()
        
        retrieved = self.session.query(OpenAPISpec).filter_by(project_id=project.id).first()
        assert retrieved is not None
        assert retrieved.version == "3.0.0"
        assert retrieved.spec == '{"openapi": "3.0.0"}'

    def test_test_model(self):
        """Test Test model"""
        project = Project(name="Test", source_path="/test")
        self.session.add(project)
        self.session.commit()
        
        test = Test(
            project_id=project.id,
            name="Test Suite",
            type="unit",
            framework="pytest",
            code="def test_example(): pass"
        )
        
        self.session.add(test)
        self.session.commit()
        
        retrieved = self.session.query(Test).filter_by(name="Test Suite").first()
        assert retrieved is not None
        assert retrieved.type == "unit"
        assert retrieved.framework == "pytest"

    def test_ai_analysis_model(self):
        """Test AIAnalysis model"""
        project = Project(name="Test", source_path="/test")
        self.session.add(project)
        self.session.commit()
        
        analysis = AIAnalysis(
            project_id=project.id,
            security_score=85,
            performance_score=90,
            compliance="GDPR compliant",
            vulnerabilities='{"issues": []}',
            recommendations='{"suggestions": []}'
        )
        
        self.session.add(analysis)
        self.session.commit()
        
        retrieved = self.session.query(AIAnalysis).filter_by(project_id=project.id).first()
        assert retrieved is not None
        assert retrieved.security_score == 85
        assert retrieved.performance_score == 90

    def test_user_relationships(self):
        """Test User model relationships"""
        user = User(email="test@example.com", username="test", hashed_password="hash")
        self.session.add(user)
        self.session.commit()
        
        # Add projects
        project1 = Project(name="Project 1", user_id=user.id, source_path="/p1")
        project2 = Project(name="Project 2", user_id=user.id, source_path="/p2")
        self.session.add_all([project1, project2])
        self.session.commit()
        
        # Check relationship
        user_with_projects = self.session.query(User).filter_by(id=user.id).first()
        assert len(user_with_projects.projects) == 2
        assert any(p.name == "Project 1" for p in user_with_projects.projects)
        assert any(p.name == "Project 2" for p in user_with_projects.projects)

    def test_project_cascade_delete(self):
        """Test cascade delete for project and its APIs"""
        project = Project(name="Test", source_path="/test")
        self.session.add(project)
        self.session.commit()
        
        # Add APIs
        api1 = API(project_id=project.id, path="/api/1", method="GET", handler="h1")
        api2 = API(project_id=project.id, path="/api/2", method="POST", handler="h2")
        self.session.add_all([api1, api2])
        self.session.commit()
        
        # Delete project
        self.session.delete(project)
        self.session.commit()
        
        # Check APIs are also deleted
        remaining_apis = self.session.query(API).all()
        assert len(remaining_apis) == 0


class TestDatabaseOperations:
    """Test database operations"""

    def setup_method(self):
        """Setup test database"""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def test_database_session_creation(self):
        """Test database session creation"""
        session = self.SessionLocal()
        
        assert isinstance(session, Session)
        assert session.is_active
        
        session.close()

    @patch('src.database.SessionLocal')
    def test_get_db_generator(self, mock_session):
        """Test get_db generator function"""
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        gen = get_db()
        db = next(gen)
        
        assert db == mock_db
        
        # Test cleanup
        try:
            next(gen)
        except StopIteration:
            pass
        
        mock_db.close.assert_called_once()

    @patch('src.database.engine')
    @patch('src.database.Base')
    def test_init_db(self, mock_base, mock_engine):
        """Test database initialization"""
        init_db()
        
        # Check that tables were created
        mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)


class TestDatabaseConstraints:
    """Test database constraints and validations"""

    def setup_method(self):
        """Setup test database"""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.session = self.SessionLocal()

    def teardown_method(self):
        """Cleanup after tests"""
        self.session.close()

    def test_unique_user_email(self):
        """Test unique constraint on user email"""
        user1 = User(email="test@example.com", username="user1", hashed_password="hash1")
        self.session.add(user1)
        self.session.commit()
        
        # Try to add another user with same email
        user2 = User(email="test@example.com", username="user2", hashed_password="hash2")
        self.session.add(user2)
        
        with pytest.raises(Exception):  # IntegrityError
            self.session.commit()

    def test_unique_username(self):
        """Test unique constraint on username"""
        user1 = User(email="test1@example.com", username="testuser", hashed_password="hash1")
        self.session.add(user1)
        self.session.commit()
        
        # Try to add another user with same username
        user2 = User(email="test2@example.com", username="testuser", hashed_password="hash2")
        self.session.add(user2)
        
        with pytest.raises(Exception):  # IntegrityError
            self.session.commit()

    def test_default_values(self):
        """Test default values for model fields"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hash"
        )
        self.session.add(user)
        self.session.commit()
        
        retrieved = self.session.query(User).filter_by(email="test@example.com").first()
        
        # Check defaults
        assert retrieved.is_active is True
        assert retrieved.subscription_tier == "free"
        assert retrieved.api_calls_limit == 100
        assert retrieved.api_calls_used == 0
        assert retrieved.created_at is not None

    def test_timestamp_auto_update(self):
        """Test automatic timestamp updates"""
        project = Project(name="Test", source_path="/test")
        self.session.add(project)
        self.session.commit()
        
        created_at = project.created_at
        
        # Update project
        project.description = "Updated description"
        self.session.commit()
        
        # created_at should not change
        assert project.created_at == created_at
        # updated_at should be set
        assert project.updated_at is not None
        assert project.updated_at >= created_at