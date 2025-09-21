"""
Distributed Tracing and Observability System for API Orchestrator
OpenTelemetry-based tracing with Jaeger, Zipkin, and custom observability
"""

from typing import Optional, Dict, Any, List, Set, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import uuid
import time
import logging
from contextlib import asynccontextmanager
import contextvars
from collections import defaultdict, deque
import threading

# Optional imports with graceful fallbacks
try:
    from opentelemetry import trace, metrics, baggage
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.exporter.zipkin.json import ZipkinExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.propagators.b3 import B3MultiFormat
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False

try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    structlog = None
    HAS_STRUCTLOG = False

from src.config import settings

class TraceLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"

class SpanType(str, Enum):
    HTTP_REQUEST = "http.request"
    DATABASE_QUERY = "db.query"
    CACHE_OPERATION = "cache.operation"
    EXTERNAL_API = "external.api"
    BUSINESS_LOGIC = "business.logic"
    BACKGROUND_TASK = "background.task"
    MESSAGE_QUEUE = "message.queue"
    AI_OPERATION = "ai.operation"

@dataclass
class TraceContext:
    """Trace context information"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)
    service_name: str = "api-orchestrator"
    operation_name: str = ""
    start_time: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Span:
    """Custom span implementation for when OpenTelemetry is not available"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "ok"
    error: Optional[str] = None

@dataclass
class ServiceMetrics:
    """Service-level metrics for observability"""
    service_name: str
    request_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0
    p50_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    error_rate: float = 0.0
    throughput_rps: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

@dataclass
class DependencyMap:
    """Service dependency mapping"""
    service_name: str
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    call_count: Dict[str, int] = field(default_factory=dict)
    error_count: Dict[str, int] = field(default_factory=dict)

class DistributedTracer:
    """Distributed tracing implementation with OpenTelemetry integration"""

    def __init__(self, service_name: str = "api-orchestrator"):
        self.service_name = service_name
        self.trace_provider = None
        self.tracer = None
        self.meter_provider = None
        self.meter = None

        # Fallback tracking when OpenTelemetry is not available
        self.active_spans: Dict[str, Span] = {}
        self.completed_spans: deque = deque(maxlen=10000)
        self.span_lock = threading.Lock()

        # Context variables for async trace propagation
        self.current_trace_context: contextvars.ContextVar[Optional[TraceContext]] = \
            contextvars.ContextVar('current_trace_context', default=None)

        # Metrics collection
        self.service_metrics: Dict[str, ServiceMetrics] = {}
        self.dependency_map: Dict[str, DependencyMap] = {}

        self.initialized = False

    async def initialize(self,
                        jaeger_endpoint: Optional[str] = None,
                        zipkin_endpoint: Optional[str] = None,
                        enable_console_export: bool = True):
        """Initialize distributed tracing with various backends"""

        if HAS_OTEL:
            await self._initialize_opentelemetry(
                jaeger_endpoint, zipkin_endpoint, enable_console_export
            )
        else:
            logging.warning("OpenTelemetry not available, using fallback tracing")

        self.initialized = True
        logging.info(f"🔍 Distributed tracing initialized for service: {self.service_name}")

    async def _initialize_opentelemetry(self,
                                      jaeger_endpoint: Optional[str],
                                      zipkin_endpoint: Optional[str],
                                      enable_console_export: bool):
        """Initialize OpenTelemetry with multiple exporters"""

        # Set up trace provider
        self.trace_provider = TracerProvider()
        trace.set_tracer_provider(self.trace_provider)

        # Add exporters
        if jaeger_endpoint:
            jaeger_exporter = JaegerExporter(
                agent_host_name=jaeger_endpoint.split(':')[0],
                agent_port=int(jaeger_endpoint.split(':')[1]) if ':' in jaeger_endpoint else 14268,
            )
            self.trace_provider.add_span_processor(
                BatchSpanProcessor(jaeger_exporter)
            )

        if zipkin_endpoint:
            zipkin_exporter = ZipkinExporter(endpoint=zipkin_endpoint)
            self.trace_provider.add_span_processor(
                BatchSpanProcessor(zipkin_exporter)
            )

        if enable_console_export:
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            console_exporter = ConsoleSpanExporter()
            self.trace_provider.add_span_processor(
                BatchSpanProcessor(console_exporter)
            )

        # Set up propagation
        set_global_textmap(B3MultiFormat())

        # Get tracer
        self.tracer = trace.get_tracer(__name__)

        # Auto-instrument popular frameworks
        FastAPIInstrumentor.instrument()
        RequestsInstrumentor.instrument()
        SQLAlchemyInstrumentor.instrument()

        # Set up metrics
        self.meter_provider = MeterProvider()
        metrics.set_meter_provider(self.meter_provider)
        self.meter = metrics.get_meter(__name__)

    @asynccontextmanager
    async def trace_span(self,
                        operation_name: str,
                        span_type: SpanType = SpanType.BUSINESS_LOGIC,
                        tags: Optional[Dict[str, Any]] = None,
                        parent_context: Optional[TraceContext] = None):
        """Create a traced span with automatic timing and error handling"""

        # Generate trace context
        trace_context = await self._create_trace_context(
            operation_name, parent_context, tags
        )

        if HAS_OTEL and self.tracer:
            # Use OpenTelemetry span
            with self.tracer.start_as_current_span(operation_name) as otel_span:
                # Set tags
                if tags:
                    for key, value in tags.items():
                        otel_span.set_attribute(key, value)

                otel_span.set_attribute("span.type", span_type.value)
                otel_span.set_attribute("service.name", self.service_name)

                # Set context variable
                token = self.current_trace_context.set(trace_context)

                try:
                    yield trace_context
                    otel_span.set_status(Status(StatusCode.OK))
                except Exception as e:
                    otel_span.set_status(Status(StatusCode.ERROR, str(e)))
                    otel_span.record_exception(e)
                    raise
                finally:
                    self.current_trace_context.reset(token)
        else:
            # Use fallback span tracking
            span = await self._create_fallback_span(trace_context, span_type)

            try:
                token = self.current_trace_context.set(trace_context)
                yield trace_context
                await self._complete_fallback_span(span, "ok")
            except Exception as e:
                await self._complete_fallback_span(span, "error", str(e))
                raise
            finally:
                self.current_trace_context.reset(token)

    async def _create_trace_context(self,
                                  operation_name: str,
                                  parent_context: Optional[TraceContext],
                                  tags: Optional[Dict[str, Any]]) -> TraceContext:
        """Create trace context for a new span"""

        # Get current context or create new one
        current_context = self.current_trace_context.get()

        if parent_context:
            trace_id = parent_context.trace_id
            parent_span_id = parent_context.span_id
        elif current_context:
            trace_id = current_context.trace_id
            parent_span_id = current_context.span_id
        else:
            trace_id = str(uuid.uuid4())
            parent_span_id = None

        return TraceContext(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=parent_span_id,
            service_name=self.service_name,
            operation_name=operation_name,
            tags=tags or {}
        )

    async def _create_fallback_span(self, trace_context: TraceContext, span_type: SpanType) -> Span:
        """Create fallback span when OpenTelemetry is not available"""

        span = Span(
            trace_id=trace_context.trace_id,
            span_id=trace_context.span_id,
            parent_span_id=trace_context.parent_span_id,
            operation_name=trace_context.operation_name,
            service_name=trace_context.service_name,
            start_time=trace_context.start_time,
            tags=trace_context.tags.copy()
        )

        span.tags["span.type"] = span_type.value

        with self.span_lock:
            self.active_spans[span.span_id] = span

        return span

    async def _complete_fallback_span(self, span: Span, status: str, error: Optional[str] = None):
        """Complete a fallback span"""

        span.end_time = datetime.utcnow()
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
        span.status = status
        span.error = error

        with self.span_lock:
            if span.span_id in self.active_spans:
                del self.active_spans[span.span_id]
            self.completed_spans.append(span)

        # Update metrics
        await self._update_service_metrics(span)

    async def _update_service_metrics(self, span: Span):
        """Update service-level metrics from completed span"""

        service_name = span.service_name

        if service_name not in self.service_metrics:
            self.service_metrics[service_name] = ServiceMetrics(service_name=service_name)

        metrics = self.service_metrics[service_name]
        metrics.request_count += 1

        if span.status == "error":
            metrics.error_count += 1

        if span.duration_ms:
            metrics.total_duration_ms += span.duration_ms

        # Calculate rolling averages (simplified)
        metrics.error_rate = metrics.error_count / metrics.request_count
        metrics.throughput_rps = metrics.request_count / 60  # Approximate RPS

        metrics.last_updated = datetime.utcnow()

    def add_span_tag(self, key: str, value: Any):
        """Add tag to current span"""
        context = self.current_trace_context.get()
        if context:
            context.tags[key] = value

    def add_span_log(self, message: str, level: TraceLevel = TraceLevel.INFO, **kwargs):
        """Add log entry to current span"""
        context = self.current_trace_context.get()
        if context and not HAS_OTEL:
            # For fallback spans, add to logs
            span_id = context.span_id
            if span_id in self.active_spans:
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": level.value,
                    "message": message,
                    **kwargs
                }
                self.active_spans[span_id].logs.append(log_entry)

    def get_current_trace_id(self) -> Optional[str]:
        """Get current trace ID"""
        context = self.current_trace_context.get()
        return context.trace_id if context else None

    def get_current_span_id(self) -> Optional[str]:
        """Get current span ID"""
        context = self.current_trace_context.get()
        return context.span_id if context else None

    async def inject_trace_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject trace context into HTTP headers"""
        context = self.current_trace_context.get()
        if context:
            headers["X-Trace-Id"] = context.trace_id
            headers["X-Span-Id"] = context.span_id
            if context.parent_span_id:
                headers["X-Parent-Span-Id"] = context.parent_span_id

        return headers

    async def extract_trace_headers(self, headers: Dict[str, str]) -> Optional[TraceContext]:
        """Extract trace context from HTTP headers"""
        trace_id = headers.get("X-Trace-Id")
        span_id = headers.get("X-Span-Id")
        parent_span_id = headers.get("X-Parent-Span-Id")

        if trace_id and span_id:
            return TraceContext(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                service_name=self.service_name
            )

        return None

    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get summary for a specific trace"""
        spans = [span for span in self.completed_spans if span.trace_id == trace_id]

        if not spans:
            return {"error": "Trace not found"}

        total_duration = sum(span.duration_ms or 0 for span in spans)
        error_count = sum(1 for span in spans if span.status == "error")

        return {
            "trace_id": trace_id,
            "total_spans": len(spans),
            "total_duration_ms": total_duration,
            "error_count": error_count,
            "success_rate": (len(spans) - error_count) / len(spans) if spans else 0,
            "services": list(set(span.service_name for span in spans)),
            "operations": list(set(span.operation_name for span in spans)),
            "spans": [
                {
                    "span_id": span.span_id,
                    "operation_name": span.operation_name,
                    "service_name": span.service_name,
                    "duration_ms": span.duration_ms,
                    "status": span.status,
                    "start_time": span.start_time.isoformat(),
                    "tags": span.tags
                }
                for span in spans
            ]
        }

class ObservabilityManager:
    """Comprehensive observability management"""

    def __init__(self, service_name: str = "api-orchestrator"):
        self.service_name = service_name
        self.tracer = DistributedTracer(service_name)
        self.metrics_store = defaultdict(list)
        self.health_checks = {}
        self.sli_metrics = {}  # Service Level Indicators
        self.error_budget = 99.9  # 99.9% availability target

        # Structured logging
        if HAS_STRUCTLOG:
            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.JSONRenderer()
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )

    async def initialize(self, **tracer_config):
        """Initialize observability system"""
        await self.tracer.initialize(**tracer_config)
        logging.info("🔭 Observability system initialized")

    @asynccontextmanager
    async def trace_operation(self,
                            operation_name: str,
                            span_type: SpanType = SpanType.BUSINESS_LOGIC,
                            **kwargs):
        """Trace an operation with observability features"""
        async with self.tracer.trace_span(operation_name, span_type, **kwargs) as context:
            yield context

    def record_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a custom metric"""
        metric_entry = {
            "name": metric_name,
            "value": value,
            "timestamp": datetime.utcnow(),
            "tags": tags or {}
        }
        self.metrics_store[metric_name].append(metric_entry)

        # Keep only last 1000 entries per metric
        if len(self.metrics_store[metric_name]) > 1000:
            self.metrics_store[metric_name] = self.metrics_store[metric_name][-1000:]

    def add_health_check(self, name: str, check_func: Callable):
        """Add a health check function"""
        self.health_checks[name] = check_func

    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}

        for name, check_func in self.health_checks.items():
            try:
                start_time = time.time()
                result = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
                duration = (time.time() - start_time) * 1000

                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "response_time_ms": duration,
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }

        overall_status = "healthy" if all(
            r["status"] == "healthy" for r in results.values()
        ) else "unhealthy"

        return {
            "overall_status": overall_status,
            "checks": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    def calculate_sli_metrics(self) -> Dict[str, float]:
        """Calculate Service Level Indicators"""
        if not self.tracer.service_metrics:
            return {}

        sli_metrics = {}

        for service_name, metrics in self.tracer.service_metrics.items():
            # Availability (success rate)
            availability = (1 - metrics.error_rate) * 100

            # Latency (P95 response time)
            latency_sli = min(100, max(0, 100 - (metrics.p95_latency / 1000) * 10))

            # Throughput score
            throughput_sli = min(100, metrics.throughput_rps * 2)

            sli_metrics[f"{service_name}_availability"] = availability
            sli_metrics[f"{service_name}_latency"] = latency_sli
            sli_metrics[f"{service_name}_throughput"] = throughput_sli

        return sli_metrics

    def get_observability_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive observability dashboard data"""
        return {
            "service_name": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "tracing": {
                "active_spans": len(self.tracer.active_spans),
                "completed_spans": len(self.tracer.completed_spans),
                "current_trace_id": self.tracer.get_current_trace_id()
            },
            "metrics": {
                "service_metrics": {
                    name: {
                        "request_count": m.request_count,
                        "error_rate": m.error_rate,
                        "throughput_rps": m.throughput_rps,
                        "p95_latency": m.p95_latency
                    }
                    for name, m in self.tracer.service_metrics.items()
                },
                "custom_metrics_count": len(self.metrics_store)
            },
            "sli_metrics": self.calculate_sli_metrics(),
            "error_budget_remaining": max(0, self.error_budget - sum(
                m.error_rate for m in self.tracer.service_metrics.values()
            ))
        }

# Global observability instance
observability = ObservabilityManager()

# Decorators for easy integration
def trace(operation_name: str, span_type: SpanType = SpanType.BUSINESS_LOGIC):
    """Decorator to trace function calls"""
    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            async with observability.trace_operation(operation_name, span_type):
                return await func(*args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            # For sync functions, create a simple span
            span_id = str(uuid.uuid4())
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                observability.record_metric(f"{operation_name}_duration_ms", duration)
                return result
            except Exception as e:
                observability.record_metric(f"{operation_name}_errors", 1)
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Utility functions
async def initialize_observability(**config):
    """Initialize the observability system"""
    await observability.initialize(**config)

def get_trace_id() -> Optional[str]:
    """Get current trace ID"""
    return observability.tracer.get_current_trace_id()

def add_trace_tag(key: str, value: Any):
    """Add tag to current trace"""
    observability.tracer.add_span_tag(key, value)

def record_metric(name: str, value: float, **tags):
    """Record a metric value"""
    observability.record_metric(name, value, tags)

# FastAPI middleware for automatic tracing
class TracingMiddleware:
    """FastAPI middleware for automatic request tracing"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_method = scope["method"]
        request_path = scope["path"]
        operation_name = f"{request_method} {request_path}"

        # Extract trace context from headers
        headers = dict(scope.get("headers", []))
        trace_context = await observability.tracer.extract_trace_headers({
            k.decode(): v.decode() for k, v in headers.items()
        })

        async with observability.trace_operation(
            operation_name,
            SpanType.HTTP_REQUEST,
            tags={
                "http.method": request_method,
                "http.path": request_path,
                "http.scheme": scope.get("scheme", "http")
            },
            parent_context=trace_context
        ):
            await self.app(scope, receive, send)