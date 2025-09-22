"""
API Governance and Compliance - Enterprise Standards
Enforce API design standards, compliance, and best practices
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import hashlib


class ComplianceFramework(Enum):
    """Compliance frameworks"""

    GDPR = "gdpr"  # General Data Protection Regulation
    HIPAA = "hipaa"  # Health Insurance Portability and Accountability Act
    SOC2 = "soc2"  # Service Organization Control 2
    PCI_DSS = "pci_dss"  # Payment Card Industry Data Security Standard
    ISO_27001 = "iso_27001"  # Information Security Management
    CCPA = "ccpa"  # California Consumer Privacy Act
    NIST = "nist"  # National Institute of Standards and Technology
    OWASP = "owasp"  # Open Web Application Security Project


class RuleType(Enum):
    """Types of governance rules"""

    NAMING = "naming"
    STRUCTURE = "structure"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    VERSIONING = "versioning"
    DATA_VALIDATION = "data_validation"
    ERROR_HANDLING = "error_handling"
    RATE_LIMITING = "rate_limiting"
    AUTHENTICATION = "authentication"


class RuleSeverity(Enum):
    """Rule violation severity"""

    ERROR = "error"  # Must fix
    WARNING = "warning"  # Should fix
    INFO = "info"  # Suggestion
    HINT = "hint"  # Best practice


class RuleViolation(BaseModel):
    """Rule violation details"""

    rule_id: str
    rule_name: str
    type: RuleType
    severity: RuleSeverity
    message: str
    location: Dict[str, Any]  # path, line, etc.
    suggestion: Optional[str] = None
    documentation_url: Optional[str] = None
    auto_fixable: bool = False
    fix_suggestion: Optional[str] = None


class GovernanceRule(BaseModel):
    """API governance rule definition"""

    id: str
    name: str
    description: str
    type: RuleType
    severity: RuleSeverity
    enabled: bool = True

    # Rule logic
    pattern: Optional[str] = None  # Regex pattern
    validator: Optional[str] = None  # Validator function name
    conditions: List[Dict[str, Any]] = []

    # Compliance mapping
    compliance_frameworks: List[ComplianceFramework] = []

    # Auto-fix
    auto_fixable: bool = False
    fix_template: Optional[str] = None

    # Documentation
    documentation: str = ""
    examples: List[Dict[str, str]] = []  # good/bad examples


class ComplianceReport(BaseModel):
    """Compliance assessment report"""

    id: str = Field(
        default_factory=lambda: hashlib.sha256(
            str(datetime.now()).encode()
        ).hexdigest()[:16]
    )
    api_id: str
    api_name: str
    scan_date: datetime = Field(default_factory=datetime.now)

    # Overall scores
    overall_score: float  # 0-100
    security_score: float
    documentation_score: float
    design_score: float

    # Violations
    total_violations: int = 0
    violations_by_severity: Dict[str, int] = {}
    violations_by_type: Dict[str, int] = {}
    violations: List[RuleViolation] = []

    # Compliance status
    compliance_status: Dict[str, bool] = {}  # framework -> compliant
    missing_requirements: Dict[str, List[str]] = {}

    # Recommendations
    recommendations: List[str] = []
    critical_issues: List[str] = []

    # Trends
    score_trend: str = "stable"  # improving, stable, declining
    previous_score: Optional[float] = None


class APIGovernance:
    """API Governance and Compliance Engine"""

    def __init__(self):
        self.rules = self._initialize_default_rules()
        self.custom_rules: List[GovernanceRule] = []
        self.compliance_mappings = self._initialize_compliance_mappings()
        self.scan_history: List[ComplianceReport] = []

    def _initialize_default_rules(self) -> List[GovernanceRule]:
        """Initialize default governance rules"""
        return [
            # Naming conventions
            GovernanceRule(
                id="naming-001",
                name="Resource naming convention",
                description="Resources should use kebab-case",
                type=RuleType.NAMING,
                severity=RuleSeverity.WARNING,
                pattern=r"^[a-z]+(-[a-z]+)*$",
                compliance_frameworks=[ComplianceFramework.OWASP],
                documentation="Use lowercase letters with hyphens for resource names",
            ),
            GovernanceRule(
                id="naming-002",
                name="Version in path",
                description="API path should include version",
                type=RuleType.NAMING,
                severity=RuleSeverity.ERROR,
                pattern=r"/v\d+/",
                compliance_frameworks=[ComplianceFramework.OWASP],
                documentation="Include API version in path (e.g., /v1/users)",
            ),
            # Security rules
            GovernanceRule(
                id="security-001",
                name="HTTPS required",
                description="All APIs must use HTTPS",
                type=RuleType.SECURITY,
                severity=RuleSeverity.ERROR,
                pattern=r"^https://",
                compliance_frameworks=[
                    ComplianceFramework.PCI_DSS,
                    ComplianceFramework.HIPAA,
                    ComplianceFramework.SOC2,
                ],
                documentation="Use HTTPS for all API endpoints",
            ),
            GovernanceRule(
                id="security-002",
                name="Authentication required",
                description="All endpoints must have authentication",
                type=RuleType.AUTHENTICATION,
                severity=RuleSeverity.ERROR,
                compliance_frameworks=[
                    ComplianceFramework.OWASP,
                    ComplianceFramework.ISO_27001,
                ],
                documentation="Implement proper authentication (OAuth2, API Keys, etc.)",
            ),
            GovernanceRule(
                id="security-003",
                name="Rate limiting",
                description="APIs should implement rate limiting",
                type=RuleType.RATE_LIMITING,
                severity=RuleSeverity.WARNING,
                compliance_frameworks=[ComplianceFramework.OWASP],
                documentation="Implement rate limiting to prevent abuse",
            ),
            # Data protection
            GovernanceRule(
                id="data-001",
                name="PII protection",
                description="Personally Identifiable Information must be encrypted",
                type=RuleType.SECURITY,
                severity=RuleSeverity.ERROR,
                compliance_frameworks=[
                    ComplianceFramework.GDPR,
                    ComplianceFramework.CCPA,
                    ComplianceFramework.HIPAA,
                ],
                documentation="Encrypt all PII data in transit and at rest",
            ),
            GovernanceRule(
                id="data-002",
                name="Data retention policy",
                description="APIs must specify data retention periods",
                type=RuleType.DOCUMENTATION,
                severity=RuleSeverity.WARNING,
                compliance_frameworks=[
                    ComplianceFramework.GDPR,
                    ComplianceFramework.CCPA,
                ],
                documentation="Document data retention and deletion policies",
            ),
            # Documentation
            GovernanceRule(
                id="doc-001",
                name="OpenAPI specification",
                description="APIs must have OpenAPI documentation",
                type=RuleType.DOCUMENTATION,
                severity=RuleSeverity.ERROR,
                compliance_frameworks=[ComplianceFramework.SOC2],
                documentation="Provide complete OpenAPI 3.0+ specification",
            ),
            GovernanceRule(
                id="doc-002",
                name="Response examples",
                description="All endpoints should have response examples",
                type=RuleType.DOCUMENTATION,
                severity=RuleSeverity.WARNING,
                documentation="Include example responses for all status codes",
            ),
            # Error handling
            GovernanceRule(
                id="error-001",
                name="Consistent error format",
                description="Use consistent error response format",
                type=RuleType.ERROR_HANDLING,
                severity=RuleSeverity.WARNING,
                compliance_frameworks=[ComplianceFramework.OWASP],
                documentation="Use RFC 7807 Problem Details format for errors",
            ),
            GovernanceRule(
                id="error-002",
                name="No sensitive data in errors",
                description="Error messages must not expose sensitive information",
                type=RuleType.ERROR_HANDLING,
                severity=RuleSeverity.ERROR,
                compliance_frameworks=[
                    ComplianceFramework.OWASP,
                    ComplianceFramework.PCI_DSS,
                ],
                documentation="Avoid exposing system details in error messages",
            ),
            # Performance
            GovernanceRule(
                id="perf-001",
                name="Pagination required",
                description="List endpoints must support pagination",
                type=RuleType.PERFORMANCE,
                severity=RuleSeverity.WARNING,
                documentation="Implement pagination for list endpoints",
            ),
            GovernanceRule(
                id="perf-002",
                name="Response time SLA",
                description="APIs should respond within 1 second",
                type=RuleType.PERFORMANCE,
                severity=RuleSeverity.INFO,
                documentation="Optimize for sub-second response times",
            ),
        ]

    def _initialize_compliance_mappings(self) -> Dict[ComplianceFramework, List[str]]:
        """Initialize compliance framework requirements"""
        return {
            ComplianceFramework.GDPR: [
                "data-001",  # PII protection
                "data-002",  # Data retention
                "security-001",  # HTTPS
                "security-002",  # Authentication
                "doc-001",  # Documentation
            ],
            ComplianceFramework.HIPAA: [
                "data-001",  # PII protection
                "security-001",  # HTTPS
                "security-002",  # Authentication
                "error-002",  # No sensitive data in errors
            ],
            ComplianceFramework.PCI_DSS: [
                "security-001",  # HTTPS
                "security-002",  # Authentication
                "data-001",  # PII protection
                "error-002",  # No sensitive data in errors
            ],
            ComplianceFramework.SOC2: [
                "security-001",  # HTTPS
                "security-002",  # Authentication
                "doc-001",  # Documentation
                "error-001",  # Consistent errors
            ],
            ComplianceFramework.OWASP: [
                "security-001",  # HTTPS
                "security-002",  # Authentication
                "security-003",  # Rate limiting
                "error-002",  # No sensitive data
                "naming-001",  # Naming convention
                "naming-002",  # Version in path
            ],
        }

    async def scan_api(
        self,
        api_spec: Dict[str, Any],
        api_id: str,
        api_name: str,
        compliance_frameworks: List[ComplianceFramework] = None,
    ) -> ComplianceReport:
        """Scan API for governance compliance"""

        report = ComplianceReport(api_id=api_id, api_name=api_name)

        violations = []

        # Check all enabled rules
        for rule in self.rules + self.custom_rules:
            if not rule.enabled:
                continue

            # Check if rule applies to requested frameworks
            if compliance_frameworks:
                if not any(
                    cf in rule.compliance_frameworks for cf in compliance_frameworks
                ):
                    continue

            # Run rule validation
            rule_violations = await self._validate_rule(rule, api_spec)
            violations.extend(rule_violations)

        # Process violations
        report.violations = violations
        report.total_violations = len(violations)

        # Count by severity
        for violation in violations:
            severity = violation.severity.value
            report.violations_by_severity[severity] = (
                report.violations_by_severity.get(severity, 0) + 1
            )

            rule_type = violation.type.value
            report.violations_by_type[rule_type] = (
                report.violations_by_type.get(rule_type, 0) + 1
            )

        # Calculate scores
        report.overall_score = self._calculate_score(violations)
        report.security_score = self._calculate_category_score(
            violations, RuleType.SECURITY
        )
        report.documentation_score = self._calculate_category_score(
            violations, RuleType.DOCUMENTATION
        )
        report.design_score = self._calculate_category_score(
            violations, RuleType.NAMING
        )

        # Check compliance status
        if compliance_frameworks:
            for framework in compliance_frameworks:
                is_compliant, missing = self._check_framework_compliance(
                    framework, violations
                )
                report.compliance_status[framework.value] = is_compliant
                if missing:
                    report.missing_requirements[framework.value] = missing

        # Generate recommendations
        report.recommendations = self._generate_recommendations(violations)
        report.critical_issues = self._identify_critical_issues(violations)

        # Check trend
        if self.scan_history:
            last_scan = self.scan_history[-1]
            if last_scan.api_id == api_id:
                report.previous_score = last_scan.overall_score
                if report.overall_score > last_scan.overall_score:
                    report.score_trend = "improving"
                elif report.overall_score < last_scan.overall_score:
                    report.score_trend = "declining"

        # Store in history
        self.scan_history.append(report)

        return report

    async def _validate_rule(
        self, rule: GovernanceRule, api_spec: Dict[str, Any]
    ) -> List[RuleViolation]:
        """Validate a single rule against API spec"""

        violations = []

        # OpenAPI spec validation
        if "openapi" in api_spec or "swagger" in api_spec:
            violations.extend(await self._validate_openapi_rule(rule, api_spec))

        # Custom validation logic
        if rule.validator:
            custom_violations = await self._run_custom_validator(rule, api_spec)
            violations.extend(custom_violations)

        return violations

    async def _validate_openapi_rule(
        self, rule: GovernanceRule, spec: Dict[str, Any]
    ) -> List[RuleViolation]:
        """Validate rule against OpenAPI spec"""

        violations = []

        # Check servers/URLs
        if rule.id == "security-001":  # HTTPS check
            servers = spec.get("servers", [])
            for idx, server in enumerate(servers):
                url = server.get("url", "")
                if not url.startswith("https://"):
                    violations.append(
                        RuleViolation(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            type=rule.type,
                            severity=rule.severity,
                            message=f"Server URL must use HTTPS: {url}",
                            location={"servers": idx, "url": url},
                            suggestion="Change URL to use HTTPS protocol",
                            auto_fixable=True,
                            fix_suggestion=url.replace("http://", "https://"),
                        )
                    )

        # Check paths
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            # Version in path check
            if rule.id == "naming-002":
                if not re.search(r"/v\d+", path):
                    violations.append(
                        RuleViolation(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            type=rule.type,
                            severity=rule.severity,
                            message=f"Path should include version: {path}",
                            location={"path": path},
                            suggestion="Add version prefix (e.g., /v1{path})",
                            auto_fixable=True,
                            fix_suggestion=f"/v1{path}",
                        )
                    )

            # Resource naming check
            if rule.id == "naming-001":
                parts = path.strip("/").split("/")
                for part in parts:
                    if not part.startswith("{") and not re.match(
                        r"^[a-z]+(-[a-z]+)*$", part
                    ):
                        violations.append(
                            RuleViolation(
                                rule_id=rule.id,
                                rule_name=rule.name,
                                type=rule.type,
                                severity=rule.severity,
                                message=f"Resource should use kebab-case: {part}",
                                location={"path": path, "resource": part},
                                suggestion="Use lowercase with hyphens",
                                auto_fixable=False,
                            )
                        )

            # Check methods
            for method, operation in methods.items():
                if not isinstance(operation, dict):
                    continue

                # Authentication check
                if rule.id == "security-002":
                    security = operation.get("security", spec.get("security", []))
                    if not security:
                        violations.append(
                            RuleViolation(
                                rule_id=rule.id,
                                rule_name=rule.name,
                                type=rule.type,
                                severity=rule.severity,
                                message=f"Endpoint lacks authentication: {method.upper()} {path}",
                                location={"path": path, "method": method},
                                suggestion="Add security requirement to operation",
                                auto_fixable=False,
                            )
                        )

                # Documentation checks
                if rule.id == "doc-002":
                    responses = operation.get("responses", {})
                    for status_code, response in responses.items():
                        if "example" not in response and "examples" not in response:
                            violations.append(
                                RuleViolation(
                                    rule_id=rule.id,
                                    rule_name=rule.name,
                                    type=rule.type,
                                    severity=rule.severity,
                                    message=f"Missing response example: {method.upper()} {path} ({status_code})",
                                    location={
                                        "path": path,
                                        "method": method,
                                        "status": status_code,
                                    },
                                    suggestion="Add example response",
                                    auto_fixable=False,
                                )
                            )

                # Pagination check for GET list endpoints
                if rule.id == "perf-001" and method == "get":
                    params = operation.get("parameters", [])
                    has_pagination = any(
                        p.get("name") in ["page", "limit", "offset", "cursor"]
                        for p in params
                    )
                    if (
                        not has_pagination
                        and "list" in operation.get("operationId", "").lower()
                    ):
                        violations.append(
                            RuleViolation(
                                rule_id=rule.id,
                                rule_name=rule.name,
                                type=rule.type,
                                severity=rule.severity,
                                message=f"List endpoint should support pagination: GET {path}",
                                location={"path": path, "method": method},
                                suggestion="Add page/limit or cursor parameters",
                                auto_fixable=False,
                            )
                        )

        return violations

    async def _run_custom_validator(
        self, rule: GovernanceRule, api_spec: Dict[str, Any]
    ) -> List[RuleViolation]:
        """Run custom validator function"""
        # Placeholder for custom validation logic
        return []

    def _calculate_score(self, violations: List[RuleViolation]) -> float:
        """Calculate overall compliance score"""

        if not violations:
            return 100.0

        # Weight by severity
        weights = {
            RuleSeverity.ERROR: 10,
            RuleSeverity.WARNING: 5,
            RuleSeverity.INFO: 2,
            RuleSeverity.HINT: 1,
        }

        total_weight = sum(weights[v.severity] for v in violations)
        max_weight = 100  # Maximum expected weight

        score = max(0, 100 - (total_weight / max_weight * 100))
        return round(score, 2)

    def _calculate_category_score(
        self, violations: List[RuleViolation], category: RuleType
    ) -> float:
        """Calculate score for specific category"""

        category_violations = [v for v in violations if v.type == category]
        return self._calculate_score(category_violations)

    def _check_framework_compliance(
        self, framework: ComplianceFramework, violations: List[RuleViolation]
    ) -> tuple[bool, List[str]]:
        """Check if API is compliant with framework"""

        required_rules = self.compliance_mappings.get(framework, [])
        violated_rules = {
            v.rule_id for v in violations if v.severity == RuleSeverity.ERROR
        }

        missing_rules = []
        for rule_id in required_rules:
            if rule_id in violated_rules:
                rule = next((r for r in self.rules if r.id == rule_id), None)
                if rule:
                    missing_rules.append(rule.name)

        is_compliant = len(missing_rules) == 0
        return is_compliant, missing_rules

    def _generate_recommendations(self, violations: List[RuleViolation]) -> List[str]:
        """Generate recommendations based on violations"""

        recommendations = []

        # Group by type
        by_type = {}
        for v in violations:
            if v.type not in by_type:
                by_type[v.type] = []
            by_type[v.type].append(v)

        # Security recommendations
        if RuleType.SECURITY in by_type:
            recommendations.append(
                "🔒 Prioritize fixing security violations to protect sensitive data"
            )
            if len(by_type[RuleType.SECURITY]) > 5:
                recommendations.append(
                    "⚠️ Consider a security audit - multiple security issues detected"
                )

        # Documentation recommendations
        if RuleType.DOCUMENTATION in by_type:
            recommendations.append(
                "📚 Improve API documentation for better developer experience"
            )

        # Performance recommendations
        if RuleType.PERFORMANCE in by_type:
            recommendations.append(
                "⚡ Optimize API performance to meet SLA requirements"
            )

        # Auto-fix recommendations
        auto_fixable = [v for v in violations if v.auto_fixable]
        if auto_fixable:
            recommendations.append(
                f"🔧 {len(auto_fixable)} violations can be auto-fixed"
            )

        return recommendations

    def _identify_critical_issues(self, violations: List[RuleViolation]) -> List[str]:
        """Identify critical issues that need immediate attention"""

        critical = []

        for v in violations:
            if v.severity == RuleSeverity.ERROR:
                if v.type == RuleType.SECURITY:
                    critical.append(f"🚨 SECURITY: {v.message}")
                elif v.type == RuleType.AUTHENTICATION:
                    critical.append(f"🔐 AUTH: {v.message}")
                elif "PII" in v.message or "personal" in v.message.lower():
                    critical.append(f"🔏 DATA PROTECTION: {v.message}")

        return critical[:5]  # Top 5 critical issues

    async def auto_fix_violations(
        self, api_spec: Dict[str, Any], violations: List[RuleViolation]
    ) -> Dict[str, Any]:
        """Auto-fix violations where possible"""

        fixed_spec = json.loads(json.dumps(api_spec))  # Deep copy
        fixed_count = 0

        for violation in violations:
            if not violation.auto_fixable:
                continue

            # Apply fix based on rule
            if violation.rule_id == "security-001":  # HTTPS
                if "servers" in fixed_spec:
                    for server in fixed_spec["servers"]:
                        if "url" in server:
                            server["url"] = server["url"].replace("http://", "https://")
                            fixed_count += 1

            elif violation.rule_id == "naming-002":  # Version in path
                if "paths" in fixed_spec:
                    new_paths = {}
                    for path, methods in fixed_spec["paths"].items():
                        if not re.search(r"/v\d+", path):
                            new_path = f"/v1{path}"
                            new_paths[new_path] = methods
                            fixed_count += 1
                        else:
                            new_paths[path] = methods
                    fixed_spec["paths"] = new_paths

        return {
            "fixed_spec": fixed_spec,
            "fixed_count": fixed_count,
            "total_fixable": len([v for v in violations if v.auto_fixable]),
        }

    async def add_custom_rule(self, rule: GovernanceRule):
        """Add custom governance rule"""
        self.custom_rules.append(rule)

    async def export_compliance_report(
        self, report: ComplianceReport, format: str = "json"  # json, html, pdf
    ) -> str:
        """Export compliance report in various formats"""

        if format == "json":
            return json.dumps(report.dict(), indent=2, default=str)

        elif format == "html":
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>API Compliance Report - {report.api_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .score {{ font-size: 48px; font-weight: bold; }}
        .good {{ color: green; }}
        .warning {{ color: orange; }}
        .bad {{ color: red; }}
        .section {{ margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>API Compliance Report</h1>
        <h2>{report.api_name}</h2>
        <p>Scan Date: {report.scan_date}</p>
        <div class="score {self._get_score_class(report.overall_score)}">
            Overall Score: {report.overall_score}%
        </div>
    </div>
    
    <div class="section">
        <h3>Compliance Status</h3>
        <table>
            <tr>
                <th>Framework</th>
                <th>Status</th>
            </tr>
"""
            for framework, compliant in report.compliance_status.items():
                status = "✅ Compliant" if compliant else "❌ Non-Compliant"
                html += f"""
            <tr>
                <td>{framework}</td>
                <td>{status}</td>
            </tr>
"""

            html += """
        </table>
    </div>
    
    <div class="section">
        <h3>Violations Summary</h3>
        <p>Total Violations: {report.total_violations}</p>
        <ul>
"""
            for severity, count in report.violations_by_severity.items():
                html += f"            <li>{severity.upper()}: {count}</li>\n"

            html += """
        </ul>
    </div>
    
    <div class="section">
        <h3>Critical Issues</h3>
        <ul>
"""
            for issue in report.critical_issues:
                html += f"            <li>{issue}</li>\n"

            html += """
        </ul>
    </div>
    
    <div class="section">
        <h3>Recommendations</h3>
        <ul>
"""
            for rec in report.recommendations:
                html += f"            <li>{rec}</li>\n"

            html += """
        </ul>
    </div>
</body>
</html>"""
            return html

        return ""

    def _get_score_class(self, score: float) -> str:
        """Get CSS class for score"""
        if score >= 80:
            return "good"
        elif score >= 60:
            return "warning"
        else:
            return "bad"


# Global governance instance
api_governance = APIGovernance()
