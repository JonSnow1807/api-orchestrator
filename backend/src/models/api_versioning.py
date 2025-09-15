"""
API Versioning System
Track API changes, versions, and diffs over time
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import json
import difflib
from typing import Dict, List, Any, Optional

from src.database import Base

class APIVersion(Base):
    """Track different versions of an API specification"""
    __tablename__ = "api_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, ForeignKey('api_specs.id', ondelete='CASCADE'))
    workspace_id = Column(Integer, ForeignKey('workspaces.id', ondelete='CASCADE'))
    
    # Version information
    version_number = Column(String(50), nullable=False)  # e.g., "1.0.0", "2.1.3"
    version_tag = Column(String(100))  # e.g., "stable", "beta", "deprecated"
    is_current = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)
    
    # Specification content
    spec_content = Column(JSON, nullable=False)  # Full OpenAPI/GraphQL spec
    spec_format = Column(String(20))  # "openapi", "graphql", "asyncapi"
    
    # Change information
    change_summary = Column(Text)  # Human-readable summary of changes
    breaking_changes = Column(JSON, default=list)  # List of breaking changes
    deprecated_items = Column(JSON, default=list)  # List of deprecated endpoints/fields
    added_items = Column(JSON, default=list)  # New endpoints/fields
    modified_items = Column(JSON, default=list)  # Modified endpoints/fields
    removed_items = Column(JSON, default=list)  # Removed endpoints/fields
    
    # Metadata
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    deprecated_at = Column(DateTime)
    sunset_date = Column(DateTime)  # When this version will be retired
    
    # Statistics
    endpoint_count = Column(Integer, default=0)
    schema_count = Column(Integer, default=0)
    
    # Relationships
    api_spec = relationship("APISpec", backref="versions")
    creator = relationship("User", foreign_keys=[created_by])
    comparisons = relationship("APIVersionComparison",
                              foreign_keys="APIVersionComparison.version_a_id",
                              back_populates="version_a")
    changelog_entries = relationship("APIChangelog", back_populates="version", cascade="all, delete-orphan")
    
    def compare_with(self, other_version: 'APIVersion') -> Dict[str, Any]:
        """Compare this version with another version"""
        comparison = {
            'version_a': self.version_number,
            'version_b': other_version.version_number,
            'breaking_changes': [],
            'additions': [],
            'modifications': [],
            'deletions': [],
            'deprecations': []
        }
        
        # Compare endpoints
        if self.spec_format == 'openapi' and other_version.spec_format == 'openapi':
            comparison = self._compare_openapi_specs(
                self.spec_content, 
                other_version.spec_content,
                comparison
            )
        elif self.spec_format == 'graphql' and other_version.spec_format == 'graphql':
            comparison = self._compare_graphql_specs(
                self.spec_content,
                other_version.spec_content,
                comparison
            )
        
        return comparison
    
    def _compare_openapi_specs(self, spec_a: Dict, spec_b: Dict, comparison: Dict) -> Dict:
        """Compare two OpenAPI specifications"""
        paths_a = spec_a.get('paths', {})
        paths_b = spec_b.get('paths', {})
        
        # Find added paths
        for path in paths_b:
            if path not in paths_a:
                comparison['additions'].append({
                    'type': 'endpoint',
                    'path': path,
                    'methods': list(paths_b[path].keys())
                })
        
        # Find removed paths
        for path in paths_a:
            if path not in paths_b:
                comparison['deletions'].append({
                    'type': 'endpoint',
                    'path': path,
                    'methods': list(paths_a[path].keys())
                })
                comparison['breaking_changes'].append(f"Removed endpoint: {path}")
        
        # Find modified paths
        for path in paths_a:
            if path in paths_b:
                methods_a = set(paths_a[path].keys())
                methods_b = set(paths_b[path].keys())
                
                # Check for method changes
                added_methods = methods_b - methods_a
                removed_methods = methods_a - methods_b
                
                if added_methods:
                    comparison['additions'].append({
                        'type': 'method',
                        'path': path,
                        'methods': list(added_methods)
                    })
                
                if removed_methods:
                    comparison['deletions'].append({
                        'type': 'method',
                        'path': path,
                        'methods': list(removed_methods)
                    })
                    comparison['breaking_changes'].append(
                        f"Removed methods from {path}: {', '.join(removed_methods)}"
                    )
                
                # Check for parameter changes
                for method in methods_a & methods_b:
                    params_a = paths_a[path][method].get('parameters', [])
                    params_b = paths_b[path][method].get('parameters', [])
                    
                    # Check for required parameter additions (breaking change)
                    required_params_b = {p['name'] for p in params_b if p.get('required', False)}
                    required_params_a = {p['name'] for p in params_a if p.get('required', False)}
                    
                    new_required = required_params_b - required_params_a
                    if new_required:
                        comparison['breaking_changes'].append(
                            f"New required parameters in {method} {path}: {', '.join(new_required)}"
                        )
        
        return comparison
    
    def _compare_graphql_specs(self, spec_a: Dict, spec_b: Dict, comparison: Dict) -> Dict:
        """Compare two GraphQL schemas"""
        # Implementation for GraphQL comparison
        # This would compare types, queries, mutations, subscriptions
        return comparison

class APIVersionComparison(Base):
    """Store detailed comparisons between API versions"""
    __tablename__ = "api_version_comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    version_a_id = Column(Integer, ForeignKey('api_versions.id', ondelete='CASCADE'))
    version_b_id = Column(Integer, ForeignKey('api_versions.id', ondelete='CASCADE'))
    
    # Comparison results
    comparison_result = Column(JSON)  # Full comparison data
    breaking_change_count = Column(Integer, default=0)
    addition_count = Column(Integer, default=0)
    modification_count = Column(Integer, default=0)
    deletion_count = Column(Integer, default=0)
    
    # Compatibility score (0-100)
    compatibility_score = Column(Float, default=100.0)
    
    # Migration guide
    migration_guide = Column(Text)  # AI-generated migration guide
    estimated_migration_effort = Column(String(20))  # "low", "medium", "high"
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    version_a = relationship("APIVersion", foreign_keys=[version_a_id])
    version_b = relationship("APIVersion", foreign_keys=[version_b_id])
    creator = relationship("User", foreign_keys=[created_by])

class APIChangelog(Base):
    """Detailed changelog entries for API versions"""
    __tablename__ = "api_changelog"
    
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey('api_versions.id', ondelete='CASCADE'))
    workspace_id = Column(Integer, ForeignKey('workspaces.id', ondelete='CASCADE'))
    
    # Change details
    change_type = Column(String(50))  # "feature", "bugfix", "breaking", "deprecation", "security"
    change_category = Column(String(50))  # "endpoint", "schema", "authentication", "parameter"
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Affected items
    affected_endpoints = Column(JSON, default=list)
    affected_schemas = Column(JSON, default=list)
    
    # Impact assessment
    impact_level = Column(String(20))  # "low", "medium", "high", "critical"
    requires_client_update = Column(Boolean, default=False)
    
    # Metadata
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    version = relationship("APIVersion", back_populates="changelog_entries")
    creator = relationship("User", foreign_keys=[created_by])

class APIVersionNotification(Base):
    """Notifications for API version changes"""
    __tablename__ = "api_version_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id', ondelete='CASCADE'))
    version_id = Column(Integer, ForeignKey('api_versions.id', ondelete='CASCADE'))
    
    # Notification details
    notification_type = Column(String(50))  # "new_version", "deprecation", "sunset", "breaking_change"
    title = Column(String(200))
    message = Column(Text)
    
    # Target audience
    target_users = Column(JSON, default=list)  # List of user IDs to notify
    target_roles = Column(JSON, default=list)  # Roles to notify
    
    # Status
    sent_at = Column(DateTime)
    read_by = Column(JSON, default=dict)  # User ID -> timestamp mapping
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    version = relationship("APIVersion")
    creator = relationship("User", foreign_keys=[created_by])

class APIVersioningService:
    """Service class for API versioning operations"""
    
    @staticmethod
    def create_version(db, api_id: int, spec_content: Dict, 
                      version_number: str, user_id: int,
                      change_summary: str = None) -> APIVersion:
        """Create a new API version"""
        # Get the current version if exists
        current_version = db.query(APIVersion).filter(
            APIVersion.api_id == api_id,
            APIVersion.is_current == True
        ).first()
        
        # Create new version
        new_version = APIVersion(
            api_id=api_id,
            version_number=version_number,
            spec_content=spec_content,
            change_summary=change_summary,
            created_by=user_id,
            is_current=True
        )
        
        # If there's a current version, compare and unset it
        if current_version:
            current_version.is_current = False
            
            # Perform comparison
            comparison = new_version.compare_with(current_version)
            
            # Store comparison results
            new_version.breaking_changes = comparison.get('breaking_changes', [])
            new_version.added_items = comparison.get('additions', [])
            new_version.modified_items = comparison.get('modifications', [])
            new_version.removed_items = comparison.get('deletions', [])
            
            # Create comparison record
            comparison_record = APIVersionComparison(
                version_a_id=current_version.id,
                version_b_id=new_version.id,
                comparison_result=comparison,
                breaking_change_count=len(comparison.get('breaking_changes', [])),
                addition_count=len(comparison.get('additions', [])),
                modification_count=len(comparison.get('modifications', [])),
                deletion_count=len(comparison.get('deletions', [])),
                created_by=user_id
            )
            db.add(comparison_record)
        
        # Calculate statistics
        if spec_content.get('paths'):
            new_version.endpoint_count = len(spec_content.get('paths', {}))
        if spec_content.get('components', {}).get('schemas'):
            new_version.schema_count = len(spec_content['components']['schemas'])
        
        db.add(new_version)
        db.commit()
        db.refresh(new_version)
        
        return new_version
    
    @staticmethod
    def get_version_timeline(db, api_id: int) -> List[Dict]:
        """Get timeline of all versions for an API"""
        versions = db.query(APIVersion).filter(
            APIVersion.api_id == api_id
        ).order_by(APIVersion.created_at.desc()).all()
        
        timeline = []
        for version in versions:
            timeline.append({
                'id': version.id,
                'version': version.version_number,
                'created_at': version.created_at,
                'created_by': version.creator.username if version.creator else 'Unknown',
                'is_current': version.is_current,
                'is_published': version.is_published,
                'breaking_changes': len(version.breaking_changes or []),
                'change_summary': version.change_summary
            })
        
        return timeline
    
    @staticmethod
    def rollback_version(db, api_id: int, target_version_id: int, user_id: int) -> APIVersion:
        """Rollback to a previous API version"""
        target_version = db.query(APIVersion).filter(
            APIVersion.id == target_version_id,
            APIVersion.api_id == api_id
        ).first()
        
        if not target_version:
            raise ValueError("Target version not found")
        
        # Create a new version based on the target
        rollback_version = APIVersioningService.create_version(
            db,
            api_id,
            target_version.spec_content,
            f"{target_version.version_number}-rollback",
            user_id,
            f"Rollback to version {target_version.version_number}"
        )
        
        return rollback_version