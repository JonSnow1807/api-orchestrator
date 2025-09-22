"""
Project Management Module for API Orchestrator
Handles CRUD operations for projects
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
import uuid

from src.database import Project, API, Task, OpenAPISpec


# Pydantic models for request/response
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    source_type: str = Field("directory", pattern="^(directory|github|upload)$")
    source_path: Optional[str] = None
    github_url: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    source_path: Optional[str] = None
    github_url: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    source_type: str
    source_path: Optional[str]
    github_url: Optional[str]
    created_at: str
    updated_at: str
    api_count: int
    task_count: int


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    page: int
    per_page: int


class ProjectStats(BaseModel):
    total_projects: int
    total_apis: int
    total_tests: int
    total_tasks: int
    security_issues_found: int
    average_security_score: float
    hours_saved: float
    money_saved: float


class ProjectManager:
    """Manages project CRUD operations"""

    @staticmethod
    def create_project(
        db: Session, user_id: int, project_data: ProjectCreate
    ) -> Project:
        """Create a new project for a user"""

        # Check if project name already exists for this user
        existing = (
            db.query(Project)
            .filter(and_(Project.name == project_data.name, Project.user_id == user_id))
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project '{project_data.name}' already exists",
            )

        # Create new project
        project = Project(
            name=project_data.name,
            description=project_data.description,
            source_type=project_data.source_type,
            source_path=project_data.source_path,
            github_url=project_data.github_url,
            user_id=user_id,
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        return project

    @staticmethod
    def get_project(db: Session, user_id: int, project_id: int) -> Project:
        """Get a specific project by ID"""

        project = (
            db.query(Project)
            .filter(and_(Project.id == project_id, Project.user_id == user_id))
            .first()
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        return project

    @staticmethod
    def list_projects(
        db: Session,
        user_id: int,
        page: int = 1,
        per_page: int = 10,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List all projects for a user with pagination"""

        query = db.query(Project).filter(Project.user_id == user_id)

        # Add search filter if provided
        if search:
            query = query.filter(
                or_(
                    Project.name.ilike(f"%{search}%"),
                    Project.description.ilike(f"%{search}%"),
                )
            )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        projects = query.offset(offset).limit(per_page).all()

        return {
            "projects": [p.to_dict() for p in projects],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def update_project(
        db: Session, user_id: int, project_id: int, update_data: ProjectUpdate
    ) -> Project:
        """Update a project"""

        project = ProjectManager.get_project(db, user_id, project_id)

        # Check if new name conflicts with another project
        if update_data.name and update_data.name != project.name:
            existing = (
                db.query(Project)
                .filter(
                    and_(
                        Project.name == update_data.name,
                        Project.user_id == user_id,
                        Project.id != project_id,
                    )
                )
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Project '{update_data.name}' already exists",
                )

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(project, field, value)

        db.commit()
        db.refresh(project)

        return project

    @staticmethod
    def delete_project(db: Session, user_id: int, project_id: int) -> bool:
        """Delete a project and all associated data"""

        project = ProjectManager.get_project(db, user_id, project_id)

        # Delete project (cascade will handle related records)
        db.delete(project)
        db.commit()

        return True

    @staticmethod
    def get_project_stats(db: Session, user_id: int) -> ProjectStats:
        """Get statistics for all user projects"""

        # Get all projects for user
        projects = db.query(Project).filter(Project.user_id == user_id).all()

        total_apis = 0
        total_tests = 0
        total_tasks = 0
        security_issues = 0
        security_scores = []
        hours_saved = 0.0
        money_saved = 0.0

        for project in projects:
            total_apis += len(project.apis)
            total_tasks += len(project.tasks)

            # Count tests
            for api in project.apis:
                total_tests += len(api.tests)
                if api.security_score:
                    security_scores.append(api.security_score)
                if api.security_issues:
                    security_issues += len(api.security_issues)

            # Calculate business value
            for task in project.tasks:
                if task.hours_saved:
                    hours_saved += task.hours_saved
                if task.money_saved:
                    money_saved += task.money_saved

        avg_security = (
            sum(security_scores) / len(security_scores) if security_scores else 0.0
        )

        return ProjectStats(
            total_projects=len(projects),
            total_apis=total_apis,
            total_tests=total_tests,
            total_tasks=total_tasks,
            security_issues_found=security_issues,
            average_security_score=avg_security,
            hours_saved=hours_saved,
            money_saved=money_saved,
        )

    @staticmethod
    def clone_project(
        db: Session, user_id: int, project_id: int, new_name: str
    ) -> Project:
        """Clone an existing project"""

        source_project = ProjectManager.get_project(db, user_id, project_id)

        # Create new project
        new_project = Project(
            name=new_name,
            description=f"Clone of {source_project.name}",
            source_type=source_project.source_type,
            source_path=source_project.source_path,
            github_url=source_project.github_url,
            user_id=user_id,
        )

        db.add(new_project)
        db.flush()  # Get the new project ID

        # Clone APIs
        for api in source_project.apis:
            new_api = API(
                project_id=new_project.id,
                path=api.path,
                method=api.method,
                handler_name=api.handler_name,
                description=api.description,
                parameters=api.parameters,
                response_schema=api.response_schema,
                auth_required=api.auth_required,
                rate_limit=api.rate_limit,
                security_score=api.security_score,
                security_issues=api.security_issues,
                optimization_suggestions=api.optimization_suggestions,
                test_coverage=api.test_coverage,
            )
            db.add(new_api)

        # Clone OpenAPI specs
        for spec in (
            db.query(OpenAPISpec).filter(OpenAPISpec.project_id == project_id).all()
        ):
            new_spec = OpenAPISpec(
                project_id=new_project.id,
                version=spec.version,
                spec_data=spec.spec_data,
            )
            db.add(new_spec)

        db.commit()
        db.refresh(new_project)

        return new_project

    @staticmethod
    def start_orchestration(db: Session, user_id: int, project_id: int) -> Task:
        """Start orchestration for a project"""

        ProjectManager.get_project(db, user_id, project_id)

        # Create a new task
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id, project_id=project_id, status="pending", stage="initialization"
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        return task
