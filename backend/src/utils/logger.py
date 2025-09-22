"""
Structured Logging Configuration for API Orchestrator
Provides JSON-formatted logs for production monitoring and debugging
"""

import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler
import traceback


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "service": "api-orchestrator",
            "environment": self._get_environment(),
        }

        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
        if hasattr(record, "project_id"):
            log_obj["project_id"] = record.project_id
        if hasattr(record, "task_id"):
            log_obj["task_id"] = record.task_id
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "ip_address"):
            log_obj["ip_address"] = record.ip_address

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_obj)

    @staticmethod
    def _get_environment() -> str:
        """Get environment name from config or default to development"""
        import os

        return os.getenv("ENVIRONMENT", "development")


class SecurityLogger:
    """Specialized logger for security events"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_auth_attempt(
        self, email: str, success: bool, ip: str, reason: Optional[str] = None
    ):
        """Log authentication attempt"""
        extra = {
            "email": email,
            "success": success,
            "ip_address": ip,
            "event_type": "auth_attempt",
        }
        if reason:
            extra["reason"] = reason

        if success:
            self.logger.info(f"Successful authentication for {email}", extra=extra)
        else:
            self.logger.warning(
                f"Failed authentication for {email}: {reason}", extra=extra
            )

    def log_permission_denied(self, user_id: int, resource: str, action: str):
        """Log permission denied events"""
        self.logger.warning(
            f"Permission denied for user {user_id} to {action} {resource}",
            extra={
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "event_type": "permission_denied",
            },
        )

    def log_suspicious_activity(self, description: str, **kwargs):
        """Log suspicious activity"""
        extra = {"event_type": "suspicious_activity"}
        extra.update(kwargs)
        self.logger.warning(f"Suspicious activity detected: {description}", extra=extra)


class PerformanceLogger:
    """Specialized logger for performance metrics"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_api_call(
        self, endpoint: str, method: str, duration_ms: float, status_code: int
    ):
        """Log API call performance"""
        self.logger.info(
            f"{method} {endpoint} completed in {duration_ms}ms with status {status_code}",
            extra={
                "endpoint": endpoint,
                "method": method,
                "duration_ms": duration_ms,
                "status_code": status_code,
                "event_type": "api_call",
            },
        )

    def log_agent_performance(self, agent_type: str, duration_ms: float, success: bool):
        """Log agent execution performance"""
        self.logger.info(
            f"Agent {agent_type} completed in {duration_ms}ms",
            extra={
                "agent_type": agent_type,
                "duration_ms": duration_ms,
                "success": success,
                "event_type": "agent_performance",
            },
        )


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = True,
    console_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Configure structured logging for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if None, logs to stdout only)
        json_format: Whether to use JSON formatting
        console_output: Whether to output to console
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance
    """

    # Create logger
    logger = logging.getLogger("api_orchestrator")
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.handlers.clear()  # Clear existing handlers

    # Choose formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Add separate error log file
        error_log_file = log_path.parent / f"{log_path.stem}_errors{log_path.suffix}"
        error_handler = RotatingFileHandler(
            filename=str(error_log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

    # Create specialized loggers
    security_logger = SecurityLogger(logger)
    performance_logger = PerformanceLogger(logger)

    # Store specialized loggers as attributes
    logger.security = security_logger
    logger.performance = performance_logger

    return logger


# Create default logger instance
import os

logger = setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", "logs/api_orchestrator.log")
    if os.getenv("ENVIRONMENT") != "development"
    else None,
    json_format=os.getenv("ENVIRONMENT", "development") != "development",
    console_output=True,
)


# Convenience functions
def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance"""
    return logging.getLogger(f"api_orchestrator.{name}")


def log_request(request: Any) -> Dict[str, Any]:
    """Extract request metadata for logging"""
    return {
        "request_id": getattr(request, "request_id", None),
        "ip_address": getattr(request.client, "host", None)
        if hasattr(request, "client")
        else None,
        "user_agent": request.headers.get("user-agent", "unknown")
        if hasattr(request, "headers")
        else None,
        "method": request.method if hasattr(request, "method") else None,
        "path": str(request.url.path) if hasattr(request, "url") else None,
    }
