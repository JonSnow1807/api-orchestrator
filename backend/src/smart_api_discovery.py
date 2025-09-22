"""
Smart AI-Powered API Discovery System
Advanced ML-driven API discovery with pattern recognition, behavioral analysis, and predictive recommendations
"""

from typing import Optional, Dict, Any, List, Set, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import uuid
import time
import logging
import re
import hashlib
import os
from collections import defaultdict, deque
import numpy as np
from urllib.parse import urlparse, parse_qs

# Optional ML imports with graceful fallbacks
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import DBSCAN
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.ensemble import IsolationForest
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

# Import existing systems
from src.kill_shots.telepathic_discovery import TelepathicDiscovery, DiscoveredAPI
from src.ai_suggestions import InlineAISuggestions, AISuggestion, SuggestionType

# Import advanced ML models
try:
    from src.ml_models.advanced_api_discovery import (
        AdvancedAPIDiscoveryEngine,
        ModelPrediction,
        initialize_advanced_models,
        analyze_api_with_ml,
        detect_traffic_anomalies
    )
    HAS_ADVANCED_ML = True
except ImportError:
    HAS_ADVANCED_ML = False

class DiscoveryConfidence(str, Enum):
    VERY_HIGH = "very_high"      # 90-100%
    HIGH = "high"                # 70-89%
    MEDIUM = "medium"            # 50-69%
    LOW = "low"                  # 30-49%
    VERY_LOW = "very_low"        # 0-29%

class APICategory(str, Enum):
    REST_API = "rest_api"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    GRPC = "grpc"
    SOAP = "soap"
    WEBHOOK = "webhook"
    STREAMING = "streaming"
    MICROSERVICE = "microservice"
    THIRD_PARTY = "third_party"
    INTERNAL = "internal"

class DiscoveryMethod(str, Enum):
    ML_PATTERN_ANALYSIS = "ml_pattern_analysis"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    NETWORK_TRAFFIC = "network_traffic"
    CODE_ANALYSIS = "code_analysis"
    LOG_MINING = "log_mining"
    DNS_ENUMERATION = "dns_enumeration"
    SSL_CERTIFICATE = "ssl_certificate"
    SUBDOMAIN_DISCOVERY = "subdomain_discovery"
    PORT_SCANNING = "port_scanning"
    WEB_CRAWLING = "web_crawling"
    AI_PREDICTION = "ai_prediction"

@dataclass
class SmartAPIEndpoint:
    """Enhanced API endpoint with ML-derived insights"""
    url: str
    method: str
    category: APICategory
    confidence: DiscoveryConfidence
    discovery_method: DiscoveryMethod

    # Enhanced metadata
    predicted_parameters: List[Dict[str, Any]] = field(default_factory=list)
    predicted_response_schema: Optional[Dict[str, Any]] = None
    authentication_predictions: List[str] = field(default_factory=list)
    rate_limiting_predictions: Optional[Dict[str, Any]] = None
    usage_patterns: Dict[str, Any] = field(default_factory=dict)

    # ML features
    similarity_score: float = 0.0
    anomaly_score: float = 0.0
    clustering_label: int = -1

    # Behavioral insights
    traffic_volume: int = 0
    response_time_patterns: List[float] = field(default_factory=list)
    error_patterns: Dict[str, int] = field(default_factory=dict)

    # Discovery metadata
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    last_verified: Optional[datetime] = None
    verification_status: str = "unverified"
    tags: Set[str] = field(default_factory=set)

@dataclass
class APICluster:
    """Cluster of related APIs discovered through ML"""
    cluster_id: str
    category: APICategory
    endpoints: List[SmartAPIEndpoint]
    common_patterns: Dict[str, Any]
    cluster_confidence: float
    potential_base_url: Optional[str] = None

@dataclass
class DiscoveryInsight:
    """ML-generated insight about discovered APIs"""
    insight_type: str
    description: str
    confidence: float
    related_endpoints: List[str]
    actionable_recommendation: str
    supporting_data: Dict[str, Any] = field(default_factory=dict)

class SmartAPIDiscovery:
    """AI/ML-powered API discovery with advanced pattern recognition"""

    def __init__(self):
        self.telepathic_discovery = TelepathicDiscovery()
        self.ai_suggestions = InlineAISuggestions()

        # Discovery state
        self.discovered_endpoints: Dict[str, SmartAPIEndpoint] = {}
        self.api_clusters: Dict[str, APICluster] = {}
        self.discovery_insights: List[DiscoveryInsight] = []

        # ML models and components
        self.tfidf_vectorizer = None
        self.clustering_model = None
        self.anomaly_detector = None
        self.nlp_pipeline = None

        # Advanced ML engine
        self.advanced_ml_engine = None
        if HAS_ADVANCED_ML:
            from src.ml_models.advanced_api_discovery import advanced_discovery_engine
            self.advanced_ml_engine = advanced_discovery_engine

        # Pattern databases
        self.known_patterns = self._load_api_patterns()
        self.behavior_patterns = defaultdict(list)
        self.traffic_patterns = defaultdict(list)

        # Real-time monitoring
        self.traffic_buffer = deque(maxlen=10000)
        self.pattern_cache = {}

        self.initialized = False

    async def initialize(self):
        """Initialize ML models and discovery components"""

        if HAS_SKLEARN:
            await self._initialize_ml_models()

        if HAS_TRANSFORMERS:
            await self._initialize_nlp_models()

        # Initialize pattern recognition
        await self._initialize_pattern_recognition()

        # Initialize advanced ML models
        if HAS_ADVANCED_ML and self.advanced_ml_engine:
            await self.advanced_ml_engine.initialize_models()
            logging.info("🚀 Advanced ML models initialized")

        self.initialized = True
        logging.info("🧠 Smart API Discovery system initialized")

    async def _initialize_ml_models(self):
        """Initialize scikit-learn models"""

        # TF-IDF for API URL pattern analysis
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 3),
            analyzer='char_wb'
        )

        # DBSCAN for clustering similar APIs
        self.clustering_model = DBSCAN(
            eps=0.3,
            min_samples=2,
            metric='cosine'
        )

        # Isolation Forest for anomaly detection
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            random_state=42
        )

    async def _initialize_nlp_models(self):
        """Initialize NLP models for semantic understanding"""
        try:
            # Initialize text classification pipeline
            self.nlp_pipeline = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",
                return_all_scores=True
            )
        except Exception as e:
            logging.warning(f"Could not initialize NLP models: {e}")

    async def _initialize_pattern_recognition(self):
        """Initialize pattern recognition systems"""

        # Load common API patterns
        self.known_patterns = {
            "rest_patterns": [
                r"/api/v\d+/",
                r"/rest/",
                r"/api/",
                r"/(users|user)/\d+",
                r"/(products|items)/\w+",
                r"/\w+/\{id\}",
            ],
            "graphql_patterns": [
                r"/graphql",
                r"/graph",
                r"/gql",
            ],
            "websocket_patterns": [
                r"/ws/",
                r"/websocket/",
                r"/socket\.io/",
            ],
            "auth_patterns": [
                r"/auth/",
                r"/login",
                r"/oauth/",
                r"/token",
            ]
        }

    def _load_api_patterns(self) -> Dict[str, List[str]]:
        """Load known API URL patterns"""
        return {
            "common_endpoints": [
                "/api/users", "/api/auth", "/api/products", "/api/orders",
                "/api/health", "/api/status", "/api/version", "/api/docs"
            ],
            "parameter_patterns": [
                "id", "user_id", "product_id", "limit", "offset", "page",
                "sort", "filter", "search", "q", "format", "callback"
            ],
            "auth_indicators": [
                "authorization", "bearer", "token", "api_key", "x-api-key",
                "authentication", "auth", "login", "oauth"
            ]
        }

    async def discover_apis_with_ml(self,
                                  target: Optional[str] = None,
                                  deep_analysis: bool = True,
                                  include_predictions: bool = True) -> List[SmartAPIEndpoint]:
        """
        Comprehensive ML-powered API discovery
        """

        logging.info("🚀 Starting ML-powered API discovery")

        # Step 1: Use existing telepathic discovery
        base_discoveries = await self.telepathic_discovery.full_telepathic_scan(target or "localhost")

        # Step 2: Convert to smart endpoints with ML analysis
        smart_endpoints = []
        for api in base_discoveries:
            smart_endpoint = await self._enhance_with_ml_analysis(api)
            smart_endpoints.append(smart_endpoint)
            self.discovered_endpoints[smart_endpoint.url] = smart_endpoint

        # Step 3: Pattern-based discovery
        pattern_endpoints = await self._discover_by_patterns(target)
        smart_endpoints.extend(pattern_endpoints)

        # Step 4: Behavioral analysis discovery
        if deep_analysis:
            behavioral_endpoints = await self._discover_by_behavior()
            smart_endpoints.extend(behavioral_endpoints)

        # Step 5: ML clustering and similarity analysis
        if HAS_SKLEARN and len(smart_endpoints) > 3:
            await self._perform_clustering_analysis(smart_endpoints)

        # Step 6: Generate predictions for missing endpoints
        if include_predictions:
            predicted_endpoints = await self._predict_missing_endpoints(smart_endpoints)
            smart_endpoints.extend(predicted_endpoints)

        # Step 7: Advanced ML analysis
        if HAS_ADVANCED_ML and self.advanced_ml_engine:
            ml_enhanced_endpoints = await self._enhance_with_advanced_ml(smart_endpoints)
            smart_endpoints = ml_enhanced_endpoints

        # Step 8: Generate insights
        await self._generate_discovery_insights(smart_endpoints)

        logging.info(f"✅ Discovery complete: {len(smart_endpoints)} smart endpoints found")
        return smart_endpoints

    async def _enhance_with_ml_analysis(self, base_api: DiscoveredAPI) -> SmartAPIEndpoint:
        """Enhance basic API discovery with ML analysis"""

        # Categorize API
        category = await self._categorize_api(base_api.url, base_api.method)

        # Calculate confidence
        confidence = await self._calculate_confidence(base_api)

        # Predict parameters
        predicted_params = await self._predict_parameters(base_api.url, base_api.method)

        # Predict authentication
        auth_predictions = await self._predict_authentication(base_api.url)

        # Create smart endpoint
        smart_endpoint = SmartAPIEndpoint(
            url=base_api.url,
            method=base_api.method,
            category=category,
            confidence=confidence,
            discovery_method=DiscoveryMethod.ML_PATTERN_ANALYSIS,
            predicted_parameters=predicted_params,
            authentication_predictions=auth_predictions,
            tags={"source": "telepathic_discovery"}
        )

        return smart_endpoint

    async def _categorize_api(self, url: str, method: str) -> APICategory:
        """Use ML to categorize API type"""

        url_lower = url.lower()

        # Pattern-based categorization
        if any(pattern in url_lower for pattern in ["/graphql", "/graph", "/gql"]):
            return APICategory.GRAPHQL
        elif any(pattern in url_lower for pattern in ["/ws/", "/websocket", "/socket.io"]):
            return APICategory.WEBSOCKET
        elif "grpc" in url_lower or ":50051" in url:
            return APICategory.GRPC
        elif any(pattern in url_lower for pattern in ["/soap", "/wsdl"]):
            return APICategory.SOAP
        elif "webhook" in url_lower or "hook" in url_lower:
            return APICategory.WEBHOOK
        elif "stream" in url_lower or "sse" in url_lower:
            return APICategory.STREAMING
        elif "localhost" in url or "127.0.0.1" in url or "internal" in url_lower:
            return APICategory.INTERNAL
        elif any(domain in url_lower for domain in ["api.github.com", "api.stripe.com", "graph.facebook.com"]):
            return APICategory.THIRD_PARTY
        else:
            return APICategory.REST_API

    async def _calculate_confidence(self, base_api: DiscoveredAPI) -> DiscoveryConfidence:
        """Calculate confidence level using multiple factors"""

        confidence_score = base_api.confidence

        # Boost confidence based on discovery method
        method_boost = {
            "code_analysis": 0.2,
            "network_scan": 0.15,
            "dns_enum": 0.1,
            "swagger_scan": 0.25
        }

        confidence_score += method_boost.get(base_api.discovered_via, 0)

        # Boost for common API patterns
        url_lower = base_api.url.lower()
        if any(pattern in url_lower for pattern in ["/api/", "/rest/", "/v1/", "/v2/"]):
            confidence_score += 0.1

        # Boost for documentation presence
        if base_api.documentation_url:
            confidence_score += 0.15

        # Convert to enum
        if confidence_score >= 0.9:
            return DiscoveryConfidence.VERY_HIGH
        elif confidence_score >= 0.7:
            return DiscoveryConfidence.HIGH
        elif confidence_score >= 0.5:
            return DiscoveryConfidence.MEDIUM
        elif confidence_score >= 0.3:
            return DiscoveryConfidence.LOW
        else:
            return DiscoveryConfidence.VERY_LOW

    async def _predict_parameters(self, url: str, method: str) -> List[Dict[str, Any]]:
        """Predict likely parameters for the API endpoint"""

        predicted_params = []
        url_lower = url.lower()

        # Pattern-based parameter prediction
        if "users" in url_lower:
            predicted_params.extend([
                {"name": "user_id", "type": "integer", "required": True, "location": "path"},
                {"name": "limit", "type": "integer", "required": False, "location": "query"},
                {"name": "offset", "type": "integer", "required": False, "location": "query"}
            ])

        if "search" in url_lower or method == "GET":
            predicted_params.extend([
                {"name": "q", "type": "string", "required": False, "location": "query"},
                {"name": "sort", "type": "string", "required": False, "location": "query"},
                {"name": "filter", "type": "string", "required": False, "location": "query"}
            ])

        if method in ["POST", "PUT", "PATCH"]:
            predicted_params.append({
                "name": "body", "type": "object", "required": True, "location": "body"
            })

        # Extract path parameters
        path_params = re.findall(r'/\{(\w+)\}', url)
        for param in path_params:
            predicted_params.append({
                "name": param, "type": "string", "required": True, "location": "path"
            })

        return predicted_params

    async def _predict_authentication(self, url: str) -> List[str]:
        """Predict authentication methods for the API"""

        auth_predictions = []
        url_lower = url.lower()

        # Pattern-based auth prediction
        if any(auth_pattern in url_lower for auth_pattern in ["auth", "login", "oauth", "token"]):
            auth_predictions.extend(["bearer_token", "oauth2", "api_key"])

        if "api" in url_lower:
            auth_predictions.append("api_key")

        if "graphql" in url_lower:
            auth_predictions.extend(["bearer_token", "jwt"])

        # Default predictions for secure endpoints
        if "https" in url or any(secure_path in url_lower for secure_path in ["admin", "user", "account"]):
            auth_predictions.append("bearer_token")

        return list(set(auth_predictions))  # Remove duplicates

    async def _discover_by_patterns(self, target: Optional[str]) -> List[SmartAPIEndpoint]:
        """Discover APIs using learned patterns"""

        pattern_endpoints = []

        if not target:
            return pattern_endpoints

        # Common API path patterns
        common_paths = [
            "/api/v1/users", "/api/v1/auth", "/api/v1/products",
            "/api/v2/users", "/api/v2/auth", "/api/v2/products",
            "/rest/users", "/rest/auth", "/rest/products",
            "/graphql", "/api/graphql",
            "/health", "/status", "/metrics", "/docs", "/swagger",
            "/ws", "/websocket", "/socket.io"
        ]

        base_url = f"http://{target}" if not target.startswith("http") else target

        for path in common_paths:
            url = f"{base_url}{path}"

            # Skip if already discovered
            if url in self.discovered_endpoints:
                continue

            category = await self._categorize_api(url, "GET")

            endpoint = SmartAPIEndpoint(
                url=url,
                method="GET",
                category=category,
                confidence=DiscoveryConfidence.MEDIUM,
                discovery_method=DiscoveryMethod.ML_PATTERN_ANALYSIS,
                predicted_parameters=await self._predict_parameters(url, "GET"),
                authentication_predictions=await self._predict_authentication(url),
                tags={"source": "pattern_discovery"}
            )

            pattern_endpoints.append(endpoint)
            self.discovered_endpoints[url] = endpoint

        return pattern_endpoints

    async def _discover_by_behavior(self) -> List[SmartAPIEndpoint]:
        """Discover APIs through behavioral analysis of network traffic"""

        behavioral_endpoints = []

        # Analyze traffic patterns from the buffer
        if not self.traffic_buffer:
            return behavioral_endpoints

        # Group requests by URL patterns
        url_patterns = defaultdict(list)
        for traffic_item in self.traffic_buffer:
            url = traffic_item.get("url", "")
            url_patterns[self._extract_url_pattern(url)].append(traffic_item)

        # Identify frequent patterns that might be APIs
        for pattern, requests in url_patterns.items():
            if len(requests) >= 5 and self._looks_like_api(pattern):
                endpoint = SmartAPIEndpoint(
                    url=pattern,
                    method="GET",  # Default, would be refined
                    category=await self._categorize_api(pattern, "GET"),
                    confidence=DiscoveryConfidence.HIGH,
                    discovery_method=DiscoveryMethod.BEHAVIORAL_ANALYSIS,
                    traffic_volume=len(requests),
                    tags={"source": "behavioral_analysis"}
                )

                behavioral_endpoints.append(endpoint)

        return behavioral_endpoints

    def _extract_url_pattern(self, url: str) -> str:
        """Extract pattern from URL by replacing dynamic parts"""
        # Replace numbers with {id}
        pattern = re.sub(r'/\d+', '/{id}', url)
        # Replace UUIDs with {uuid}
        pattern = re.sub(r'/[a-f0-9-]{36}', '/{uuid}', pattern)
        return pattern

    def _looks_like_api(self, url: str) -> bool:
        """Determine if URL pattern looks like an API"""
        api_indicators = ["/api/", "/rest/", "/v1/", "/v2/", "/graphql", "/ws/"]
        return any(indicator in url.lower() for indicator in api_indicators)

    async def _perform_clustering_analysis(self, endpoints: List[SmartAPIEndpoint]):
        """Perform ML clustering to find related APIs"""

        if not HAS_SKLEARN or len(endpoints) < 3:
            return

        # Extract features for clustering
        urls = [ep.url for ep in endpoints]

        try:
            # Vectorize URLs
            url_vectors = self.tfidf_vectorizer.fit_transform(urls)

            # Perform clustering
            cluster_labels = self.clustering_model.fit_predict(url_vectors.toarray())

            # Group endpoints by cluster
            clusters = defaultdict(list)
            for i, label in enumerate(cluster_labels):
                if label != -1:  # Ignore noise points
                    endpoints[i].clustering_label = label
                    clusters[label].append(endpoints[i])

            # Create API clusters
            for cluster_id, cluster_endpoints in clusters.items():
                if len(cluster_endpoints) >= 2:
                    common_patterns = self._extract_common_patterns(cluster_endpoints)

                    api_cluster = APICluster(
                        cluster_id=f"cluster_{cluster_id}",
                        category=self._determine_cluster_category(cluster_endpoints),
                        endpoints=cluster_endpoints,
                        common_patterns=common_patterns,
                        cluster_confidence=np.mean([self._confidence_to_float(ep.confidence) for ep in cluster_endpoints])
                    )

                    self.api_clusters[api_cluster.cluster_id] = api_cluster

        except Exception as e:
            logging.warning(f"Clustering analysis failed: {e}")

    def _extract_common_patterns(self, endpoints: List[SmartAPIEndpoint]) -> Dict[str, Any]:
        """Extract common patterns from clustered endpoints"""

        patterns = {
            "common_base_path": "",
            "common_parameters": [],
            "common_methods": [],
            "common_auth": []
        }

        # Find common base path
        urls = [ep.url for ep in endpoints]
        if urls:
            common_prefix = os.path.commonprefix(urls)
            patterns["common_base_path"] = common_prefix

        # Find common parameters
        all_params = []
        for ep in endpoints:
            all_params.extend([p["name"] for p in ep.predicted_parameters])

        param_counts = defaultdict(int)
        for param in all_params:
            param_counts[param] += 1

        patterns["common_parameters"] = [
            param for param, count in param_counts.items()
            if count >= len(endpoints) / 2
        ]

        return patterns

    def _determine_cluster_category(self, endpoints: List[SmartAPIEndpoint]) -> APICategory:
        """Determine category for a cluster of endpoints"""
        categories = [ep.category for ep in endpoints]
        return max(set(categories), key=categories.count)

    def _confidence_to_float(self, confidence: DiscoveryConfidence) -> float:
        """Convert confidence enum to float for calculations"""
        mapping = {
            DiscoveryConfidence.VERY_HIGH: 0.95,
            DiscoveryConfidence.HIGH: 0.8,
            DiscoveryConfidence.MEDIUM: 0.6,
            DiscoveryConfidence.LOW: 0.4,
            DiscoveryConfidence.VERY_LOW: 0.2
        }
        return mapping.get(confidence, 0.5)

    async def _predict_missing_endpoints(self, existing_endpoints: List[SmartAPIEndpoint]) -> List[SmartAPIEndpoint]:
        """Use ML to predict likely missing endpoints"""

        predicted_endpoints = []

        # Analyze patterns in existing endpoints
        rest_apis = [ep for ep in existing_endpoints if ep.category == APICategory.REST_API]

        if len(rest_apis) >= 3:
            # Predict CRUD endpoints
            predicted_endpoints.extend(await self._predict_crud_endpoints(rest_apis))

            # Predict versioned endpoints
            predicted_endpoints.extend(await self._predict_versioned_endpoints(rest_apis))

        return predicted_endpoints

    async def _predict_crud_endpoints(self, rest_apis: List[SmartAPIEndpoint]) -> List[SmartAPIEndpoint]:
        """Predict missing CRUD endpoints"""

        predicted = []

        # Group by resource (extract resource from URL)
        resources = set()
        for api in rest_apis:
            resource = self._extract_resource_from_url(api.url)
            if resource:
                resources.add(resource)

        # For each resource, predict missing CRUD operations
        for resource in resources:
            base_url = self._extract_base_url_from_resource(rest_apis, resource)

            crud_operations = [
                ("GET", f"{base_url}/{resource}"),           # List
                ("POST", f"{base_url}/{resource}"),          # Create
                ("GET", f"{base_url}/{resource}/{{id}}"),    # Read
                ("PUT", f"{base_url}/{resource}/{{id}}"),    # Update
                ("DELETE", f"{base_url}/{resource}/{{id}}")  # Delete
            ]

            for method, url in crud_operations:
                if not any(ep.url == url and ep.method == method for ep in rest_apis):
                    predicted_endpoint = SmartAPIEndpoint(
                        url=url,
                        method=method,
                        category=APICategory.REST_API,
                        confidence=DiscoveryConfidence.MEDIUM,
                        discovery_method=DiscoveryMethod.AI_PREDICTION,
                        predicted_parameters=await self._predict_parameters(url, method),
                        authentication_predictions=await self._predict_authentication(url),
                        tags={"source": "crud_prediction", "resource": resource}
                    )
                    predicted.append(predicted_endpoint)

        return predicted

    def _extract_resource_from_url(self, url: str) -> Optional[str]:
        """Extract resource name from API URL"""
        # Simple extraction - find the last path segment that looks like a resource
        path = urlparse(url).path
        segments = [s for s in path.split('/') if s and not s.isdigit() and '{' not in s]

        # Common resource patterns
        if segments:
            last_segment = segments[-1]
            if last_segment in ['users', 'products', 'orders', 'items', 'accounts']:
                return last_segment

        return None

    def _extract_base_url_from_resource(self, apis: List[SmartAPIEndpoint], resource: str) -> str:
        """Extract base URL for a resource"""
        for api in apis:
            if resource in api.url:
                parts = api.url.split(resource)[0]
                return parts.rstrip('/')

        return "http://localhost/api/v1"  # Default fallback

    async def _predict_versioned_endpoints(self, rest_apis: List[SmartAPIEndpoint]) -> List[SmartAPIEndpoint]:
        """Predict endpoints in different API versions"""

        predicted = []

        # Find version patterns
        v1_apis = [api for api in rest_apis if '/v1/' in api.url]
        v2_apis = [api for api in rest_apis if '/v2/' in api.url]

        # If we have v1 but not v2, predict v2 endpoints
        if v1_apis and not v2_apis:
            for v1_api in v1_apis:
                v2_url = v1_api.url.replace('/v1/', '/v2/')

                predicted_endpoint = SmartAPIEndpoint(
                    url=v2_url,
                    method=v1_api.method,
                    category=v1_api.category,
                    confidence=DiscoveryConfidence.LOW,
                    discovery_method=DiscoveryMethod.AI_PREDICTION,
                    predicted_parameters=v1_api.predicted_parameters,
                    authentication_predictions=v1_api.authentication_predictions,
                    tags={"source": "version_prediction", "base_version": "v1"}
                )
                predicted.append(predicted_endpoint)

        return predicted

    async def _generate_discovery_insights(self, endpoints: List[SmartAPIEndpoint]):
        """Generate actionable insights from discovered APIs"""

        insights = []

        # Security insights
        unauth_endpoints = [ep for ep in endpoints if not ep.authentication_predictions]
        if unauth_endpoints:
            insights.append(DiscoveryInsight(
                insight_type="security",
                description=f"Found {len(unauth_endpoints)} endpoints without predicted authentication",
                confidence=0.8,
                related_endpoints=[ep.url for ep in unauth_endpoints[:5]],
                actionable_recommendation="Review these endpoints for security requirements",
                supporting_data={"count": len(unauth_endpoints)}
            ))

        # API versioning insights
        versioned_apis = defaultdict(list)
        for ep in endpoints:
            version_match = re.search(r'/v(\d+)/', ep.url)
            if version_match:
                versioned_apis[version_match.group(1)].append(ep)

        if len(versioned_apis) > 1:
            insights.append(DiscoveryInsight(
                insight_type="versioning",
                description=f"Multiple API versions detected: {list(versioned_apis.keys())}",
                confidence=0.9,
                related_endpoints=[],
                actionable_recommendation="Consider API version deprecation strategy",
                supporting_data={"versions": dict(versioned_apis)}
            ))

        # Coverage insights
        rest_endpoints = [ep for ep in endpoints if ep.category == APICategory.REST_API]
        crud_coverage = self._analyze_crud_coverage(rest_endpoints)

        if crud_coverage["incomplete_resources"]:
            insights.append(DiscoveryInsight(
                insight_type="coverage",
                description=f"Incomplete CRUD operations for {len(crud_coverage['incomplete_resources'])} resources",
                confidence=0.7,
                related_endpoints=[],
                actionable_recommendation="Consider implementing missing CRUD operations",
                supporting_data=crud_coverage
            ))

        self.discovery_insights.extend(insights)

    def _analyze_crud_coverage(self, rest_endpoints: List[SmartAPIEndpoint]) -> Dict[str, Any]:
        """Analyze CRUD operation coverage"""

        resources = defaultdict(set)

        for ep in rest_endpoints:
            resource = self._extract_resource_from_url(ep.url)
            if resource:
                resources[resource].add(ep.method)

        incomplete_resources = []
        for resource, methods in resources.items():
            expected_methods = {"GET", "POST", "PUT", "DELETE"}
            if not expected_methods.issubset(methods):
                missing = expected_methods - methods
                incomplete_resources.append({
                    "resource": resource,
                    "missing_methods": list(missing),
                    "available_methods": list(methods)
                })

        return {
            "total_resources": len(resources),
            "incomplete_resources": incomplete_resources,
            "coverage_percentage": (len(resources) - len(incomplete_resources)) / len(resources) * 100 if resources else 0
        }

    async def analyze_api_traffic(self, traffic_data: List[Dict[str, Any]]):
        """Analyze API traffic patterns for discovery insights"""

        # Add to traffic buffer
        self.traffic_buffer.extend(traffic_data)

        # Extract patterns
        for item in traffic_data:
            url = item.get("url", "")
            method = item.get("method", "GET")
            response_time = item.get("response_time", 0)

            # Store behavioral patterns
            pattern_key = self._extract_url_pattern(url)
            self.behavior_patterns[pattern_key].append({
                "method": method,
                "response_time": response_time,
                "timestamp": item.get("timestamp", datetime.utcnow())
            })

    async def _enhance_with_advanced_ml(self, endpoints: List[SmartAPIEndpoint]) -> List[SmartAPIEndpoint]:
        """Enhance endpoints with advanced ML analysis"""
        if not self.advanced_ml_engine:
            return endpoints

        logging.info("🧠 Enhancing endpoints with advanced ML analysis")

        enhanced_endpoints = []

        for endpoint in endpoints:
            try:
                # Prepare data for ML analysis
                api_data = {
                    'url': endpoint.url,
                    'method': endpoint.method,
                    'category': endpoint.category.value,
                    'response_time': np.mean(endpoint.response_time_patterns) if endpoint.response_time_patterns else 100,
                    'status_code': 200,  # Default
                    'payload_size': 1024,  # Default
                    'headers': {},
                    'auth_required': bool(endpoint.authentication_predictions),
                    'rate_limited': endpoint.rate_limiting_predictions is not None,
                    'traffic_volume': endpoint.traffic_volume
                }

                # Run comprehensive ML analysis
                ml_predictions = await self.advanced_ml_engine.comprehensive_analysis(api_data)

                # Enhance endpoint with ML insights
                enhanced_endpoint = await self._apply_ml_enhancements(endpoint, ml_predictions)
                enhanced_endpoints.append(enhanced_endpoint)

            except Exception as e:
                logging.warning(f"ML enhancement failed for {endpoint.url}: {e}")
                enhanced_endpoints.append(endpoint)

        return enhanced_endpoints

    async def _apply_ml_enhancements(self, endpoint: SmartAPIEndpoint, ml_predictions: Dict[str, Any]) -> SmartAPIEndpoint:
        """Apply ML predictions to enhance endpoint information"""

        # Update confidence based on pattern recognition
        if 'pattern_recognition' in ml_predictions:
            pattern_pred = ml_predictions['pattern_recognition']
            if hasattr(pattern_pred, 'confidence') and pattern_pred.confidence > 0.8:
                # Boost confidence for high-confidence pattern matches
                current_confidence = self._confidence_to_float(endpoint.confidence)
                new_confidence = min(1.0, current_confidence + 0.1)
                endpoint.confidence = self._float_to_confidence(new_confidence)

        # Update security predictions
        if 'security_analysis' in ml_predictions:
            security_pred = ml_predictions['security_analysis']
            if hasattr(security_pred, 'prediction') and isinstance(security_pred.prediction, dict):
                endpoint.tags.add(f"security_risk_{security_pred.prediction.get('risk_level', 'unknown')}")

                # Add security recommendations to tags
                recommendations = security_pred.prediction.get('recommendations', [])
                for rec in recommendations[:2]:  # Limit to first 2 recommendations
                    endpoint.tags.add(f"rec_{rec.replace(' ', '_')[:20]}")

        # Update behavior predictions
        if 'behavior_prediction' in ml_predictions:
            behavior_pred = ml_predictions['behavior_prediction']
            if hasattr(behavior_pred, 'prediction') and isinstance(behavior_pred.prediction, (int, float)):
                endpoint.predicted_response_schema = {
                    "predicted_response_time": float(behavior_pred.prediction),
                    "confidence": behavior_pred.confidence
                }

        # Add ML analysis metadata
        endpoint.tags.add("ml_enhanced")

        return endpoint

    def _float_to_confidence(self, value: float) -> DiscoveryConfidence:
        """Convert float to confidence enum"""
        if value >= 0.9:
            return DiscoveryConfidence.VERY_HIGH
        elif value >= 0.7:
            return DiscoveryConfidence.HIGH
        elif value >= 0.5:
            return DiscoveryConfidence.MEDIUM
        elif value >= 0.3:
            return DiscoveryConfidence.LOW
        else:
            return DiscoveryConfidence.VERY_LOW

    async def analyze_api_traffic_with_ml(self, traffic_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze API traffic using advanced ML models"""
        if not HAS_ADVANCED_ML or not self.advanced_ml_engine:
            logging.warning("Advanced ML not available for traffic analysis")
            return {"error": "Advanced ML models not available"}

        # Detect anomalies
        anomalies = await self.advanced_ml_engine.detect_api_anomalies(traffic_data)

        # Analyze patterns
        pattern_analysis = await self._analyze_traffic_patterns_ml(traffic_data)

        # Generate insights
        ml_insights = await self._generate_ml_insights(anomalies, pattern_analysis)

        return {
            "anomalies_detected": len(anomalies),
            "anomalies": [{
                "prediction": anom.prediction,
                "confidence": anom.confidence,
                "explanation": anom.explanation
            } for anom in anomalies],
            "pattern_analysis": pattern_analysis,
            "ml_insights": ml_insights,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

    async def _analyze_traffic_patterns_ml(self, traffic_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze traffic patterns using ML"""
        patterns = {
            "peak_hours": [],
            "common_endpoints": [],
            "response_time_trends": {},
            "error_patterns": {}
        }

        if not traffic_data:
            return patterns

        # Analyze peak hours
        hour_counts = defaultdict(int)
        for item in traffic_data:
            timestamp = item.get('timestamp', datetime.utcnow())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour_counts[timestamp.hour] += 1

        # Find peak hours (top 25%)
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        peak_count = max(1, len(sorted_hours) // 4)
        patterns["peak_hours"] = [hour for hour, count in sorted_hours[:peak_count]]

        # Analyze common endpoints
        endpoint_counts = defaultdict(int)
        for item in traffic_data:
            url = item.get('url', '')
            endpoint_counts[url] += 1

        patterns["common_endpoints"] = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return patterns

    async def _generate_ml_insights(self, anomalies: List[Any], pattern_analysis: Dict[str, Any]) -> List[str]:
        """Generate insights from ML analysis"""
        insights = []

        # Anomaly insights
        if anomalies:
            high_confidence_anomalies = [a for a in anomalies if hasattr(a, 'confidence') and a.confidence > 0.8]
            if high_confidence_anomalies:
                insights.append(f"Detected {len(high_confidence_anomalies)} high-confidence anomalies requiring attention")

        # Pattern insights
        if pattern_analysis.get("peak_hours"):
            peak_hours = pattern_analysis["peak_hours"]
            insights.append(f"Peak traffic hours identified: {peak_hours}")

        if pattern_analysis.get("common_endpoints"):
            top_endpoint = pattern_analysis["common_endpoints"][0]
            insights.append(f"Most accessed endpoint: {top_endpoint[0]} ({top_endpoint[1]} requests)")

        if not insights:
            insights.append("No significant patterns or anomalies detected")

        return insights

    async def continuous_learning_update(self, feedback_data: List[Dict[str, Any]]):
        """Update ML models with new feedback data for continuous learning"""
        if not HAS_ADVANCED_ML or not self.advanced_ml_engine:
            return

        logging.info("🔄 Updating ML models with new feedback data")

        # Categorize feedback data
        pattern_data = []
        security_data = []
        behavior_data = []

        for item in feedback_data:
            data_type = item.get('type', 'pattern')
            if data_type == 'pattern':
                pattern_data.append(item)
            elif data_type == 'security':
                security_data.append(item)
            elif data_type == 'behavior':
                behavior_data.append(item)

        # Update training data
        if pattern_data:
            await self.advanced_ml_engine.update_training_data('patterns', pattern_data)

        if security_data:
            await self.advanced_ml_engine.update_training_data('security', security_data)

        if behavior_data:
            await self.advanced_ml_engine.update_training_data('behaviors', behavior_data)

        logging.info("✅ ML models updated with continuous learning data")

    def get_ml_model_status(self) -> Dict[str, Any]:
        """Get status of ML models"""
        if not HAS_ADVANCED_ML or not self.advanced_ml_engine:
            return {
                "advanced_ml_available": False,
                "message": "Advanced ML models not available"
            }

        return {
            "advanced_ml_available": True,
            **self.advanced_ml_engine.get_model_status()
        }

    def get_discovery_summary(self) -> Dict[str, Any]:
        """Get comprehensive discovery summary"""

        endpoints_by_category = defaultdict(int)
        endpoints_by_confidence = defaultdict(int)
        endpoints_by_method = defaultdict(int)

        for endpoint in self.discovered_endpoints.values():
            endpoints_by_category[endpoint.category.value] += 1
            endpoints_by_confidence[endpoint.confidence.value] += 1
            endpoints_by_method[endpoint.discovery_method.value] += 1

        return {
            "total_endpoints": len(self.discovered_endpoints),
            "categories": dict(endpoints_by_category),
            "confidence_distribution": dict(endpoints_by_confidence),
            "discovery_methods": dict(endpoints_by_method),
            "clusters": len(self.api_clusters),
            "insights": len(self.discovery_insights),
            "high_confidence_endpoints": len([
                ep for ep in self.discovered_endpoints.values()
                if ep.confidence in [DiscoveryConfidence.HIGH, DiscoveryConfidence.VERY_HIGH]
            ]),
            "ml_enhanced_endpoints": len([
                ep for ep in self.discovered_endpoints.values()
                if "ml_enhanced" in ep.tags
            ]),
            "advanced_ml_available": HAS_ADVANCED_ML,
            "ml_model_status": self.get_ml_model_status() if HAS_ADVANCED_ML else None,
            "last_discovery": max(
                (ep.discovered_at for ep in self.discovered_endpoints.values()),
                default=None
            )
        }

# Global smart discovery instance
smart_api_discovery = SmartAPIDiscovery()

# Utility functions
async def initialize_smart_discovery():
    """Initialize the smart API discovery system"""
    await smart_api_discovery.initialize()
    logging.info("🧠 Smart API Discovery system ready")

async def discover_apis_smart(target: str = None, **kwargs) -> List[SmartAPIEndpoint]:
    """Convenient function to run smart API discovery"""
    return await smart_api_discovery.discover_apis_with_ml(target, **kwargs)

async def analyze_traffic_with_ml(traffic_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze API traffic using advanced ML models"""
    return await smart_api_discovery.analyze_api_traffic_with_ml(traffic_data)

async def update_ml_models(feedback_data: List[Dict[str, Any]]):
    """Update ML models with continuous learning data"""
    await smart_api_discovery.continuous_learning_update(feedback_data)

def get_discovery_ml_status() -> Dict[str, Any]:
    """Get ML model status for discovery system"""
    return smart_api_discovery.get_ml_model_status()