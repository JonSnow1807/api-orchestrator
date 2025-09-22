"""
Security Configuration Management
Centralized security settings and environment validation
"""

import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class SecuritySettings:
    """Centralized security configuration"""

    # Authentication settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    # Password policy
    MIN_PASSWORD_LENGTH: int = int(os.getenv("MIN_PASSWORD_LENGTH", "12"))
    REQUIRE_PASSWORD_COMPLEXITY: bool = os.getenv("REQUIRE_PASSWORD_COMPLEXITY", "true").lower() == "true"
    PASSWORD_HISTORY_COUNT: int = int(os.getenv("PASSWORD_HISTORY_COUNT", "5"))

    # Rate limiting
    LOGIN_RATE_LIMIT: int = int(os.getenv("LOGIN_RATE_LIMIT", "5"))
    API_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "100"))
    RATE_LIMIT_WINDOW_MINUTES: int = int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", "60"))

    # Session management
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
    SECURE_COOKIES: bool = os.getenv("SECURE_COOKIES", "true").lower() == "true"
    HTTPONLY_COOKIES: bool = os.getenv("HTTPONLY_COOKIES", "true").lower() == "true"
    SAMESITE_COOKIES: str = os.getenv("SAMESITE_COOKIES", "Strict")

    # Encryption
    ENCRYPTION_KEY: Optional[str] = os.getenv("ENCRYPTION_KEY")
    AES_KEY_SIZE: int = 256

    # HTTPS and TLS
    FORCE_HTTPS: bool = os.getenv("FORCE_HTTPS", "true").lower() == "true"
    HSTS_MAX_AGE: int = int(os.getenv("HSTS_MAX_AGE", "31536000"))  # 1 year

    # CORS settings
    ALLOWED_ORIGINS: List[str] = field(default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else [])
    ALLOWED_METHODS: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    ALLOWED_HEADERS: List[str] = field(default_factory=lambda: ["Content-Type", "Authorization", "X-Requested-With"])

    # Content Security Policy
    CSP_DEFAULT_SRC: str = "'self'"
    CSP_SCRIPT_SRC: str = "'self' 'unsafe-inline'"
    CSP_STYLE_SRC: str = "'self' 'unsafe-inline'"
    CSP_IMG_SRC: str = "'self' data: https:"
    CSP_CONNECT_SRC: str = "'self'"

    # File upload security
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    ALLOWED_FILE_EXTENSIONS: List[str] = field(default_factory=lambda: [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".txt", ".csv", ".json"])
    UPLOAD_SCAN_VIRUSES: bool = os.getenv("UPLOAD_SCAN_VIRUSES", "false").lower() == "true"

    # Database security
    DB_CONNECTION_TIMEOUT: int = int(os.getenv("DB_CONNECTION_TIMEOUT", "30"))
    DB_USE_SSL: bool = os.getenv("DB_USE_SSL", "true").lower() == "true"

    # Logging and monitoring
    SECURITY_LOG_LEVEL: str = os.getenv("SECURITY_LOG_LEVEL", "INFO")
    LOG_FAILED_LOGINS: bool = os.getenv("LOG_FAILED_LOGINS", "true").lower() == "true"
    LOG_SENSITIVE_DATA: bool = os.getenv("LOG_SENSITIVE_DATA", "false").lower() == "true"

    # 2FA settings
    ENABLE_2FA: bool = os.getenv("ENABLE_2FA", "false").lower() == "true"
    TOTP_ISSUER: str = os.getenv("TOTP_ISSUER", "API Orchestrator")

    # API security
    REQUIRE_API_KEY: bool = os.getenv("REQUIRE_API_KEY", "true").lower() == "true"
    API_KEY_HEADER: str = os.getenv("API_KEY_HEADER", "X-API-Key")

    # Development/Debug settings
    DEBUG_MODE: bool = os.getenv("DEBUG", "false").lower() == "true"
    DEVELOPMENT_MODE: bool = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"

class SecurityValidator:
    """Validate security configuration and environment"""

    def __init__(self, settings: SecuritySettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)

    def validate_configuration(self) -> List[str]:
        """Validate security configuration and return issues"""
        issues = []

        # Critical security checks
        if not self.settings.JWT_SECRET_KEY or len(self.settings.JWT_SECRET_KEY) < 32:
            issues.append("CRITICAL: JWT_SECRET_KEY is missing or too short (minimum 32 characters)")

        if not self.settings.ENCRYPTION_KEY:
            issues.append("WARNING: ENCRYPTION_KEY not set - data encryption will use random key")

        # Production security checks
        if not self.settings.DEBUG_MODE:  # Production environment
            if self.settings.DEVELOPMENT_MODE:
                issues.append("CRITICAL: DEVELOPMENT_MODE enabled in production")

            if not self.settings.FORCE_HTTPS:
                issues.append("CRITICAL: HTTPS not enforced in production")

            if not self.settings.SECURE_COOKIES:
                issues.append("HIGH: Secure cookies not enabled in production")

            if self.settings.LOG_SENSITIVE_DATA:
                issues.append("HIGH: Sensitive data logging enabled in production")

        # Password policy validation
        if self.settings.MIN_PASSWORD_LENGTH < 8:
            issues.append("MEDIUM: Minimum password length is below recommended (8 characters)")

        # Rate limiting validation
        if self.settings.LOGIN_RATE_LIMIT > 10:
            issues.append("MEDIUM: Login rate limit is high - consider reducing for better security")

        # Session security
        if self.settings.SESSION_TIMEOUT_MINUTES > 480:  # 8 hours
            issues.append("MEDIUM: Session timeout is very long - consider reducing")

        # CORS validation
        if "*" in self.settings.ALLOWED_ORIGINS and not self.settings.DEBUG_MODE:
            issues.append("CRITICAL: Wildcard CORS origin allowed in production")

        # File upload validation
        if self.settings.MAX_FILE_SIZE_MB > 100:
            issues.append("MEDIUM: Maximum file size is very large - consider reducing")

        return issues

    def check_environment_variables(self) -> List[str]:
        """Check for missing or insecure environment variables"""
        issues = []

        # Required variables
        required_vars = {
            "JWT_SECRET_KEY": "JWT secret key for token signing",
            "DATABASE_URL": "Database connection string"
        }

        for var, description in required_vars.items():
            if not os.getenv(var):
                issues.append(f"MISSING: {var} - {description}")

        # Recommended variables
        recommended_vars = {
            "ENCRYPTION_KEY": "Key for data encryption",
            "ALLOWED_ORIGINS": "CORS allowed origins",
            "RATE_LIMIT_WINDOW_MINUTES": "Rate limiting window"
        }

        for var, description in recommended_vars.items():
            if not os.getenv(var):
                issues.append(f"RECOMMENDED: {var} - {description}")

        # Check for default/weak values
        weak_defaults = {
            "JWT_SECRET_KEY": ["secret", "changeme", "password", "default"],
            "DATABASE_URL": ["localhost", "password", "admin"]
        }

        for var, weak_values in weak_defaults.items():
            value = os.getenv(var, "").lower()
            for weak in weak_values:
                if weak in value:
                    issues.append(f"WEAK: {var} contains weak/default value")
                    break

        return issues

    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        config_issues = self.validate_configuration()
        env_issues = self.check_environment_variables()

        # Categorize issues by severity
        critical_issues = [issue for issue in config_issues + env_issues if issue.startswith("CRITICAL")]
        high_issues = [issue for issue in config_issues + env_issues if issue.startswith("HIGH")]
        medium_issues = [issue for issue in config_issues + env_issues if issue.startswith("MEDIUM")]
        low_issues = [issue for issue in config_issues + env_issues if issue.startswith("LOW")]
        missing_issues = [issue for issue in env_issues if issue.startswith("MISSING")]
        recommended_issues = [issue for issue in env_issues if issue.startswith("RECOMMENDED")]

        report = {
            "timestamp": "2025-09-21T23:52:00Z",
            "total_issues": len(config_issues) + len(env_issues),
            "critical_issues": len(critical_issues),
            "high_issues": len(high_issues),
            "medium_issues": len(medium_issues),
            "security_score": self._calculate_security_score(critical_issues, high_issues, medium_issues),
            "issues": {
                "critical": critical_issues,
                "high": high_issues,
                "medium": medium_issues,
                "low": low_issues,
                "missing": missing_issues,
                "recommended": recommended_issues
            },
            "configuration": {
                "force_https": self.settings.FORCE_HTTPS,
                "secure_cookies": self.settings.SECURE_COOKIES,
                "password_min_length": self.settings.MIN_PASSWORD_LENGTH,
                "session_timeout": self.settings.SESSION_TIMEOUT_MINUTES,
                "2fa_enabled": self.settings.ENABLE_2FA,
                "debug_mode": self.settings.DEBUG_MODE
            },
            "recommendations": self._generate_recommendations(critical_issues, high_issues, medium_issues)
        }

        return report

    def _calculate_security_score(self, critical: List[str], high: List[str], medium: List[str]) -> int:
        """Calculate security score (0-100)"""
        base_score = 100

        # Deduct points for issues
        base_score -= len(critical) * 20  # Critical issues: -20 points each
        base_score -= len(high) * 10      # High issues: -10 points each
        base_score -= len(medium) * 5     # Medium issues: -5 points each

        return max(0, base_score)

    def _generate_recommendations(self, critical: List[str], high: List[str], medium: List[str]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []

        if critical:
            recommendations.append("URGENT: Address all critical security issues immediately")
            recommendations.append("Consider temporarily disabling affected features until fixed")

        if high:
            recommendations.append("Address high-severity issues within 24 hours")

        if medium:
            recommendations.append("Schedule medium-severity fixes within the next sprint")

        # General recommendations
        recommendations.extend([
            "Implement automated security scanning in CI/CD pipeline",
            "Regular security training for development team",
            "Enable comprehensive security logging and monitoring",
            "Conduct regular penetration testing",
            "Implement dependency vulnerability scanning",
            "Use secrets management system (e.g., HashiCorp Vault, AWS Secrets Manager)",
            "Enable database encryption at rest",
            "Implement Web Application Firewall (WAF)",
            "Regular security audits and code reviews"
        ])

        return recommendations

# Global security settings instance
security_settings = SecuritySettings()
security_validator = SecurityValidator(security_settings)

def get_security_headers() -> Dict[str, str]:
    """Get HTTP security headers based on configuration"""
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }

    # HSTS header (only for HTTPS)
    if security_settings.FORCE_HTTPS:
        headers["Strict-Transport-Security"] = f"max-age={security_settings.HSTS_MAX_AGE}; includeSubDomains"

    # Content Security Policy
    csp_parts = [
        f"default-src {security_settings.CSP_DEFAULT_SRC}",
        f"script-src {security_settings.CSP_SCRIPT_SRC}",
        f"style-src {security_settings.CSP_STYLE_SRC}",
        f"img-src {security_settings.CSP_IMG_SRC}",
        f"connect-src {security_settings.CSP_CONNECT_SRC}"
    ]
    headers["Content-Security-Policy"] = "; ".join(csp_parts)

    return headers

def validate_file_upload(filename: str, file_size: int) -> tuple[bool, Optional[str]]:
    """Validate file upload based on security settings"""
    # Check file size
    max_size_bytes = security_settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"File size exceeds maximum allowed ({security_settings.MAX_FILE_SIZE_MB}MB)"

    # Check file extension
    file_ext = Path(filename).suffix.lower()
    if file_ext not in security_settings.ALLOWED_FILE_EXTENSIONS:
        return False, f"File type not allowed. Allowed types: {', '.join(security_settings.ALLOWED_FILE_EXTENSIONS)}"

    # Check for dangerous filenames
    dangerous_patterns = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
    if any(pattern in filename for pattern in dangerous_patterns):
        return False, "Filename contains dangerous characters"

    return True, None

if __name__ == "__main__":
    # Generate and display security report
    validator = SecurityValidator(security_settings)
    report = validator.generate_security_report()

    print("🔒 SECURITY CONFIGURATION REPORT")
    print("=" * 50)
    print(f"Security Score: {report['security_score']}/100")
    print(f"Total Issues: {report['total_issues']}")
    print()

    if report['issues']['critical']:
        print("🚨 CRITICAL ISSUES:")
        for issue in report['issues']['critical']:
            print(f"  - {issue}")
        print()

    if report['issues']['high']:
        print("⚠️  HIGH ISSUES:")
        for issue in report['issues']['high']:
            print(f"  - {issue}")
        print()

    if report['issues']['medium']:
        print("📋 MEDIUM ISSUES:")
        for issue in report['issues']['medium']:
            print(f"  - {issue}")
        print()

    print("📝 RECOMMENDATIONS:")
    for rec in report['recommendations'][:5]:  # Show top 5
        print(f"  - {rec}")