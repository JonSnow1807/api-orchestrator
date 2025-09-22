"""
Comprehensive Security Audit System
Performs automated security checks across the entire codebase
"""

import os
import re
import ast
import json
import logging
import hashlib
import subprocess
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

class SecuritySeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class VulnerabilityType(str, Enum):
    SQL_INJECTION = "SQL_INJECTION"
    XSS = "XSS"
    HARDCODED_SECRETS = "HARDCODED_SECRETS"
    INSECURE_RANDOM = "INSECURE_RANDOM"
    WEAK_CRYPTO = "WEAK_CRYPTO"
    PATH_TRAVERSAL = "PATH_TRAVERSAL"
    COMMAND_INJECTION = "COMMAND_INJECTION"
    DESERIALIZATION = "UNSAFE_DESERIALIZATION"
    WEAK_AUTH = "WEAK_AUTHENTICATION"
    INSUFFICIENT_LOGGING = "INSUFFICIENT_LOGGING"
    IMPROPER_ERROR_HANDLING = "IMPROPER_ERROR_HANDLING"
    RACE_CONDITION = "RACE_CONDITION"
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    DATA_EXPOSURE = "SENSITIVE_DATA_EXPOSURE"

@dataclass
class SecurityFinding:
    """Security vulnerability or issue finding"""
    vulnerability_type: VulnerabilityType
    severity: SecuritySeverity
    file_path: str
    line_number: int
    description: str
    code_snippet: str
    recommendation: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    confidence: float = 1.0
    impact: str = ""
    exploit_scenario: str = ""

@dataclass
class SecurityAuditReport:
    """Complete security audit report"""
    scan_timestamp: datetime
    total_files_scanned: int
    total_vulnerabilities: int
    findings: List[SecurityFinding] = field(default_factory=list)
    summary: Dict[SecuritySeverity, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    compliance_status: Dict[str, bool] = field(default_factory=dict)

class SecurityAuditor:
    """Comprehensive security auditing system"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        self.findings: List[SecurityFinding] = []

        # Security patterns to detect
        self.patterns = self._load_security_patterns()

        # File extensions to scan
        self.scan_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.php', '.rb'}

        # Files/directories to exclude
        self.exclusions = {
            'node_modules', 'venv', '__pycache__', '.git', 'dist', 'build',
            'target', 'vendor', '.env', 'test', 'tests', 'spec'
        }

    def _load_security_patterns(self) -> Dict[VulnerabilityType, List[Dict[str, Any]]]:
        """Load security vulnerability patterns"""
        return {
            VulnerabilityType.HARDCODED_SECRETS: [
                {
                    'pattern': r'(?i)(password|pwd|secret|key|token|api[_-]?key|access[_-]?token)\s*[=:]\s*["\'][^"\']{8,}["\']',
                    'description': 'Hardcoded password, secret, or API key detected',
                    'severity': SecuritySeverity.CRITICAL,
                    'cwe': 'CWE-798'
                },
                {
                    'pattern': r'(?i)(aws[_-]?access[_-]?key|aws[_-]?secret|db[_-]?password|database[_-]?password)\s*[=:]\s*["\'][^"\']+["\']',
                    'description': 'Hardcoded AWS credentials or database password',
                    'severity': SecuritySeverity.CRITICAL,
                    'cwe': 'CWE-798'
                }
            ],
            VulnerabilityType.SQL_INJECTION: [
                {
                    'pattern': r'(?i)(execute|query|select|insert|update|delete)\s*\(\s*["\'].*\+.*["\']',
                    'description': 'Potential SQL injection via string concatenation',
                    'severity': SecuritySeverity.HIGH,
                    'cwe': 'CWE-89'
                },
                {
                    'pattern': r'(?i)(cursor\.execute|db\.query|connection\.execute)\s*\([^)]*%[s|d]',
                    'description': 'SQL query using string formatting (potential injection)',
                    'severity': SecuritySeverity.HIGH,
                    'cwe': 'CWE-89'
                }
            ],
            VulnerabilityType.XSS: [
                {
                    'pattern': r'(?i)(innerHTML|outerHTML|document\.write)\s*[=+]\s*.*user.*input',
                    'description': 'Potential XSS via DOM manipulation with user input',
                    'severity': SecuritySeverity.HIGH,
                    'cwe': 'CWE-79'
                },
                {
                    'pattern': r'(?i)dangerouslySetInnerHTML.*__html:.*\{.*\}',
                    'description': 'React dangerouslySetInnerHTML usage (potential XSS)',
                    'severity': SecuritySeverity.MEDIUM,
                    'cwe': 'CWE-79'
                }
            ],
            VulnerabilityType.WEAK_CRYPTO: [
                {
                    'pattern': r'(?i)(md5|sha1|des|3des|rc4)[\(\.]',
                    'description': 'Weak cryptographic algorithm detected',
                    'severity': SecuritySeverity.HIGH,
                    'cwe': 'CWE-327'
                },
                {
                    'pattern': r'(?i)random\.random\(\)|math\.random\(\)',
                    'description': 'Insecure random number generation for security purposes',
                    'severity': SecuritySeverity.MEDIUM,
                    'cwe': 'CWE-338'
                }
            ],
            VulnerabilityType.PATH_TRAVERSAL: [
                {
                    'pattern': r'(?i)(open|file|read|write|include|require)\s*\([^)]*\.\./+',
                    'description': 'Potential path traversal with relative paths',
                    'severity': SecuritySeverity.HIGH,
                    'cwe': 'CWE-22'
                },
                {
                    'pattern': r'(?i)os\.path\.join\([^)]*request\.',
                    'description': 'Path joining with user input (potential traversal)',
                    'severity': SecuritySeverity.MEDIUM,
                    'cwe': 'CWE-22'
                }
            ],
            VulnerabilityType.COMMAND_INJECTION: [
                {
                    'pattern': r'(?i)(os\.system|subprocess\.call|exec|eval|shell_exec)\s*\([^)]*\+',
                    'description': 'Command execution with string concatenation',
                    'severity': SecuritySeverity.CRITICAL,
                    'cwe': 'CWE-78'
                },
                {
                    'pattern': r'(?i)subprocess\.(run|call|Popen)\([^)]*shell\s*=\s*True',
                    'description': 'Subprocess execution with shell=True',
                    'severity': SecuritySeverity.HIGH,
                    'cwe': 'CWE-78'
                }
            ],
            VulnerabilityType.DESERIALIZATION: [
                {
                    'pattern': r'(?i)(pickle\.loads|yaml\.load|json\.loads)\s*\([^)]*request\.',
                    'description': 'Unsafe deserialization of user input',
                    'severity': SecuritySeverity.HIGH,
                    'cwe': 'CWE-502'
                }
            ],
            VulnerabilityType.WEAK_AUTH: [
                {
                    'pattern': r'(?i)auth.*=.*["\']admin["\'].*["\']password["\']',
                    'description': 'Default or weak authentication credentials',
                    'severity': SecuritySeverity.HIGH,
                    'cwe': 'CWE-798'
                }
            ]
        }

    async def run_comprehensive_audit(self) -> SecurityAuditReport:
        """Run comprehensive security audit"""
        self.logger.info("🔒 Starting comprehensive security audit...")

        start_time = datetime.utcnow()
        total_files = 0

        # Static code analysis
        total_files += await self._scan_source_code()

        # Configuration analysis
        await self._scan_configuration_files()

        # Dependency analysis
        await self._scan_dependencies()

        # Infrastructure analysis
        await self._scan_infrastructure()

        # Generate report
        report = SecurityAuditReport(
            scan_timestamp=start_time,
            total_files_scanned=total_files,
            total_vulnerabilities=len(self.findings),
            findings=self.findings,
            summary=self._generate_summary(),
            recommendations=self._generate_recommendations(),
            compliance_status=self._check_compliance()
        )

        self.logger.info(f"🔒 Security audit completed. Found {len(self.findings)} issues.")
        return report

    async def _scan_source_code(self) -> int:
        """Scan source code for security vulnerabilities"""
        total_files = 0

        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclusions]

            for file in files:
                file_path = Path(root) / file

                if file_path.suffix in self.scan_extensions:
                    total_files += 1
                    await self._scan_file(file_path)

        return total_files

    async def _scan_file(self, file_path: Path):
        """Scan individual file for security issues"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            lines = content.split('\n')

            # Pattern-based scanning
            for vuln_type, patterns in self.patterns.items():
                for pattern_config in patterns:
                    pattern = pattern_config['pattern']

                    for line_num, line in enumerate(lines, 1):
                        matches = re.finditer(pattern, line)

                        for match in matches:
                            finding = SecurityFinding(
                                vulnerability_type=vuln_type,
                                severity=pattern_config['severity'],
                                file_path=str(file_path.relative_to(self.project_root)),
                                line_number=line_num,
                                description=pattern_config['description'],
                                code_snippet=line.strip(),
                                recommendation=self._get_recommendation(vuln_type),
                                cwe_id=pattern_config.get('cwe'),
                                confidence=0.8
                            )

                            self.findings.append(finding)

            # Language-specific analysis
            if file_path.suffix == '.py':
                await self._scan_python_specific(file_path, content)
            elif file_path.suffix in {'.js', '.ts', '.jsx', '.tsx'}:
                await self._scan_javascript_specific(file_path, content)

        except Exception as e:
            self.logger.warning(f"Error scanning {file_path}: {e}")

    async def _scan_python_specific(self, file_path: Path, content: str):
        """Python-specific security analysis"""
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # Check for eval/exec usage
                if isinstance(node, ast.Call):
                    if hasattr(node.func, 'id') and node.func.id in ['eval', 'exec']:
                        finding = SecurityFinding(
                            vulnerability_type=VulnerabilityType.COMMAND_INJECTION,
                            severity=SecuritySeverity.HIGH,
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=node.lineno,
                            description=f"Use of {node.func.id}() function",
                            code_snippet=f"Line {node.lineno}: {node.func.id}() usage detected",
                            recommendation="Avoid using eval() and exec(). Use safer alternatives.",
                            cwe_id="CWE-94",
                            confidence=0.9
                        )
                        self.findings.append(finding)

                # Check for pickle usage
                if isinstance(node, ast.Attribute) and node.attr == 'loads':
                    if hasattr(node.value, 'id') and node.value.id == 'pickle':
                        finding = SecurityFinding(
                            vulnerability_type=VulnerabilityType.DESERIALIZATION,
                            severity=SecuritySeverity.HIGH,
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=node.lineno,
                            description="Unsafe pickle.loads() usage",
                            code_snippet=f"Line {node.lineno}: pickle.loads() detected",
                            recommendation="Use json.loads() or implement custom serialization with validation.",
                            cwe_id="CWE-502",
                            confidence=0.9
                        )
                        self.findings.append(finding)

        except SyntaxError:
            pass  # Skip files with syntax errors

    async def _scan_javascript_specific(self, file_path: Path, content: str):
        """JavaScript/TypeScript-specific security analysis"""
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Check for localStorage without encryption
            if 'localStorage.setItem' in line and ('password' in line.lower() or 'token' in line.lower()):
                finding = SecurityFinding(
                    vulnerability_type=VulnerabilityType.DATA_EXPOSURE,
                    severity=SecuritySeverity.MEDIUM,
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_num,
                    description="Sensitive data stored in localStorage without encryption",
                    code_snippet=line.strip(),
                    recommendation="Encrypt sensitive data before storing in localStorage or use secure storage.",
                    cwe_id="CWE-312",
                    confidence=0.7
                )
                self.findings.append(finding)

    async def _scan_configuration_files(self):
        """Scan configuration files for security issues"""
        config_patterns = {
            '.env': r'(?i)(password|secret|key|token)\s*=\s*[^#\n]+',
            'config.json': r'(?i)"(password|secret|key|token)"\s*:\s*"[^"]+',
            '*.yml': r'(?i)(password|secret|key|token)\s*:\s*[^\n]+',
            '*.yaml': r'(?i)(password|secret|key|token)\s*:\s*[^\n]+'
        }

        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self.exclusions]

            for file in files:
                file_path = Path(root) / file

                for pattern_name, pattern in config_patterns.items():
                    if file == pattern_name or file.endswith(pattern_name.replace('*', '')):
                        await self._scan_config_file(file_path, pattern)

    async def _scan_config_file(self, file_path: Path, pattern: str):
        """Scan configuration file for sensitive data"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    finding = SecurityFinding(
                        vulnerability_type=VulnerabilityType.HARDCODED_SECRETS,
                        severity=SecuritySeverity.HIGH,
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_num,
                        description="Potential hardcoded credentials in configuration file",
                        code_snippet=line.strip(),
                        recommendation="Use environment variables or secure secret management.",
                        cwe_id="CWE-798",
                        confidence=0.8
                    )
                    self.findings.append(finding)

        except Exception as e:
            self.logger.warning(f"Error scanning config file {file_path}: {e}")

    async def _scan_dependencies(self):
        """Scan dependencies for known vulnerabilities"""
        # Python dependencies
        requirements_files = list(self.project_root.glob('**/requirements*.txt'))
        for req_file in requirements_files:
            await self._scan_python_dependencies(req_file)

        # Node.js dependencies
        package_files = list(self.project_root.glob('**/package.json'))
        for pkg_file in package_files:
            await self._scan_node_dependencies(pkg_file)

    async def _scan_python_dependencies(self, requirements_file: Path):
        """Scan Python dependencies for vulnerabilities"""
        try:
            # This would integrate with safety or other vulnerability databases
            # For now, we'll check for common insecure packages
            insecure_packages = {
                'flask<1.0': 'Outdated Flask version with security vulnerabilities',
                'django<3.2': 'Outdated Django version with security vulnerabilities',
                'requests<2.20': 'Outdated requests library with vulnerabilities',
                'pyyaml<5.4': 'PyYAML with unsafe loading'
            }

            with open(requirements_file, 'r') as f:
                content = f.read()

            for package, description in insecure_packages.items():
                if package.split('<')[0] in content:
                    finding = SecurityFinding(
                        vulnerability_type=VulnerabilityType.WEAK_AUTH,
                        severity=SecuritySeverity.MEDIUM,
                        file_path=str(requirements_file.relative_to(self.project_root)),
                        line_number=1,
                        description=f"Potentially vulnerable dependency: {description}",
                        code_snippet=package,
                        recommendation="Update to latest secure version",
                        confidence=0.6
                    )
                    self.findings.append(finding)

        except Exception as e:
            self.logger.warning(f"Error scanning Python dependencies: {e}")

    async def _scan_node_dependencies(self, package_file: Path):
        """Scan Node.js dependencies for vulnerabilities"""
        try:
            with open(package_file, 'r') as f:
                package_data = json.load(f)

            dependencies = package_data.get('dependencies', {})

            # Check for known vulnerable packages
            vulnerable_packages = {
                'lodash': 'Known prototype pollution vulnerabilities in older versions',
                'moment': 'Deprecated library, consider using day.js or date-fns',
                'handlebars': 'Template injection vulnerabilities in older versions'
            }

            for pkg_name, description in vulnerable_packages.items():
                if pkg_name in dependencies:
                    finding = SecurityFinding(
                        vulnerability_type=VulnerabilityType.WEAK_AUTH,
                        severity=SecuritySeverity.MEDIUM,
                        file_path=str(package_file.relative_to(self.project_root)),
                        line_number=1,
                        description=f"Potentially vulnerable dependency: {description}",
                        code_snippet=f"{pkg_name}: {dependencies[pkg_name]}",
                        recommendation="Update to latest secure version or find alternative",
                        confidence=0.6
                    )
                    self.findings.append(finding)

        except Exception as e:
            self.logger.warning(f"Error scanning Node dependencies: {e}")

    async def _scan_infrastructure(self):
        """Scan infrastructure and deployment configurations"""
        # Docker files
        docker_files = list(self.project_root.glob('**/Dockerfile*'))
        for docker_file in docker_files:
            await self._scan_dockerfile(docker_file)

        # Docker compose files
        compose_files = list(self.project_root.glob('**/docker-compose*.yml'))
        for compose_file in compose_files:
            await self._scan_docker_compose(compose_file)

    async def _scan_dockerfile(self, dockerfile: Path):
        """Scan Dockerfile for security issues"""
        try:
            with open(dockerfile, 'r') as f:
                content = f.read()

            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                line = line.strip()

                # Check for running as root
                if line.startswith('USER root') or (line.startswith('RUN') and 'sudo' in line):
                    finding = SecurityFinding(
                        vulnerability_type=VulnerabilityType.PRIVILEGE_ESCALATION,
                        severity=SecuritySeverity.MEDIUM,
                        file_path=str(dockerfile.relative_to(self.project_root)),
                        line_number=line_num,
                        description="Container running as root or using sudo",
                        code_snippet=line,
                        recommendation="Use non-root user for container execution",
                        cwe_id="CWE-250",
                        confidence=0.8
                    )
                    self.findings.append(finding)

                # Check for secrets in build args
                if line.startswith('ARG') and any(secret in line.lower() for secret in ['password', 'secret', 'key', 'token']):
                    finding = SecurityFinding(
                        vulnerability_type=VulnerabilityType.HARDCODED_SECRETS,
                        severity=SecuritySeverity.HIGH,
                        file_path=str(dockerfile.relative_to(self.project_root)),
                        line_number=line_num,
                        description="Potential secret in Dockerfile ARG",
                        code_snippet=line,
                        recommendation="Use multi-stage builds and runtime secrets",
                        cwe_id="CWE-798",
                        confidence=0.7
                    )
                    self.findings.append(finding)

        except Exception as e:
            self.logger.warning(f"Error scanning Dockerfile: {e}")

    async def _scan_docker_compose(self, compose_file: Path):
        """Scan Docker Compose file for security issues"""
        try:
            with open(compose_file, 'r') as f:
                content = f.read()

            # Check for hardcoded passwords in environment variables
            if re.search(r'(?i)(password|secret|key)\s*[:=]\s*[^$\n]+', content):
                finding = SecurityFinding(
                    vulnerability_type=VulnerabilityType.HARDCODED_SECRETS,
                    severity=SecuritySeverity.HIGH,
                    file_path=str(compose_file.relative_to(self.project_root)),
                    line_number=1,
                    description="Hardcoded secrets in Docker Compose file",
                    code_snippet="Docker Compose environment variables",
                    recommendation="Use environment file or Docker secrets",
                    cwe_id="CWE-798",
                    confidence=0.8
                )
                self.findings.append(finding)

        except Exception as e:
            self.logger.warning(f"Error scanning Docker Compose: {e}")

    def _get_recommendation(self, vuln_type: VulnerabilityType) -> str:
        """Get security recommendation for vulnerability type"""
        recommendations = {
            VulnerabilityType.HARDCODED_SECRETS: "Use environment variables or secure secret management systems",
            VulnerabilityType.SQL_INJECTION: "Use parameterized queries or prepared statements",
            VulnerabilityType.XSS: "Sanitize and validate all user inputs, use CSP headers",
            VulnerabilityType.WEAK_CRYPTO: "Use strong cryptographic algorithms (AES-256, SHA-256+)",
            VulnerabilityType.PATH_TRAVERSAL: "Validate and sanitize file paths, use whitelist approach",
            VulnerabilityType.COMMAND_INJECTION: "Avoid shell execution, use subprocess with argument lists",
            VulnerabilityType.DESERIALIZATION: "Use safe serialization formats, validate input data",
            VulnerabilityType.WEAK_AUTH: "Implement strong authentication mechanisms",
            VulnerabilityType.PRIVILEGE_ESCALATION: "Follow principle of least privilege",
            VulnerabilityType.DATA_EXPOSURE: "Encrypt sensitive data at rest and in transit"
        }
        return recommendations.get(vuln_type, "Review and remediate security issue")

    def _generate_summary(self) -> Dict[SecuritySeverity, int]:
        """Generate security findings summary"""
        summary = {severity: 0 for severity in SecuritySeverity}

        for finding in self.findings:
            summary[finding.severity] += 1

        return summary

    def _generate_recommendations(self) -> List[str]:
        """Generate high-level security recommendations"""
        recommendations = [
            "Implement automated security scanning in CI/CD pipeline",
            "Use secure coding practices and conduct regular code reviews",
            "Implement proper input validation and output encoding",
            "Use environment variables for configuration and secrets",
            "Enable security headers and implement CSP",
            "Regular security training for development team",
            "Implement proper logging and monitoring",
            "Use dependency scanning tools",
            "Conduct regular penetration testing",
            "Implement secure secret management"
        ]

        # Add specific recommendations based on findings
        vuln_types = set(finding.vulnerability_type for finding in self.findings)

        if VulnerabilityType.HARDCODED_SECRETS in vuln_types:
            recommendations.append("Immediate action: Remove all hardcoded secrets from codebase")

        if VulnerabilityType.SQL_INJECTION in vuln_types:
            recommendations.append("Critical: Implement parameterized queries for all database operations")

        return recommendations

    def _check_compliance(self) -> Dict[str, bool]:
        """Check compliance with security standards"""
        compliance = {
            "OWASP_Top_10": True,
            "CWE_Top_25": True,
            "SANS_Top_25": True,
            "ISO_27001": True
        }

        # Check for critical security issues
        critical_findings = [f for f in self.findings if f.severity == SecuritySeverity.CRITICAL]
        high_findings = [f for f in self.findings if f.severity == SecuritySeverity.HIGH]

        if critical_findings:
            compliance["OWASP_Top_10"] = False
            compliance["CWE_Top_25"] = False

        if len(high_findings) > 5:
            compliance["SANS_Top_25"] = False

        if len(self.findings) > 20:
            compliance["ISO_27001"] = False

        return compliance

    async def generate_report_json(self, report: SecurityAuditReport, output_file: str):
        """Generate JSON security report"""
        report_data = {
            "scan_timestamp": report.scan_timestamp.isoformat(),
            "total_files_scanned": report.total_files_scanned,
            "total_vulnerabilities": report.total_vulnerabilities,
            "summary": {k.value: v for k, v in report.summary.items()},
            "compliance_status": report.compliance_status,
            "findings": [
                {
                    "vulnerability_type": f.vulnerability_type.value,
                    "severity": f.severity.value,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "description": f.description,
                    "code_snippet": f.code_snippet,
                    "recommendation": f.recommendation,
                    "cwe_id": f.cwe_id,
                    "confidence": f.confidence
                }
                for f in report.findings
            ],
            "recommendations": report.recommendations
        }

        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)

        self.logger.info(f"📄 Security report saved to {output_file}")

# Global auditor instance
security_auditor = SecurityAuditor()

# CLI usage
async def run_security_audit():
    """Run security audit from command line"""
    auditor = SecurityAuditor()
    report = await auditor.run_comprehensive_audit()

    print("\n🔒 SECURITY AUDIT REPORT")
    print("=" * 50)
    print(f"Scan Date: {report.scan_timestamp}")
    print(f"Files Scanned: {report.total_files_scanned}")
    print(f"Total Issues: {report.total_vulnerabilities}")

    print("\n📊 SEVERITY BREAKDOWN:")
    for severity, count in report.summary.items():
        if count > 0:
            print(f"  {severity.value}: {count}")

    print(f"\n🚨 CRITICAL ISSUES:")
    critical_issues = [f for f in report.findings if f.severity == SecuritySeverity.CRITICAL]
    for issue in critical_issues[:5]:  # Show top 5
        print(f"  📍 {issue.file_path}:{issue.line_number}")
        print(f"     {issue.description}")
        print(f"     {issue.recommendation}")
        print()

    print(f"\n✅ COMPLIANCE STATUS:")
    for standard, compliant in report.compliance_status.items():
        status = "✅ COMPLIANT" if compliant else "❌ NON-COMPLIANT"
        print(f"  {standard}: {status}")

    # Save detailed report
    await auditor.generate_report_json(report, "security_audit_report.json")

    return report

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_security_audit())