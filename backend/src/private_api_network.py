"""
Private API Network - Internal API catalog and discovery
Central directory for all team APIs with governance
"""

import uuid
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass
import re


class APIStatus(Enum):
    """API lifecycle status"""

    DRAFT = "draft"
    IN_DEVELOPMENT = "in_development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class APIVisibility(Enum):
    """API visibility levels"""

    PRIVATE = "private"  # Only owner can see
    TEAM = "team"  # Team members can see
    ORGANIZATION = "organization"  # All org members can see
    PUBLIC = "public"  # Public API


class APICategory(Enum):
    """API categories for organization"""

    INTERNAL = "internal"
    EXTERNAL = "external"
    PARTNER = "partner"
    MICROSERVICE = "microservice"
    INTEGRATION = "integration"
    UTILITY = "utility"
    EXPERIMENTAL = "experimental"


@dataclass
class APIVersion:
    """API version information"""

    version: str
    release_date: datetime
    changelog: str
    breaking_changes: List[str]
    deprecated_endpoints: List[str]
    new_endpoints: List[str]


class APIMetadata(BaseModel):
    """Comprehensive API metadata"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    version: str
    status: APIStatus
    visibility: APIVisibility
    category: APICategory

    # Ownership and team
    owner_id: str
    owner_email: str
    team_id: str
    team_name: str
    maintainers: List[str] = []

    # Technical details
    base_url: str
    protocols: List[str] = ["https"]
    authentication_methods: List[str] = []
    rate_limits: Dict[str, int] = {}

    # Documentation
    openapi_spec_url: Optional[str] = None
    documentation_url: Optional[str] = None
    postman_collection_url: Optional[str] = None

    # Dependencies
    depends_on: List[str] = []  # Other API IDs
    consumed_by: List[str] = []  # Services consuming this API

    # Compliance and governance
    compliance_tags: List[str] = []  # GDPR, HIPAA, SOC2, etc.
    security_score: Optional[float] = None
    last_security_scan: Optional[datetime] = None
    data_classification: str = "internal"  # public, internal, confidential, restricted

    # SLA and monitoring
    sla_tier: str = "standard"  # standard, premium, critical
    uptime_target: float = 99.9
    response_time_target_ms: int = 500
    monitoring_enabled: bool = True
    health_check_url: Optional[str] = None

    # Usage metrics
    total_requests_30d: int = 0
    unique_consumers_30d: int = 0
    avg_response_time_30d: float = 0
    error_rate_30d: float = 0

    # Lifecycle
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_deployed_at: Optional[datetime] = None
    deprecation_date: Optional[datetime] = None
    sunset_date: Optional[datetime] = None

    # Tags and search
    tags: List[str] = []
    keywords: List[str] = []

    # Version history
    versions: List[APIVersion] = []


class APIEndpoint(BaseModel):
    """Individual API endpoint details"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    api_id: str
    path: str
    method: str
    summary: str
    description: Optional[str] = None

    # Request/Response
    request_body_schema: Optional[Dict[str, Any]] = None
    response_schemas: Dict[int, Dict[str, Any]] = {}  # status code -> schema
    query_parameters: List[Dict[str, Any]] = []
    path_parameters: List[Dict[str, Any]] = []
    headers: List[Dict[str, Any]] = []

    # Performance
    avg_response_time_ms: float = 0
    p95_response_time_ms: float = 0
    requests_per_day: int = 0
    error_rate: float = 0

    # Governance
    requires_approval: bool = False
    approved_by: Optional[str] = None
    deprecated: bool = False
    deprecation_notice: Optional[str] = None


class APIConsumer(BaseModel):
    """API consumer registration"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    api_id: str
    consumer_name: str
    consumer_type: str  # service, application, partner, etc.
    contact_email: str

    # Access control
    api_key: str = Field(default_factory=lambda: str(uuid.uuid4()))
    allowed_endpoints: List[str] = []  # If empty, all endpoints allowed
    rate_limit_override: Optional[int] = None

    # Usage tracking
    total_requests: int = 0
    last_request_at: Optional[datetime] = None
    monthly_quota: Optional[int] = None
    current_month_usage: int = 0

    # Status
    active: bool = True
    approved: bool = False
    approved_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class PrivateAPINetwork:
    """Manage internal API catalog and discovery"""

    def __init__(self):
        self.apis: Dict[str, APIMetadata] = {}
        self.endpoints: Dict[str, List[APIEndpoint]] = {}
        self.consumers: Dict[str, List[APIConsumer]] = {}
        self.search_index: Dict[str, Set[str]] = {}  # keyword -> api_ids
        self.dependency_graph: Dict[str, Set[str]] = {}

    async def register_api(self, api_metadata: APIMetadata) -> APIMetadata:
        """Register a new API in the private network"""

        # Validate unique name
        for existing_api in self.apis.values():
            if (
                existing_api.name == api_metadata.name
                and existing_api.id != api_metadata.id
            ):
                raise ValueError(f"API with name '{api_metadata.name}' already exists")

        # Auto-generate keywords for search
        api_metadata.keywords = self._generate_keywords(api_metadata)

        # Add to catalog
        self.apis[api_metadata.id] = api_metadata

        # Update search index
        for keyword in api_metadata.keywords:
            if keyword not in self.search_index:
                self.search_index[keyword] = set()
            self.search_index[keyword].add(api_metadata.id)

        # Update dependency graph
        if api_metadata.depends_on:
            self.dependency_graph[api_metadata.id] = set(api_metadata.depends_on)
            # Update consumed_by for dependencies
            for dep_id in api_metadata.depends_on:
                if dep_id in self.apis:
                    self.apis[dep_id].consumed_by.append(api_metadata.id)

        return api_metadata

    async def discover_apis(
        self,
        query: Optional[str] = None,
        category: Optional[APICategory] = None,
        status: Optional[APIStatus] = None,
        team_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        visibility: Optional[APIVisibility] = None,
        user_role: str = "developer",
        user_team_id: Optional[str] = None,
    ) -> List[APIMetadata]:
        """Discover APIs with filters and access control"""

        results = []

        for api in self.apis.values():
            # Check visibility permissions
            if not self._check_visibility(api, user_role, user_team_id):
                continue

            # Apply filters
            if category and api.category != category:
                continue

            if status and api.status != status:
                continue

            if team_id and api.team_id != team_id:
                continue

            if tags:
                if not any(tag in api.tags for tag in tags):
                    continue

            if visibility and api.visibility != visibility:
                continue

            # Search query
            if query:
                query_lower = query.lower()
                if not any(
                    query_lower in field.lower()
                    for field in [api.name, api.description] + api.keywords + api.tags
                ):
                    continue

            results.append(api)

        # Sort by relevance and popularity
        results.sort(
            key=lambda x: (
                -x.unique_consumers_30d,  # Most used first
                -x.total_requests_30d,
                x.name,
            )
        )

        return results

    async def get_api_details(
        self,
        api_id: str,
        include_endpoints: bool = True,
        include_consumers: bool = False,
        user_role: str = "developer",
        user_team_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get detailed API information"""

        if api_id not in self.apis:
            raise ValueError(f"API {api_id} not found")

        api = self.apis[api_id]

        # Check access
        if not self._check_visibility(api, user_role, user_team_id):
            raise ValueError("Access denied")

        result = {
            "api": api.dict(),
            "health_status": await self._check_api_health(api),
            "dependencies": self._get_dependencies(api_id),
            "dependents": self._get_dependents(api_id),
        }

        if include_endpoints and api_id in self.endpoints:
            result["endpoints"] = [e.dict() for e in self.endpoints[api_id]]

        if include_consumers and user_role in ["admin", "owner"]:
            if api_id in self.consumers:
                result["consumers"] = [
                    {
                        "name": c.consumer_name,
                        "type": c.consumer_type,
                        "active": c.active,
                        "usage": c.total_requests,
                    }
                    for c in self.consumers[api_id]
                ]

        return result

    async def register_consumer(
        self,
        api_id: str,
        consumer_name: str,
        consumer_type: str,
        contact_email: str,
        auto_approve: bool = False,
    ) -> APIConsumer:
        """Register a new API consumer"""

        if api_id not in self.apis:
            raise ValueError(f"API {api_id} not found")

        api = self.apis[api_id]

        # Create consumer registration
        consumer = APIConsumer(
            api_id=api_id,
            consumer_name=consumer_name,
            consumer_type=consumer_type,
            contact_email=contact_email,
            approved=auto_approve or api.visibility == APIVisibility.PUBLIC,
        )

        # Add to consumers list
        if api_id not in self.consumers:
            self.consumers[api_id] = []
        self.consumers[api_id].append(consumer)

        # Update API metrics
        api.unique_consumers_30d += 1

        return consumer

    async def track_api_usage(
        self,
        api_id: str,
        consumer_id: str,
        endpoint_path: str,
        method: str,
        response_time_ms: float,
        status_code: int,
    ):
        """Track API usage metrics"""

        if api_id not in self.apis:
            return

        api = self.apis[api_id]

        # Update API metrics
        api.total_requests_30d += 1

        # Update running average response time
        alpha = 0.1  # Exponential moving average factor
        api.avg_response_time_30d = (
            alpha * response_time_ms + (1 - alpha) * api.avg_response_time_30d
        )

        # Update error rate
        if status_code >= 400:
            api.error_rate_30d = alpha * 1.0 + (1 - alpha) * api.error_rate_30d
        else:
            api.error_rate_30d = alpha * 0.0 + (1 - alpha) * api.error_rate_30d

        # Update consumer metrics
        if api_id in self.consumers:
            for consumer in self.consumers[api_id]:
                if consumer.id == consumer_id:
                    consumer.total_requests += 1
                    consumer.current_month_usage += 1
                    consumer.last_request_at = datetime.now()
                    break

        # Update endpoint metrics
        if api_id in self.endpoints:
            for endpoint in self.endpoints[api_id]:
                if endpoint.path == endpoint_path and endpoint.method == method:
                    endpoint.requests_per_day += 1
                    endpoint.avg_response_time_ms = (
                        alpha * response_time_ms
                        + (1 - alpha) * endpoint.avg_response_time_ms
                    )
                    if status_code >= 400:
                        endpoint.error_rate = (
                            alpha * 1.0 + (1 - alpha) * endpoint.error_rate
                        )
                    break

    async def deprecate_api(
        self,
        api_id: str,
        deprecation_notice: str,
        sunset_date: datetime,
        notify_consumers: bool = True,
    ) -> Dict[str, Any]:
        """Deprecate an API with notice period"""

        if api_id not in self.apis:
            raise ValueError(f"API {api_id} not found")

        api = self.apis[api_id]

        # Update status
        api.status = APIStatus.DEPRECATED
        api.deprecation_date = datetime.now()
        api.sunset_date = sunset_date

        # Mark all endpoints as deprecated
        if api_id in self.endpoints:
            for endpoint in self.endpoints[api_id]:
                endpoint.deprecated = True
                endpoint.deprecation_notice = deprecation_notice

        # Get affected consumers
        affected_consumers = []
        if api_id in self.consumers:
            affected_consumers = [
                {
                    "name": c.consumer_name,
                    "email": c.contact_email,
                    "usage": c.total_requests,
                }
                for c in self.consumers[api_id]
                if c.active
            ]

        # Get affected dependents
        affected_apis = self._get_dependents(api_id)

        return {
            "api_id": api_id,
            "api_name": api.name,
            "deprecation_date": api.deprecation_date.isoformat(),
            "sunset_date": sunset_date.isoformat(),
            "affected_consumers": affected_consumers,
            "affected_apis": affected_apis,
            "notice": deprecation_notice,
        }

    async def get_dependency_graph(
        self, api_id: Optional[str] = None, max_depth: int = 3
    ) -> Dict[str, Any]:
        """Get API dependency graph"""

        if api_id:
            # Get dependencies for specific API
            return self._build_dependency_tree(api_id, max_depth)
        else:
            # Get full dependency graph
            nodes = []
            edges = []

            for api in self.apis.values():
                nodes.append(
                    {
                        "id": api.id,
                        "name": api.name,
                        "status": api.status.value,
                        "category": api.category.value,
                        "consumers": api.unique_consumers_30d,
                    }
                )

                for dep_id in api.depends_on:
                    edges.append(
                        {"source": api.id, "target": dep_id, "type": "depends_on"}
                    )

            return {
                "nodes": nodes,
                "edges": edges,
                "total_apis": len(nodes),
                "total_dependencies": len(edges),
            }

    async def generate_api_report(
        self,
        team_id: Optional[str] = None,
        include_health: bool = True,
        include_usage: bool = True,
        include_compliance: bool = True,
    ) -> Dict[str, Any]:
        """Generate comprehensive API report"""

        apis = self.apis.values()
        if team_id:
            apis = [api for api in apis if api.team_id == team_id]

        report = {
            "generated_at": datetime.now().isoformat(),
            "total_apis": len(apis),
            "by_status": {},
            "by_category": {},
            "by_visibility": {},
            "health_summary": {},
            "usage_summary": {},
            "compliance_summary": {},
        }

        # Group by status
        for status in APIStatus:
            count = len([api for api in apis if api.status == status])
            if count > 0:
                report["by_status"][status.value] = count

        # Group by category
        for category in APICategory:
            count = len([api for api in apis if api.category == category])
            if count > 0:
                report["by_category"][category.value] = count

        # Group by visibility
        for visibility in APIVisibility:
            count = len([api for api in apis if api.visibility == visibility])
            if count > 0:
                report["by_visibility"][visibility.value] = count

        if include_health:
            healthy = len([api for api in apis if api.error_rate_30d < 0.01])
            warning = len([api for api in apis if 0.01 <= api.error_rate_30d < 0.05])
            critical = len([api for api in apis if api.error_rate_30d >= 0.05])

            report["health_summary"] = {
                "healthy": healthy,
                "warning": warning,
                "critical": critical,
                "avg_response_time": sum(api.avg_response_time_30d for api in apis)
                / len(apis)
                if apis
                else 0,
                "avg_error_rate": sum(api.error_rate_30d for api in apis) / len(apis)
                if apis
                else 0,
            }

        if include_usage:
            report["usage_summary"] = {
                "total_requests_30d": sum(api.total_requests_30d for api in apis),
                "total_consumers": sum(api.unique_consumers_30d for api in apis),
                "most_used_apis": sorted(
                    [
                        {"name": api.name, "requests": api.total_requests_30d}
                        for api in apis
                    ],
                    key=lambda x: x["requests"],
                    reverse=True,
                )[:10],
            }

        if include_compliance:
            compliance_tags = {}
            for api in apis:
                for tag in api.compliance_tags:
                    compliance_tags[tag] = compliance_tags.get(tag, 0) + 1

            report["compliance_summary"] = {
                "compliance_coverage": compliance_tags,
                "apis_without_compliance": len(
                    [api for api in apis if not api.compliance_tags]
                ),
                "apis_needing_security_scan": len(
                    [
                        api
                        for api in apis
                        if not api.last_security_scan
                        or (datetime.now() - api.last_security_scan).days > 30
                    ]
                ),
            }

        return report

    def _check_visibility(
        self, api: APIMetadata, user_role: str, user_team_id: Optional[str]
    ) -> bool:
        """Check if user can access API based on visibility"""

        if api.visibility == APIVisibility.PUBLIC:
            return True

        if api.visibility == APIVisibility.ORGANIZATION:
            return True  # Assuming user is in organization

        if api.visibility == APIVisibility.TEAM:
            return user_team_id == api.team_id

        if api.visibility == APIVisibility.PRIVATE:
            return user_role == "admin" or user_team_id == api.team_id

        return False

    def _generate_keywords(self, api: APIMetadata) -> List[str]:
        """Generate search keywords from API metadata"""

        keywords = []

        # Extract words from name and description
        text = f"{api.name} {api.description}".lower()
        words = re.findall(r"\b[a-z]+\b", text)
        keywords.extend(words)

        # Add tags
        keywords.extend([tag.lower() for tag in api.tags])

        # Add category and status
        keywords.append(api.category.value)
        keywords.append(api.status.value)

        # Add team name
        keywords.append(api.team_name.lower())

        # Remove duplicates
        return list(set(keywords))

    def _get_dependencies(self, api_id: str) -> List[Dict[str, str]]:
        """Get API dependencies"""

        if api_id not in self.apis:
            return []

        api = self.apis[api_id]
        dependencies = []

        for dep_id in api.depends_on:
            if dep_id in self.apis:
                dep_api = self.apis[dep_id]
                dependencies.append(
                    {"id": dep_id, "name": dep_api.name, "status": dep_api.status.value}
                )

        return dependencies

    def _get_dependents(self, api_id: str) -> List[Dict[str, str]]:
        """Get APIs that depend on this API"""

        if api_id not in self.apis:
            return []

        api = self.apis[api_id]
        dependents = []

        for dep_id in api.consumed_by:
            if dep_id in self.apis:
                dep_api = self.apis[dep_id]
                dependents.append(
                    {"id": dep_id, "name": dep_api.name, "status": dep_api.status.value}
                )

        return dependents

    def _build_dependency_tree(
        self,
        api_id: str,
        max_depth: int,
        current_depth: int = 0,
        visited: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """Build dependency tree for an API"""

        if visited is None:
            visited = set()

        if api_id in visited or current_depth >= max_depth:
            return None

        visited.add(api_id)

        if api_id not in self.apis:
            return None

        api = self.apis[api_id]

        node = {
            "id": api_id,
            "name": api.name,
            "status": api.status.value,
            "dependencies": [],
            "dependents": [],
        }

        # Add dependencies
        for dep_id in api.depends_on:
            dep_node = self._build_dependency_tree(
                dep_id, max_depth, current_depth + 1, visited
            )
            if dep_node:
                node["dependencies"].append(dep_node)

        # Add dependents
        for dep_id in api.consumed_by:
            dep_node = self._build_dependency_tree(
                dep_id, max_depth, current_depth + 1, visited
            )
            if dep_node:
                node["dependents"].append(dep_node)

        return node

    async def _check_api_health(self, api: APIMetadata) -> str:
        """Check API health status"""

        if api.status in [APIStatus.DEPRECATED, APIStatus.RETIRED]:
            return "deprecated"

        if api.error_rate_30d > 0.05:
            return "critical"

        if api.error_rate_30d > 0.01:
            return "warning"

        if api.avg_response_time_30d > api.response_time_target_ms * 2:
            return "warning"

        return "healthy"


# Global instance
private_api_network = PrivateAPINetwork()
