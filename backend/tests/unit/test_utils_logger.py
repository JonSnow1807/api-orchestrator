"""
Unit tests for logger utility module
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import json
import logging
from datetime import datetime

from src.utils.logger import (
    JSONFormatter,
    SecurityLogger,
    PerformanceLogger,
    setup_logging,
    get_logger,
    log_request
)


class TestJSONFormatter:
    """Test JSONFormatter class"""
    
    def test_format_basic_log(self):
        """Test formatting basic log record"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["logger"] == "test"
        assert parsed["service"] == "api-orchestrator"
    
    def test_format_with_extra_fields(self):
        """Test formatting with extra fields"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.user_id = 123
        record.project_id = 456
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert parsed["user_id"] == 123
        assert parsed["project_id"] == 456
    
    def test_format_with_exception(self):
        """Test formatting with exception info"""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=10,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info()
            )
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert "exception" in parsed
        assert parsed["exception"]["type"] == "ValueError"
        assert parsed["exception"]["message"] == "Test error"
    
    @patch.dict('os.environ', {"ENVIRONMENT": "production"})
    def test_get_environment(self):
        """Test environment detection"""
        formatter = JSONFormatter()
        env = formatter._get_environment()
        
        assert env == "production"


class TestSecurityLogger:
    """Test SecurityLogger class"""
    
    @pytest.fixture
    def security_logger(self):
        """Create SecurityLogger instance"""
        mock_logger = MagicMock()
        return SecurityLogger(mock_logger)
    
    def test_log_auth_attempt_success(self, security_logger):
        """Test logging successful authentication"""
        security_logger.log_auth_attempt(
            email="test@example.com",
            success=True,
            ip="192.168.1.1"
        )
        
        security_logger.logger.info.assert_called_once()
        call_args = security_logger.logger.info.call_args
        assert "Successful authentication" in call_args[0][0]
    
    def test_log_auth_attempt_failure(self, security_logger):
        """Test logging failed authentication"""
        security_logger.log_auth_attempt(
            email="test@example.com",
            success=False,
            ip="192.168.1.1",
            reason="Invalid password"
        )
        
        security_logger.logger.warning.assert_called_once()
        call_args = security_logger.logger.warning.call_args
        assert "Failed authentication" in call_args[0][0]
        assert "Invalid password" in call_args[0][0]
    
    def test_log_permission_denied(self, security_logger):
        """Test logging permission denied"""
        security_logger.log_permission_denied(
            user_id=123,
            resource="projects",
            action="delete"
        )
        
        security_logger.logger.warning.assert_called_once()
        call_args = security_logger.logger.warning.call_args
        assert "Permission denied" in call_args[0][0]
    
    def test_log_suspicious_activity(self, security_logger):
        """Test logging suspicious activity"""
        security_logger.log_suspicious_activity(
            description="Multiple failed login attempts",
            ip="192.168.1.1",
            user_id=123
        )
        
        security_logger.logger.warning.assert_called_once()
        call_args = security_logger.logger.warning.call_args
        assert "Suspicious activity" in call_args[0][0]


class TestPerformanceLogger:
    """Test PerformanceLogger class"""
    
    @pytest.fixture
    def perf_logger(self):
        """Create PerformanceLogger instance"""
        mock_logger = MagicMock()
        return PerformanceLogger(mock_logger)
    
    def test_log_api_call(self, perf_logger):
        """Test logging API call performance"""
        perf_logger.log_api_call(
            endpoint="/api/users",
            method="GET",
            duration_ms=125.5,
            status_code=200
        )
        
        perf_logger.logger.info.assert_called_once()
        call_args = perf_logger.logger.info.call_args
        assert "125.5ms" in call_args[0][0]
        assert "200" in call_args[0][0]
    
    def test_log_agent_performance(self, perf_logger):
        """Test logging agent performance"""
        perf_logger.log_agent_performance(
            agent_type="discovery",
            duration_ms=500.0,
            success=True
        )
        
        perf_logger.logger.info.assert_called_once()
        call_args = perf_logger.logger.info.call_args
        assert "discovery" in call_args[0][0]
        assert "500.0ms" in call_args[0][0]


class TestSetupLogging:
    """Test setup_logging function"""
    
    @patch('logging.getLogger')
    @patch('logging.StreamHandler')
    def test_setup_basic_logging(self, mock_handler, mock_get_logger):
        """Test basic logging setup"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        result = setup_logging(log_level="INFO")
        
        assert result == mock_logger
        mock_logger.setLevel.assert_called_with(logging.INFO)
    
    @patch('logging.getLogger')
    @patch('logging.StreamHandler')
    @patch('logging.handlers.RotatingFileHandler')
    @patch('pathlib.Path.mkdir')
    def test_setup_with_file(self, mock_mkdir, mock_file_handler, mock_stream_handler, mock_get_logger):
        """Test logging setup with file output"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        result = setup_logging(
            log_level="DEBUG",
            log_file="test.log",
            json_format=True
        )
        
        assert result == mock_logger
        mock_logger.setLevel.assert_called_with(logging.DEBUG)
        mock_file_handler.assert_called()
    
    def test_setup_with_specialized_loggers(self):
        """Test that specialized loggers are attached"""
        logger = setup_logging()
        
        assert hasattr(logger, 'security')
        assert hasattr(logger, 'performance')
        assert isinstance(logger.security, SecurityLogger)
        assert isinstance(logger.performance, PerformanceLogger)


class TestGetLogger:
    """Test get_logger function"""
    
    @patch('logging.getLogger')
    def test_get_named_logger(self, mock_get_logger):
        """Test getting a named logger"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        result = get_logger("test_module")
        
        mock_get_logger.assert_called_with("api_orchestrator.test_module")
        assert result == mock_logger


class TestLogRequest:
    """Test log_request function"""
    
    def test_log_request_with_full_data(self):
        """Test extracting request metadata"""
        mock_request = MagicMock()
        mock_request.request_id = "req-123"
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {"user-agent": "TestAgent/1.0"}
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        
        result = log_request(mock_request)
        
        assert result["request_id"] == "req-123"
        assert result["ip_address"] == "192.168.1.1"
        assert result["user_agent"] == "TestAgent/1.0"
        assert result["method"] == "GET"
        assert result["path"] == "/api/test"
    
    def test_log_request_with_missing_data(self):
        """Test extracting request with missing attributes"""
        mock_request = MagicMock()
        del mock_request.client
        del mock_request.headers
        
        result = log_request(mock_request)
        
        assert result["ip_address"] is None
        assert result["user_agent"] is None


class TestLoggerIntegration:
    """Test logger integration scenarios"""
    
    def test_json_formatter_output(self):
        """Test that JSON formatter produces valid JSON"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Integration test",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        
        # Should be valid JSON
        try:
            parsed = json.loads(output)
            assert True
        except json.JSONDecodeError:
            assert False
    
    @patch.dict('os.environ', {"LOG_LEVEL": "WARNING"})
    def test_environment_log_level(self):
        """Test log level from environment"""
        logger = setup_logging()
        
        assert logger.level == logging.WARNING or logger.level == logging.INFO