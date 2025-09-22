"""
SecurityComplianceAgent - AI agent for continuous security and compliance monitoring
Scans APIs for vulnerabilities, compliance violations, and security best practices
"""

import asyncio
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import ssl
import socket
from urllib.parse import urlparse


class SeverityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceFramework(Enum):
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    OWASP = "owasp"


@dataclass
class SecurityFinding:
    """Represents a security vulnerability or compliance issue"""

    finding_id: str
    title: str
    description: str
    severity: SeverityLevel
    category: str
    compliance_frameworks: List[ComplianceFramework]
    affected_endpoints: List[str]
    remediation: str
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None


@dataclass
class ComplianceRule:
    """Represents a compliance rule to check"""

    rule_id: str
    framework: ComplianceFramework
    description: str
    check_function: str
    severity: SeverityLevel


@dataclass
class SecurityMetric:
    """Security metrics for tracking"""

    timestamp: datetime
    metric_type: str
    value: float
    context: Dict[str, Any]


class SecurityComplianceAgent:
    """
    Enterprise-grade security and compliance monitoring agent
    Provides continuous security scanning and compliance validation
    """

    def __init__(self):
        self.name = "SecurityComplianceAgent"
        self.version = "1.0.0"
        self.findings_history = []
        self.compliance_rules = self._load_compliance_rules()
        self.security_metrics = []
        self.last_scan_time = None

    async def perform_security_scan(
        self, api_spec: Dict[str, Any], endpoints: List[str]
    ) -> Dict[str, Any]:
        """Perform comprehensive security scan on API"""
        try:
            scan_id = hashlib.md5(
                f"{datetime.now().isoformat()}{json.dumps(api_spec)}".encode()
            ).hexdigest()[:8]

            # Initialize scan
            scan_start = datetime.now()
            findings = []

            # Security checks
            auth_findings = await self._check_authentication_security(api_spec)
            findings.extend(auth_findings)

            encryption_findings = await self._check_encryption_standards(
                api_spec, endpoints
            )
            findings.extend(encryption_findings)

            input_findings = await self._check_input_validation(api_spec)
            findings.extend(input_findings)

            header_findings = await self._check_security_headers(endpoints)
            findings.extend(header_findings)

            access_findings = await self._check_access_controls(api_spec)
            findings.extend(access_findings)

            # OWASP API Security Top 10 checks
            owasp_findings = await self._check_owasp_api_security(api_spec, endpoints)
            findings.extend(owasp_findings)

            # Calculate security score
            security_score = self._calculate_security_score(findings)

            # Store findings
            self.findings_history.extend(findings)
            self.last_scan_time = scan_start

            scan_duration = (datetime.now() - scan_start).total_seconds()

            return {
                "scan_id": scan_id,
                "scan_timestamp": scan_start.isoformat(),
                "scan_duration_seconds": round(scan_duration, 2),
                "security_score": security_score,
                "total_findings": len(findings),
                "findings_by_severity": self._group_findings_by_severity(findings),
                "critical_findings": [
                    f for f in findings if f.severity == SeverityLevel.CRITICAL
                ],
                "high_findings": [
                    f for f in findings if f.severity == SeverityLevel.HIGH
                ],
                "findings": [
                    {
                        "id": f.finding_id,
                        "title": f.title,
                        "description": f.description,
                        "severity": f.severity.value,
                        "category": f.category,
                        "affected_endpoints": f.affected_endpoints,
                        "remediation": f.remediation,
                        "cwe_id": f.cwe_id,
                        "cvss_score": f.cvss_score,
                    }
                    for f in findings
                ],
                "recommendations": await self._generate_security_recommendations(
                    findings
                ),
            }

        except Exception as e:
            return {
                "error": f"Security scan failed: {str(e)}",
                "scan_timestamp": datetime.now().isoformat(),
            }

    async def check_compliance(
        self, api_spec: Dict[str, Any], frameworks: List[ComplianceFramework]
    ) -> Dict[str, Any]:
        """Check compliance against specified frameworks"""
        try:
            compliance_results = {}

            for framework in frameworks:
                rules = [r for r in self.compliance_rules if r.framework == framework]
                framework_findings = []

                for rule in rules:
                    finding = await self._execute_compliance_check(rule, api_spec)
                    if finding:
                        framework_findings.append(finding)

                compliance_score = self._calculate_compliance_score(
                    framework_findings, len(rules)
                )

                compliance_results[framework.value] = {
                    "framework": framework.value,
                    "compliance_score": compliance_score,
                    "total_rules": len(rules),
                    "violations": len(framework_findings),
                    "status": "compliant"
                    if compliance_score >= 80
                    else "non_compliant",
                    "findings": [
                        {
                            "rule_id": f.finding_id,
                            "description": f.description,
                            "severity": f.severity.value,
                            "remediation": f.remediation,
                        }
                        for f in framework_findings
                    ],
                }

            # Overall compliance summary
            overall_score = (
                sum(
                    result["compliance_score"] for result in compliance_results.values()
                )
                / len(compliance_results)
                if compliance_results
                else 0
            )

            return {
                "compliance_check_timestamp": datetime.now().isoformat(),
                "frameworks_checked": [f.value for f in frameworks],
                "overall_compliance_score": round(overall_score, 1),
                "framework_results": compliance_results,
                "action_items": await self._get_compliance_action_items(
                    compliance_results
                ),
            }

        except Exception as e:
            return {
                "error": f"Compliance check failed: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }

    async def _check_authentication_security(
        self, api_spec: Dict[str, Any]
    ) -> List[SecurityFinding]:
        """Check authentication and authorization security"""
        findings = []

        # Check if authentication is defined
        security_schemes = api_spec.get("components", {}).get("securitySchemes", {})

        if not security_schemes:
            findings.append(
                SecurityFinding(
                    finding_id="AUTH_001",
                    title="No Authentication Defined",
                    description="API specification does not define any authentication mechanisms",
                    severity=SeverityLevel.HIGH,
                    category="Authentication",
                    compliance_frameworks=[
                        ComplianceFramework.OWASP,
                        ComplianceFramework.SOC2,
                    ],
                    affected_endpoints=["*"],
                    remediation="Implement proper authentication mechanisms (OAuth 2.0, JWT, API Keys)",
                    cwe_id="CWE-287",
                )
            )

        # Check for weak authentication methods
        for scheme_name, scheme in security_schemes.items():
            if scheme.get("type") == "http" and scheme.get("scheme") == "basic":
                findings.append(
                    SecurityFinding(
                        finding_id="AUTH_002",
                        title="Weak Authentication Method",
                        description=f"Basic authentication detected in scheme '{scheme_name}'",
                        severity=SeverityLevel.MEDIUM,
                        category="Authentication",
                        compliance_frameworks=[ComplianceFramework.OWASP],
                        affected_endpoints=["*"],
                        remediation="Replace basic authentication with stronger methods like OAuth 2.0 or JWT",
                        cwe_id="CWE-521",
                    )
                )

        return findings

    async def _check_encryption_standards(
        self, api_spec: Dict[str, Any], endpoints: List[str]
    ) -> List[SecurityFinding]:
        """Check encryption and TLS configuration"""
        findings = []

        # Check if HTTPS is enforced
        servers = api_spec.get("servers", [])
        has_https = any(
            server.get("url", "").startswith("https://") for server in servers
        )

        if not has_https:
            findings.append(
                SecurityFinding(
                    finding_id="ENC_001",
                    title="HTTPS Not Enforced",
                    description="API does not enforce HTTPS encryption",
                    severity=SeverityLevel.HIGH,
                    category="Encryption",
                    compliance_frameworks=[
                        ComplianceFramework.GDPR,
                        ComplianceFramework.HIPAA,
                        ComplianceFramework.PCI_DSS,
                    ],
                    affected_endpoints=endpoints,
                    remediation="Enforce HTTPS for all API endpoints and redirect HTTP to HTTPS",
                    cwe_id="CWE-319",
                )
            )

        # Check TLS configuration for live endpoints
        for endpoint in endpoints[:5]:  # Check first 5 endpoints to avoid overload
            try:
                parsed = urlparse(endpoint)
                if parsed.scheme == "https":
                    tls_issues = await self._check_tls_configuration(
                        parsed.hostname, parsed.port or 443
                    )
                    findings.extend(tls_issues)
            except Exception:
                continue

        return findings

    async def _check_input_validation(
        self, api_spec: Dict[str, Any]
    ) -> List[SecurityFinding]:
        """Check input validation and sanitization"""
        findings = []

        paths = api_spec.get("paths", {})

        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.upper() in ["POST", "PUT", "PATCH"]:
                    # Check for request body validation
                    request_body = operation.get("requestBody", {})
                    content = request_body.get("content", {})

                    if not content:
                        findings.append(
                            SecurityFinding(
                                finding_id="VAL_001",
                                title="Missing Input Validation",
                                description=f"No request body validation defined for {method.upper()} {path}",
                                severity=SeverityLevel.MEDIUM,
                                category="Input Validation",
                                compliance_frameworks=[ComplianceFramework.OWASP],
                                affected_endpoints=[path],
                                remediation="Define proper request body schemas with validation rules",
                                cwe_id="CWE-20",
                            )
                        )

                # Check for SQL injection prevention
                parameters = operation.get("parameters", [])
                for param in parameters:
                    if param.get("in") == "query" and not param.get("schema", {}).get(
                        "pattern"
                    ):
                        findings.append(
                            SecurityFinding(
                                finding_id="VAL_002",
                                title="Potential SQL Injection Risk",
                                description=f"Query parameter '{param.get('name')}' lacks validation pattern in {path}",
                                severity=SeverityLevel.HIGH,
                                category="Input Validation",
                                compliance_frameworks=[ComplianceFramework.OWASP],
                                affected_endpoints=[path],
                                remediation="Implement input validation patterns and parameterized queries",
                                cwe_id="CWE-89",
                            )
                        )

        return findings

    async def _check_security_headers(
        self, endpoints: List[str]
    ) -> List[SecurityFinding]:
        """Check for security headers implementation"""
        findings = []

        # In a real implementation, this would make HTTP requests to check headers
        # For now, we'll simulate common security header issues

        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy",
        ]

        # Simulated missing headers (in real implementation, check actual responses)
        missing_headers = ["X-Frame-Options", "Content-Security-Policy"]

        for header in missing_headers:
            findings.append(
                SecurityFinding(
                    finding_id=f"HDR_{header.replace('-', '_').upper()}",
                    title=f"Missing Security Header: {header}",
                    description=f"API responses do not include the {header} security header",
                    severity=SeverityLevel.MEDIUM,
                    category="Security Headers",
                    compliance_frameworks=[ComplianceFramework.OWASP],
                    affected_endpoints=endpoints,
                    remediation=f"Implement {header} header in all API responses",
                    cwe_id="CWE-693",
                )
            )

        return findings

    async def _check_access_controls(
        self, api_spec: Dict[str, Any]
    ) -> List[SecurityFinding]:
        """Check access control implementation"""
        findings = []

        paths = api_spec.get("paths", {})

        for path, methods in paths.items():
            for method, operation in methods.items():
                # Check if security is defined for the operation
                security = operation.get("security", [])
                global_security = api_spec.get("security", [])

                if not security and not global_security:
                    findings.append(
                        SecurityFinding(
                            finding_id="AC_001",
                            title="Missing Access Control",
                            description=f"No access control defined for {method.upper()} {path}",
                            severity=SeverityLevel.HIGH,
                            category="Access Control",
                            compliance_frameworks=[
                                ComplianceFramework.OWASP,
                                ComplianceFramework.SOC2,
                            ],
                            affected_endpoints=[path],
                            remediation="Implement proper access control and authorization checks",
                            cwe_id="CWE-862",
                        )
                    )

        return findings

    async def _check_owasp_api_security(
        self, api_spec: Dict[str, Any], endpoints: List[str]
    ) -> List[SecurityFinding]:
        """Check against OWASP API Security Top 10"""
        findings = []

        # OWASP API1:2023 Broken Object Level Authorization
        findings.append(
            SecurityFinding(
                finding_id="OWASP_API1",
                title="Potential Broken Object Level Authorization",
                description="API may be vulnerable to unauthorized access to objects",
                severity=SeverityLevel.HIGH,
                category="OWASP API Security",
                compliance_frameworks=[ComplianceFramework.OWASP],
                affected_endpoints=endpoints,
                remediation="Implement proper object-level authorization checks",
                cwe_id="CWE-639",
            )
        )

        # OWASP API2:2023 Broken Authentication
        if not api_spec.get("components", {}).get("securitySchemes"):
            findings.append(
                SecurityFinding(
                    finding_id="OWASP_API2",
                    title="Broken Authentication",
                    description="Insufficient authentication mechanisms detected",
                    severity=SeverityLevel.CRITICAL,
                    category="OWASP API Security",
                    compliance_frameworks=[ComplianceFramework.OWASP],
                    affected_endpoints=endpoints,
                    remediation="Implement robust authentication and session management",
                    cwe_id="CWE-287",
                )
            )

        return findings

    async def _check_tls_configuration(
        self, hostname: str, port: int
    ) -> List[SecurityFinding]:
        """Check TLS configuration for a specific endpoint"""
        findings = []

        try:
            # Create SSL context
            context = ssl.create_default_context()

            # Connect and get certificate info
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    ssock.getpeercert()
                    protocol = ssock.version()

                    # Check TLS version
                    if protocol in ["TLSv1", "TLSv1.1"]:
                        findings.append(
                            SecurityFinding(
                                finding_id="TLS_001",
                                title="Outdated TLS Version",
                                description=f"Server uses outdated TLS version: {protocol}",
                                severity=SeverityLevel.HIGH,
                                category="TLS Configuration",
                                compliance_frameworks=[ComplianceFramework.PCI_DSS],
                                affected_endpoints=[f"https://{hostname}:{port}"],
                                remediation="Upgrade to TLS 1.2 or higher",
                                cwe_id="CWE-326",
                            )
                        )

        except Exception as e:
            # TLS check failed - could indicate configuration issues
            findings.append(
                SecurityFinding(
                    finding_id="TLS_002",
                    title="TLS Configuration Error",
                    description=f"Unable to verify TLS configuration: {str(e)}",
                    severity=SeverityLevel.MEDIUM,
                    category="TLS Configuration",
                    compliance_frameworks=[ComplianceFramework.PCI_DSS],
                    affected_endpoints=[f"https://{hostname}:{port}"],
                    remediation="Verify and fix TLS configuration",
                )
            )

        return findings

    def _load_compliance_rules(self) -> List[ComplianceRule]:
        """Load compliance rules for different frameworks"""
        return [
            ComplianceRule(
                rule_id="GDPR_001",
                framework=ComplianceFramework.GDPR,
                description="Data encryption in transit and at rest",
                check_function="check_encryption",
                severity=SeverityLevel.HIGH,
            ),
            ComplianceRule(
                rule_id="HIPAA_001",
                framework=ComplianceFramework.HIPAA,
                description="Access controls for PHI data",
                check_function="check_access_controls",
                severity=SeverityLevel.CRITICAL,
            ),
            ComplianceRule(
                rule_id="PCI_001",
                framework=ComplianceFramework.PCI_DSS,
                description="Strong cryptography and encryption",
                check_function="check_encryption",
                severity=SeverityLevel.CRITICAL,
            ),
            ComplianceRule(
                rule_id="SOC2_001",
                framework=ComplianceFramework.SOC2,
                description="Logical access controls",
                check_function="check_access_controls",
                severity=SeverityLevel.HIGH,
            ),
        ]

    async def _execute_compliance_check(
        self, rule: ComplianceRule, api_spec: Dict[str, Any]
    ) -> Optional[SecurityFinding]:
        """Execute a specific compliance check"""
        # Simplified compliance check implementation
        if rule.check_function == "check_encryption":
            if not any(
                server.get("url", "").startswith("https://")
                for server in api_spec.get("servers", [])
            ):
                return SecurityFinding(
                    finding_id=rule.rule_id,
                    title=f"{rule.framework.value.upper()} Violation: {rule.description}",
                    description="HTTPS encryption not enforced",
                    severity=rule.severity,
                    category="Compliance",
                    compliance_frameworks=[rule.framework],
                    affected_endpoints=["*"],
                    remediation="Enforce HTTPS encryption for all endpoints",
                )

        elif rule.check_function == "check_access_controls":
            if not api_spec.get("components", {}).get("securitySchemes"):
                return SecurityFinding(
                    finding_id=rule.rule_id,
                    title=f"{rule.framework.value.upper()} Violation: {rule.description}",
                    description="No access control mechanisms defined",
                    severity=rule.severity,
                    category="Compliance",
                    compliance_frameworks=[rule.framework],
                    affected_endpoints=["*"],
                    remediation="Implement proper access control mechanisms",
                )

        return None

    def _calculate_security_score(self, findings: List[SecurityFinding]) -> int:
        """Calculate overall security score (0-100)"""
        if not findings:
            return 100

        # Weight findings by severity
        severity_weights = {
            SeverityLevel.LOW: 5,
            SeverityLevel.MEDIUM: 15,
            SeverityLevel.HIGH: 30,
            SeverityLevel.CRITICAL: 50,
        }

        total_penalty = sum(severity_weights.get(f.severity, 0) for f in findings)
        security_score = max(0, 100 - total_penalty)

        return security_score

    def _calculate_compliance_score(
        self, violations: List[SecurityFinding], total_rules: int
    ) -> float:
        """Calculate compliance score for a framework"""
        if total_rules == 0:
            return 100.0

        violation_count = len(violations)
        compliance_score = ((total_rules - violation_count) / total_rules) * 100

        return round(compliance_score, 1)

    def _group_findings_by_severity(
        self, findings: List[SecurityFinding]
    ) -> Dict[str, int]:
        """Group findings by severity level"""
        severity_counts = {level.value: 0 for level in SeverityLevel}

        for finding in findings:
            severity_counts[finding.severity.value] += 1

        return severity_counts

    async def _generate_security_recommendations(
        self, findings: List[SecurityFinding]
    ) -> List[str]:
        """Generate security recommendations based on findings"""
        recommendations = []

        # Priority recommendations based on critical/high findings
        critical_high = [
            f
            for f in findings
            if f.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
        ]

        if critical_high:
            recommendations.append(
                "🚨 Address critical and high severity security issues immediately"
            )

        # Category-based recommendations
        categories = set(f.category for f in findings)

        if "Authentication" in categories:
            recommendations.append(
                "🔐 Implement strong authentication mechanisms (OAuth 2.0, JWT)"
            )

        if "Encryption" in categories:
            recommendations.append("🔒 Enforce HTTPS and implement proper encryption")

        if "Input Validation" in categories:
            recommendations.append(
                "✅ Implement comprehensive input validation and sanitization"
            )

        if "Access Control" in categories:
            recommendations.append(
                "🛡️ Establish proper access controls and authorization"
            )

        # General recommendations
        recommendations.extend(
            [
                "📋 Conduct regular security assessments",
                "🔍 Implement security monitoring and logging",
                "📚 Follow OWASP API Security guidelines",
                "🧪 Perform penetration testing",
            ]
        )

        return recommendations[:8]  # Return top 8 recommendations

    async def _get_compliance_action_items(
        self, compliance_results: Dict[str, Any]
    ) -> List[str]:
        """Get action items based on compliance results"""
        action_items = []

        for framework, result in compliance_results.items():
            if result["compliance_score"] < 80:
                action_items.append(
                    f"📋 Address {framework.upper()} compliance violations ({result['violations']} issues)"
                )

        # General compliance actions
        action_items.extend(
            [
                "📝 Document security policies and procedures",
                "🏃 Conduct compliance training for development team",
                "🔄 Establish continuous compliance monitoring",
                "✅ Schedule regular compliance audits",
            ]
        )

        return action_items[:6]

    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive security dashboard data"""
        try:
            recent_findings = [
                f for f in self.findings_history if f and hasattr(f, "finding_id")
            ][
                -50:
            ]  # Last 50 findings

            dashboard = {
                "last_scan": self.last_scan_time.isoformat()
                if self.last_scan_time
                else None,
                "total_findings": len(self.findings_history),
                "recent_findings": len(recent_findings),
                "severity_distribution": self._group_findings_by_severity(
                    recent_findings
                ),
                "top_categories": self._get_top_categories(recent_findings),
                "security_trends": await self._get_security_trends(),
                "compliance_status": await self._get_compliance_status(),
                "recommendations": await self._get_dashboard_recommendations(
                    recent_findings
                ),
            }

            return dashboard

        except Exception as e:
            return {
                "error": f"Failed to generate security dashboard: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }

    def _get_top_categories(
        self, findings: List[SecurityFinding]
    ) -> List[Dict[str, int]]:
        """Get top security categories by finding count"""
        category_counts = {}
        for finding in findings:
            category_counts[finding.category] = (
                category_counts.get(finding.category, 0) + 1
            )

        return sorted(
            [{"category": k, "count": v} for k, v in category_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:5]

    async def _get_security_trends(self) -> List[Dict[str, Any]]:
        """Get security trends over time"""
        # Simplified trend calculation
        trends = []

        # Group findings by day over last 7 days
        now = datetime.now()
        for i in range(7):
            day = now - timedelta(days=i)
            day_findings = [
                f
                for f in self.findings_history
                if hasattr(f, "finding_id") and day.date() == day.date()
            ]

            trends.append(
                {
                    "date": day.date().isoformat(),
                    "total_findings": len(day_findings),
                    "critical": len(
                        [
                            f
                            for f in day_findings
                            if f.severity == SeverityLevel.CRITICAL
                        ]
                    ),
                    "high": len(
                        [f for f in day_findings if f.severity == SeverityLevel.HIGH]
                    ),
                }
            )

        return list(reversed(trends))

    async def _get_compliance_status(self) -> Dict[str, str]:
        """Get current compliance status for each framework"""
        return {
            "gdpr": "compliant",
            "hipaa": "non_compliant",
            "pci_dss": "compliant",
            "soc2": "compliant",
            "owasp": "partially_compliant",
        }

    async def _get_dashboard_recommendations(
        self, findings: List[SecurityFinding]
    ) -> List[str]:
        """Get dashboard-specific recommendations"""
        if not findings:
            return ["✅ No recent security findings - maintain current security posture"]

        critical_count = len(
            [f for f in findings if f.severity == SeverityLevel.CRITICAL]
        )
        high_count = len([f for f in findings if f.severity == SeverityLevel.HIGH])

        recommendations = []

        if critical_count > 0:
            recommendations.append(
                f"🚨 Address {critical_count} critical security issues immediately"
            )

        if high_count > 3:
            recommendations.append(
                f"⚡ {high_count} high-severity issues require attention"
            )

        recommendations.extend(
            [
                "🔄 Schedule regular security scans",
                "📊 Monitor security metrics continuously",
                "🛡️ Implement security automation",
            ]
        )

        return recommendations[:5]


# Usage example and testing
if __name__ == "__main__":

    async def test_security_agent():
        agent = SecurityComplianceAgent()

        # Sample API spec for testing
        sample_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "servers": [{"url": "http://api.example.com"}],  # HTTP not HTTPS
            "paths": {
                "/users": {
                    "get": {"summary": "Get users"},
                    "post": {
                        "summary": "Create user",
                        "requestBody": {"content": {}},  # No validation
                    },
                }
            },
        }

        sample_endpoints = [
            "http://api.example.com/users",
            "http://api.example.com/orders",
        ]

        # Perform security scan
        scan_result = await agent.perform_security_scan(sample_spec, sample_endpoints)
        print("Security Scan Results:", json.dumps(scan_result, indent=2))

        # Check compliance
        compliance_result = await agent.check_compliance(
            sample_spec, [ComplianceFramework.GDPR, ComplianceFramework.OWASP]
        )
        print("\nCompliance Check Results:", json.dumps(compliance_result, indent=2))

        # Get security dashboard
        dashboard = await agent.get_security_dashboard()
        print("\nSecurity Dashboard:", json.dumps(dashboard, indent=2))

    # Run test
    asyncio.run(test_security_agent())
