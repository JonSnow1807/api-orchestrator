#!/usr/bin/env python3
"""
Specialized Security Agents - DevOps, Database, Infrastructure
Industry-leading specialized autonomous security capabilities
"""

import os
import re
import yaml
import subprocess
from typing import Dict, List, Any
from datetime import datetime


class DevOpsSecurityAgent:
    """Specialized agent for DevOps pipeline security"""

    def __init__(self):
        self.agent_id = "devops_security"
        self.capabilities = [
            "ci_cd_security_scan",
            "container_security_analysis",
            "infrastructure_as_code_audit",
            "pipeline_hardening",
            "secret_scanning",
            "dependency_vulnerability_scan",
        ]
        self.safe_mode = True

    async def execute_ci_cd_security_scan(
        self, parameters: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Comprehensive CI/CD pipeline security analysis"""

        print("🔧 Executing CI/CD Security Scan...")

        start_time = datetime.now()
        findings = []

        # Scan common CI/CD files
        ci_files = self._find_ci_cd_files()

        for file_path in ci_files:
            if os.path.exists(file_path):
                file_findings = await self._analyze_ci_cd_file(file_path)
                findings.extend(file_findings)

        # Container security analysis
        container_findings = await self._analyze_container_security()
        findings.extend(container_findings)

        # Environment security check
        env_findings = self._analyze_environment_security()
        findings.extend(env_findings)

        execution_time = (datetime.now() - start_time).total_seconds()

        result = {
            "agent": self.agent_id,
            "action": "ci_cd_security_scan",
            "status": "completed",
            "execution_time": execution_time,
            "findings_count": len(findings),
            "findings": findings,
            "security_score": self._calculate_devops_security_score(findings),
            "recommendations": self._generate_devops_recommendations(findings),
        }

        print(f"   ✅ CI/CD scan completed: {len(findings)} findings")
        return result

    async def execute_container_security_analysis(
        self, parameters: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Advanced container security analysis"""

        print("🐳 Executing Container Security Analysis...")

        start_time = datetime.now()
        findings = []

        # Analyze Dockerfiles
        dockerfile_findings = await self._analyze_dockerfiles()
        findings.extend(dockerfile_findings)

        # Analyze Kubernetes manifests
        k8s_findings = await self._analyze_kubernetes_manifests()
        findings.extend(k8s_findings)

        # Docker Compose analysis
        compose_findings = await self._analyze_docker_compose()
        findings.extend(compose_findings)

        execution_time = (datetime.now() - start_time).total_seconds()

        result = {
            "agent": self.agent_id,
            "action": "container_security_analysis",
            "status": "completed",
            "execution_time": execution_time,
            "container_findings": len(findings),
            "findings": findings,
            "container_security_score": self._calculate_container_security_score(
                findings
            ),
            "hardening_recommendations": self._generate_container_hardening(findings),
        }

        print(f"   ✅ Container analysis completed: {len(findings)} findings")
        return result

    async def execute_infrastructure_as_code_audit(
        self, parameters: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Infrastructure as Code security audit"""

        print("🏗️ Executing Infrastructure as Code Audit...")

        start_time = datetime.now()
        findings = []

        # Terraform analysis
        terraform_findings = await self._analyze_terraform_files()
        findings.extend(terraform_findings)

        # CloudFormation analysis
        cf_findings = await self._analyze_cloudformation_templates()
        findings.extend(cf_findings)

        # Ansible playbook analysis
        ansible_findings = await self._analyze_ansible_playbooks()
        findings.extend(ansible_findings)

        execution_time = (datetime.now() - start_time).total_seconds()

        result = {
            "agent": self.agent_id,
            "action": "infrastructure_as_code_audit",
            "status": "completed",
            "execution_time": execution_time,
            "iac_findings": len(findings),
            "findings": findings,
            "infrastructure_security_score": self._calculate_iac_security_score(
                findings
            ),
            "compliance_gaps": self._identify_iac_compliance_gaps(findings),
        }

        print(f"   ✅ IaC audit completed: {len(findings)} findings")
        return result

    def _find_ci_cd_files(self) -> List[str]:
        """Find CI/CD configuration files"""
        ci_files = []

        # Common CI/CD file patterns
        patterns = [
            ".github/workflows/*.yml",
            ".github/workflows/*.yaml",
            ".gitlab-ci.yml",
            "Jenkinsfile",
            ".travis.yml",
            "azure-pipelines.yml",
            "buildspec.yml",  # AWS CodeBuild
            ".circleci/config.yml",
        ]

        for pattern in patterns:
            if "*" in pattern:
                # Handle glob patterns
                import glob

                ci_files.extend(glob.glob(pattern))
            else:
                if os.path.exists(pattern):
                    ci_files.append(pattern)

        return ci_files

    async def _analyze_ci_cd_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze individual CI/CD file for security issues"""
        findings = []

        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Check for hardcoded secrets
            if re.search(r'password\s*[:=]\s*["\'][^"\']{8,}', content, re.IGNORECASE):
                findings.append(
                    {
                        "type": "hardcoded_secret",
                        "severity": "HIGH",
                        "file": file_path,
                        "issue": "Hardcoded password found in CI/CD configuration",
                        "recommendation": "Use encrypted secrets or environment variables",
                    }
                )

            # Check for API keys
            if re.search(
                r'(api_key|token)\s*[:=]\s*["\'][^"\']{20,}', content, re.IGNORECASE
            ):
                findings.append(
                    {
                        "type": "exposed_api_key",
                        "severity": "CRITICAL",
                        "file": file_path,
                        "issue": "API key exposed in CI/CD configuration",
                        "recommendation": "Move API keys to secure secret management",
                    }
                )

            # Check for insecure commands
            insecure_patterns = [
                r"curl.*http://",  # Unencrypted HTTP
                r"wget.*http://",
                r"sudo.*NOPASSWD",  # Passwordless sudo
                r"chmod\s+777",  # Overly permissive permissions
            ]

            for pattern in insecure_patterns:
                if re.search(pattern, content):
                    findings.append(
                        {
                            "type": "insecure_command",
                            "severity": "MEDIUM",
                            "file": file_path,
                            "issue": f"Insecure command pattern detected: {pattern}",
                            "recommendation": "Use secure alternatives and proper permissions",
                        }
                    )

            # Check for missing security steps
            if (
                "security" not in content.lower()
                and "vulnerability" not in content.lower()
            ):
                findings.append(
                    {
                        "type": "missing_security_step",
                        "severity": "MEDIUM",
                        "file": file_path,
                        "issue": "No security scanning steps detected in pipeline",
                        "recommendation": "Add security scanning and vulnerability assessment steps",
                    }
                )

        except Exception as e:
            findings.append(
                {
                    "type": "analysis_error",
                    "severity": "LOW",
                    "file": file_path,
                    "issue": f"Could not analyze file: {str(e)}",
                    "recommendation": "Manual review required",
                }
            )

        return findings

    async def _analyze_container_security(self) -> List[Dict[str, Any]]:
        """Analyze container security configurations"""
        findings = []

        # Look for Dockerfile
        if os.path.exists("Dockerfile"):
            findings.extend(await self._analyze_dockerfile("Dockerfile"))

        # Look for docker-compose files
        compose_files = [
            "docker-compose.yml",
            "docker-compose.yaml",
            "docker-compose.override.yml",
        ]
        for compose_file in compose_files:
            if os.path.exists(compose_file):
                findings.extend(await self._analyze_docker_compose_file(compose_file))

        return findings

    async def _analyze_dockerfile(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze Dockerfile for security issues"""
        findings = []

        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Check for running as root
            if "USER root" in content or "USER 0" in content:
                findings.append(
                    {
                        "type": "container_runs_as_root",
                        "severity": "HIGH",
                        "file": file_path,
                        "issue": "Container configured to run as root user",
                        "recommendation": "Create and use a non-root user",
                    }
                )

            # Check for missing USER instruction
            if "USER " not in content:
                findings.append(
                    {
                        "type": "missing_user_instruction",
                        "severity": "MEDIUM",
                        "file": file_path,
                        "issue": "No USER instruction found - container may run as root",
                        "recommendation": "Add USER instruction to run as non-root",
                    }
                )

            # Check for hardcoded secrets
            if re.search(r'(PASSWORD|SECRET|TOKEN|KEY)\s*=\s*["\'][^"\']+', content):
                findings.append(
                    {
                        "type": "hardcoded_secret_in_container",
                        "severity": "CRITICAL",
                        "file": file_path,
                        "issue": "Hardcoded secrets in Dockerfile",
                        "recommendation": "Use build arguments or runtime environment variables",
                    }
                )

            # Check for latest tag usage
            if re.search(r"FROM\s+[^:]+:latest", content):
                findings.append(
                    {
                        "type": "using_latest_tag",
                        "severity": "MEDIUM",
                        "file": file_path,
                        "issue": "Using 'latest' tag for base image",
                        "recommendation": "Pin to specific version tags for reproducibility",
                    }
                )

        except Exception as e:
            findings.append(
                {
                    "type": "dockerfile_analysis_error",
                    "severity": "LOW",
                    "file": file_path,
                    "issue": f"Could not analyze Dockerfile: {str(e)}",
                    "recommendation": "Manual review required",
                }
            )

        return findings

    async def _analyze_dockerfiles(self) -> List[Dict[str, Any]]:
        """Analyze all Dockerfiles in the project"""
        findings = []

        # Find all Dockerfiles
        import glob

        dockerfiles = glob.glob("**/Dockerfile*", recursive=True)

        for dockerfile in dockerfiles:
            findings.extend(await self._analyze_dockerfile(dockerfile))

        return findings

    async def _analyze_kubernetes_manifests(self) -> List[Dict[str, Any]]:
        """Analyze Kubernetes manifests for security issues"""
        findings = []

        # Find Kubernetes YAML files
        import glob

        k8s_files = []
        k8s_files.extend(glob.glob("k8s/**/*.yml", recursive=True))
        k8s_files.extend(glob.glob("k8s/**/*.yaml", recursive=True))
        k8s_files.extend(glob.glob("kubernetes/**/*.yml", recursive=True))
        k8s_files.extend(glob.glob("kubernetes/**/*.yaml", recursive=True))

        for k8s_file in k8s_files:
            try:
                with open(k8s_file, "r") as f:
                    content = f.read()

                # Parse YAML
                docs = yaml.safe_load_all(content)

                for doc in docs:
                    if doc and doc.get("kind"):
                        findings.extend(self._analyze_k8s_resource(doc, k8s_file))

            except Exception as e:
                findings.append(
                    {
                        "type": "k8s_analysis_error",
                        "severity": "LOW",
                        "file": k8s_file,
                        "issue": f"Could not analyze Kubernetes manifest: {str(e)}",
                        "recommendation": "Manual review required",
                    }
                )

        return findings

    def _analyze_k8s_resource(
        self, resource: Dict[str, Any], file_path: str
    ) -> List[Dict[str, Any]]:
        """Analyze individual Kubernetes resource"""
        findings = []

        kind = resource.get("kind", "")

        if kind in ["Pod", "Deployment", "DaemonSet", "StatefulSet"]:
            # Check security context
            spec = resource.get("spec", {})

            if kind == "Pod":
                containers = spec.get("containers", [])
            else:
                containers = (
                    spec.get("template", {}).get("spec", {}).get("containers", [])
                )

            for container in containers:
                # Check for privileged containers
                security_context = container.get("securityContext", {})
                if security_context.get("privileged"):
                    findings.append(
                        {
                            "type": "privileged_container",
                            "severity": "HIGH",
                            "file": file_path,
                            "issue": f"Container '{container.get('name', 'unknown')}' runs in privileged mode",
                            "recommendation": "Remove privileged flag unless absolutely necessary",
                        }
                    )

                # Check for root user
                if security_context.get("runAsUser") == 0:
                    findings.append(
                        {
                            "type": "container_runs_as_root",
                            "severity": "HIGH",
                            "file": file_path,
                            "issue": f"Container '{container.get('name', 'unknown')}' runs as root (UID 0)",
                            "recommendation": "Use non-root user ID",
                        }
                    )

        return findings

    async def _analyze_docker_compose(self) -> List[Dict[str, Any]]:
        """Analyze Docker Compose files"""
        findings = []

        compose_files = [
            "docker-compose.yml",
            "docker-compose.yaml",
            "docker-compose.override.yml",
        ]

        for compose_file in compose_files:
            if os.path.exists(compose_file):
                findings.extend(await self._analyze_docker_compose_file(compose_file))

        return findings

    async def _analyze_docker_compose_file(
        self, file_path: str
    ) -> List[Dict[str, Any]]:
        """Analyze individual Docker Compose file"""
        findings = []

        try:
            with open(file_path, "r") as f:
                content = f.read()

            compose_data = yaml.safe_load(content)
            services = compose_data.get("services", {})

            for service_name, service_config in services.items():
                # Check for privileged containers
                if service_config.get("privileged"):
                    findings.append(
                        {
                            "type": "privileged_service",
                            "severity": "HIGH",
                            "file": file_path,
                            "issue": f"Service '{service_name}' runs in privileged mode",
                            "recommendation": "Remove privileged flag unless absolutely necessary",
                        }
                    )

                # Check for host network mode
                if service_config.get("network_mode") == "host":
                    findings.append(
                        {
                            "type": "host_network_mode",
                            "severity": "MEDIUM",
                            "file": file_path,
                            "issue": f"Service '{service_name}' uses host network mode",
                            "recommendation": "Use bridge network for better isolation",
                        }
                    )

                # Check for exposed ports
                ports = service_config.get("ports", [])
                for port in ports:
                    if isinstance(port, str) and ":" in port:
                        host_port = port.split(":")[0]
                        if host_port in [
                            "22",
                            "3389",
                            "5432",
                            "3306",
                        ]:  # Common sensitive ports
                            findings.append(
                                {
                                    "type": "sensitive_port_exposed",
                                    "severity": "MEDIUM",
                                    "file": file_path,
                                    "issue": f"Service '{service_name}' exposes sensitive port {host_port}",
                                    "recommendation": "Ensure proper authentication and access controls",
                                }
                            )

        except Exception as e:
            findings.append(
                {
                    "type": "compose_analysis_error",
                    "severity": "LOW",
                    "file": file_path,
                    "issue": f"Could not analyze Docker Compose file: {str(e)}",
                    "recommendation": "Manual review required",
                }
            )

        return findings

    def _analyze_environment_security(self) -> List[Dict[str, Any]]:
        """Analyze environment configuration security"""
        findings = []

        # Check for .env files with secrets
        env_files = [".env", ".env.local", ".env.production", ".env.development"]

        for env_file in env_files:
            if os.path.exists(env_file):
                try:
                    with open(env_file, "r") as f:
                        f.read()

                    # Check if .env file is tracked in git
                    try:
                        result = subprocess.run(
                            ["git", "ls-files", env_file],
                            capture_output=True,
                            text=True,
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            findings.append(
                                {
                                    "type": "env_file_in_git",
                                    "severity": "HIGH",
                                    "file": env_file,
                                    "issue": "Environment file is tracked in git",
                                    "recommendation": "Add to .gitignore and remove from git history",
                                }
                            )
                    except Exception:
                        pass  # Git not available or not a git repo

                except Exception:
                    pass

        return findings

    async def _analyze_terraform_files(self) -> List[Dict[str, Any]]:
        """Analyze Terraform files for security issues"""
        findings = []

        import glob

        tf_files = glob.glob("**/*.tf", recursive=True)

        for tf_file in tf_files:
            try:
                with open(tf_file, "r") as f:
                    content = f.read()

                # Check for hardcoded secrets
                if re.search(
                    r'(password|secret|key)\s*=\s*"[^"]{8,}"', content, re.IGNORECASE
                ):
                    findings.append(
                        {
                            "type": "hardcoded_secret_terraform",
                            "severity": "HIGH",
                            "file": tf_file,
                            "issue": "Hardcoded secrets in Terraform configuration",
                            "recommendation": "Use Terraform variables or external secret management",
                        }
                    )

                # Check for public S3 buckets
                if (
                    "aws_s3_bucket_public_access_block" not in content
                    and "aws_s3_bucket" in content
                ):
                    findings.append(
                        {
                            "type": "missing_s3_public_access_block",
                            "severity": "MEDIUM",
                            "file": tf_file,
                            "issue": "S3 bucket without public access block configuration",
                            "recommendation": "Add aws_s3_bucket_public_access_block resource",
                        }
                    )

            except Exception as e:
                findings.append(
                    {
                        "type": "terraform_analysis_error",
                        "severity": "LOW",
                        "file": tf_file,
                        "issue": f"Could not analyze Terraform file: {str(e)}",
                        "recommendation": "Manual review required",
                    }
                )

        return findings

    async def _analyze_cloudformation_templates(self) -> List[Dict[str, Any]]:
        """Analyze CloudFormation templates"""
        findings = []

        import glob

        cf_files = []
        cf_files.extend(glob.glob("**/*.template", recursive=True))
        cf_files.extend(glob.glob("**/*cloudformation*.yml", recursive=True))
        cf_files.extend(glob.glob("**/*cloudformation*.yaml", recursive=True))

        for cf_file in cf_files:
            try:
                with open(cf_file, "r") as f:
                    content = f.read()

                cf_data = yaml.safe_load(content)

                # Check for hardcoded secrets in parameters
                parameters = cf_data.get("Parameters", {})
                for param_name, param_config in parameters.items():
                    if (
                        param_config.get("NoEcho") != True
                        and "password" in param_name.lower()
                    ):
                        findings.append(
                            {
                                "type": "password_parameter_not_hidden",
                                "severity": "MEDIUM",
                                "file": cf_file,
                                "issue": f"Password parameter '{param_name}' not marked as NoEcho",
                                "recommendation": "Set NoEcho: true for sensitive parameters",
                            }
                        )

            except Exception as e:
                findings.append(
                    {
                        "type": "cloudformation_analysis_error",
                        "severity": "LOW",
                        "file": cf_file,
                        "issue": f"Could not analyze CloudFormation template: {str(e)}",
                        "recommendation": "Manual review required",
                    }
                )

        return findings

    async def _analyze_ansible_playbooks(self) -> List[Dict[str, Any]]:
        """Analyze Ansible playbooks for security issues"""
        findings = []

        import glob

        ansible_files = []
        ansible_files.extend(glob.glob("**/*playbook*.yml", recursive=True))
        ansible_files.extend(glob.glob("**/*playbook*.yaml", recursive=True))
        ansible_files.extend(glob.glob("**/playbooks/**/*.yml", recursive=True))
        ansible_files.extend(glob.glob("**/playbooks/**/*.yaml", recursive=True))

        for ansible_file in ansible_files:
            try:
                with open(ansible_file, "r") as f:
                    content = f.read()

                # Check for hardcoded passwords
                if re.search(r'password:\s*["\'][^"\']{8,}', content):
                    findings.append(
                        {
                            "type": "hardcoded_password_ansible",
                            "severity": "HIGH",
                            "file": ansible_file,
                            "issue": "Hardcoded password in Ansible playbook",
                            "recommendation": "Use Ansible Vault for sensitive data",
                        }
                    )

                # Check for become without proper controls
                if "become: yes" in content or "become: true" in content:
                    if "become_user:" not in content:
                        findings.append(
                            {
                                "type": "unrestricted_privilege_escalation",
                                "severity": "MEDIUM",
                                "file": ansible_file,
                                "issue": "Privilege escalation without specifying target user",
                                "recommendation": "Specify become_user for controlled privilege escalation",
                            }
                        )

            except Exception as e:
                findings.append(
                    {
                        "type": "ansible_analysis_error",
                        "severity": "LOW",
                        "file": ansible_file,
                        "issue": f"Could not analyze Ansible playbook: {str(e)}",
                        "recommendation": "Manual review required",
                    }
                )

        return findings

    def _calculate_devops_security_score(
        self, findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate DevOps security score"""
        total_findings = len(findings)
        critical_findings = len(
            [f for f in findings if f.get("severity") == "CRITICAL"]
        )
        high_findings = len([f for f in findings if f.get("severity") == "HIGH"])

        # Calculate score (100 - penalty for findings)
        penalty = (
            (critical_findings * 20)
            + (high_findings * 10)
            + ((total_findings - critical_findings - high_findings) * 5)
        )
        score = max(0, 100 - penalty)

        return {
            "overall_score": score,
            "total_findings": total_findings,
            "critical_findings": critical_findings,
            "high_findings": high_findings,
            "risk_level": "HIGH" if score < 50 else "MEDIUM" if score < 80 else "LOW",
        }

    def _calculate_container_security_score(
        self, findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate container security score"""
        container_findings = [
            f for f in findings if "container" in f.get("type", "").lower()
        ]
        return self._calculate_devops_security_score(container_findings)

    def _calculate_iac_security_score(
        self, findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate Infrastructure as Code security score"""
        iac_findings = [
            f
            for f in findings
            if any(
                term in f.get("type", "").lower()
                for term in ["terraform", "cloudformation", "ansible"]
            )
        ]
        return self._calculate_devops_security_score(iac_findings)

    def _generate_devops_recommendations(
        self, findings: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate DevOps security recommendations"""
        recommendations = []

        finding_types = [f.get("type") for f in findings]

        if "hardcoded_secret" in finding_types:
            recommendations.append(
                "Implement proper secret management (HashiCorp Vault, AWS Secrets Manager)"
            )

        if "missing_security_step" in finding_types:
            recommendations.append("Add automated security scanning to CI/CD pipelines")

        if "privileged_container" in finding_types:
            recommendations.append(
                "Implement least-privilege containers with proper security contexts"
            )

        if "env_file_in_git" in finding_types:
            recommendations.append(
                "Remove environment files from version control and use proper secret injection"
            )

        recommendations.append(
            "Implement continuous security monitoring for DevOps pipelines"
        )

        return recommendations

    def _generate_container_hardening(
        self, findings: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate container hardening recommendations"""
        recommendations = []

        finding_types = [f.get("type") for f in findings]

        if "container_runs_as_root" in finding_types:
            recommendations.append("Create and use non-root users in all containers")

        if "using_latest_tag" in finding_types:
            recommendations.append("Pin container images to specific version tags")

        if "privileged_service" in finding_types:
            recommendations.append(
                "Remove privileged flags and use specific capabilities instead"
            )

        recommendations.append("Implement container image vulnerability scanning")
        recommendations.append("Use multi-stage builds to reduce attack surface")

        return recommendations

    def _identify_iac_compliance_gaps(
        self, findings: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify Infrastructure as Code compliance gaps"""
        gaps = []

        finding_types = [f.get("type") for f in findings]

        if "missing_s3_public_access_block" in finding_types:
            gaps.append("S3 bucket public access controls not configured")

        if "password_parameter_not_hidden" in finding_types:
            gaps.append("Sensitive parameters not properly protected in templates")

        if "hardcoded_secret_terraform" in finding_types:
            gaps.append("Secrets management not implemented in Infrastructure as Code")

        return gaps


class DatabaseSecurityAgent:
    """Specialized agent for database security analysis"""

    def __init__(self):
        self.agent_id = "database_security"
        self.capabilities = [
            "sql_injection_analysis",
            "database_configuration_audit",
            "query_security_review",
            "database_access_control_audit",
            "data_encryption_analysis",
            "database_privilege_review",
        ]
        self.safe_mode = True

    async def execute_sql_injection_analysis(
        self, parameters: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Advanced SQL injection vulnerability analysis"""

        print("🗄️ Executing SQL Injection Analysis...")

        start_time = datetime.now()
        findings = []

        # Analyze SQL patterns in code
        sql_findings = await self._analyze_sql_patterns()
        findings.extend(sql_findings)

        # Analyze ORM usage
        orm_findings = await self._analyze_orm_security()
        findings.extend(orm_findings)

        # Database configuration analysis
        db_config_findings = await self._analyze_database_configurations()
        findings.extend(db_config_findings)

        execution_time = (datetime.now() - start_time).total_seconds()

        result = {
            "agent": self.agent_id,
            "action": "sql_injection_analysis",
            "status": "completed",
            "execution_time": execution_time,
            "sql_vulnerabilities": len(
                [f for f in findings if f.get("type", "").startswith("sql_")]
            ),
            "orm_issues": len(
                [f for f in findings if f.get("type", "").startswith("orm_")]
            ),
            "config_issues": len(
                [f for f in findings if f.get("type", "").startswith("db_config_")]
            ),
            "findings": findings,
            "risk_score": self._calculate_database_risk_score(findings),
            "remediation_plan": self._generate_database_remediation_plan(findings),
        }

        print(f"   ✅ SQL injection analysis completed: {len(findings)} findings")
        return result

    async def execute_database_configuration_audit(
        self, parameters: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Comprehensive database configuration security audit"""

        print("🔐 Executing Database Configuration Audit...")

        start_time = datetime.now()
        findings = []

        # Database connection security
        connection_findings = await self._analyze_database_connections()
        findings.extend(connection_findings)

        # Database schema security
        schema_findings = await self._analyze_database_schemas()
        findings.extend(schema_findings)

        # Access control analysis
        access_findings = await self._analyze_database_access_controls()
        findings.extend(access_findings)

        execution_time = (datetime.now() - start_time).total_seconds()

        result = {
            "agent": self.agent_id,
            "action": "database_configuration_audit",
            "status": "completed",
            "execution_time": execution_time,
            "connection_issues": len(
                [f for f in findings if "connection" in f.get("type", "")]
            ),
            "schema_issues": len(
                [f for f in findings if "schema" in f.get("type", "")]
            ),
            "access_control_issues": len(
                [f for f in findings if "access" in f.get("type", "")]
            ),
            "findings": findings,
            "security_posture": self._assess_database_security_posture(findings),
            "compliance_gaps": self._identify_database_compliance_gaps(findings),
        }

        print(f"   ✅ Database configuration audit completed: {len(findings)} findings")
        return result

    async def _analyze_sql_patterns(self) -> List[Dict[str, Any]]:
        """Analyze SQL patterns for injection vulnerabilities"""
        findings = []

        # Find Python files with SQL
        import glob

        python_files = glob.glob("**/*.py", recursive=True)

        for py_file in python_files:
            try:
                with open(py_file, "r") as f:
                    content = f.read()

                # Dangerous SQL patterns
                dangerous_patterns = [
                    # String formatting in SQL
                    {
                        "pattern": r'(SELECT|INSERT|UPDATE|DELETE).*["\'][^"\']*%s[^"\']*["\']',
                        "type": "sql_string_formatting",
                        "severity": "HIGH",
                        "description": "SQL query uses string formatting (%s) - potential injection risk",
                    },
                    # F-string in SQL
                    {
                        "pattern": r'f["\'][^"\']*(?:SELECT|INSERT|UPDATE|DELETE)[^"\']*\{[^}]+\}',
                        "type": "sql_fstring_injection",
                        "severity": "CRITICAL",
                        "description": "SQL query uses f-string with variables - high injection risk",
                    },
                    # String concatenation in SQL
                    {
                        "pattern": r'(SELECT|INSERT|UPDATE|DELETE)[^"\']*["\'][^"\']*\+[^"\']*["\']',
                        "type": "sql_string_concatenation",
                        "severity": "HIGH",
                        "description": "SQL query uses string concatenation - potential injection risk",
                    },
                    # .format() in SQL
                    {
                        "pattern": r'["\'][^"\']*(?:SELECT|INSERT|UPDATE|DELETE)[^"\']*["\']\.format\(',
                        "type": "sql_format_method",
                        "severity": "HIGH",
                        "description": "SQL query uses .format() method - potential injection risk",
                    },
                ]

                for pattern_info in dangerous_patterns:
                    if re.search(pattern_info["pattern"], content, re.IGNORECASE):
                        findings.append(
                            {
                                "type": pattern_info["type"],
                                "severity": pattern_info["severity"],
                                "file": py_file,
                                "issue": pattern_info["description"],
                                "recommendation": "Use parameterized queries or prepared statements",
                            }
                        )

                # Check for execute() with string concatenation
                if re.search(r"\.execute\([^)]*\+[^)]*\)", content):
                    findings.append(
                        {
                            "type": "sql_execute_concatenation",
                            "severity": "HIGH",
                            "file": py_file,
                            "issue": "Database execute() method uses string concatenation",
                            "recommendation": "Use parameterized queries with execute(query, params)",
                        }
                    )

            except Exception:
                continue

        return findings

    async def _analyze_orm_security(self) -> List[Dict[str, Any]]:
        """Analyze ORM usage for security issues"""
        findings = []

        import glob

        python_files = glob.glob("**/*.py", recursive=True)

        for py_file in python_files:
            try:
                with open(py_file, "r") as f:
                    content = f.read()

                # SQLAlchemy raw SQL
                if re.search(r"text\([^)]*\+[^)]*\)", content):
                    findings.append(
                        {
                            "type": "orm_raw_sql_concatenation",
                            "severity": "HIGH",
                            "file": py_file,
                            "issue": "SQLAlchemy text() with string concatenation",
                            "recommendation": "Use bound parameters in text() queries",
                        }
                    )

                # Django raw queries
                if re.search(r"\.raw\([^)]*%[^)]*\)", content):
                    findings.append(
                        {
                            "type": "orm_django_raw_formatting",
                            "severity": "HIGH",
                            "file": py_file,
                            "issue": "Django raw() query with string formatting",
                            "recommendation": "Use parameterized raw queries",
                        }
                    )

                # Missing query filtering
                if re.search(r"\.filter\(\)\.delete\(\)", content):
                    findings.append(
                        {
                            "type": "orm_unfiltered_delete",
                            "severity": "CRITICAL",
                            "file": py_file,
                            "issue": "Unfiltered delete operation - could delete all records",
                            "recommendation": "Add proper filtering before delete operations",
                        }
                    )

            except Exception:
                continue

        return findings

    async def _analyze_database_configurations(self) -> List[Dict[str, Any]]:
        """Analyze database configuration files"""
        findings = []

        # Database configuration files
        config_files = [
            "settings.py",  # Django
            "config.py",  # Flask
            "database.yml",  # Rails
            "knexfile.js",  # Node.js Knex
            ".env",  # Environment variables
            "docker-compose.yml",  # Docker database configs
        ]

        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, "r") as f:
                        content = f.read()

                    # Hardcoded database credentials
                    if re.search(
                        r'(DATABASE_PASSWORD|DB_PASS)\s*=\s*["\'][^"\']{1,}["\']',
                        content,
                    ):
                        findings.append(
                            {
                                "type": "db_config_hardcoded_password",
                                "severity": "CRITICAL",
                                "file": config_file,
                                "issue": "Hardcoded database password in configuration",
                                "recommendation": "Use environment variables for database credentials",
                            }
                        )

                    # Insecure database host
                    if re.search(
                        r'(DATABASE_HOST|DB_HOST)\s*=\s*["\']0\.0\.0\.0["\']', content
                    ):
                        findings.append(
                            {
                                "type": "db_config_insecure_host",
                                "severity": "MEDIUM",
                                "file": config_file,
                                "issue": "Database configured to listen on all interfaces",
                                "recommendation": "Bind database to specific network interface",
                            }
                        )

                    # Debugging enabled with database access
                    if "DEBUG = True" in content and "DATABASE" in content:
                        findings.append(
                            {
                                "type": "db_config_debug_enabled",
                                "severity": "MEDIUM",
                                "file": config_file,
                                "issue": "Debug mode enabled with database configuration",
                                "recommendation": "Disable debug mode in production",
                            }
                        )

                except Exception:
                    continue

        return findings

    async def _analyze_database_connections(self) -> List[Dict[str, Any]]:
        """Analyze database connection security"""
        findings = []

        # Look for database connection patterns
        import glob

        code_files = glob.glob("**/*.py", recursive=True)

        for code_file in code_files:
            try:
                with open(code_file, "r") as f:
                    content = f.read()

                # Unencrypted database connections
                if re.search(r"(mysql|postgresql|postgres)://[^@]*@[^/]*/", content):
                    findings.append(
                        {
                            "type": "db_connection_unencrypted",
                            "severity": "HIGH",
                            "file": code_file,
                            "issue": "Database connection string without SSL/TLS",
                            "recommendation": "Use encrypted database connections (SSL/TLS)",
                        }
                    )

                # Connection without timeout
                if "connect(" in content and "timeout" not in content:
                    findings.append(
                        {
                            "type": "db_connection_no_timeout",
                            "severity": "MEDIUM",
                            "file": code_file,
                            "issue": "Database connection without timeout configuration",
                            "recommendation": "Set appropriate connection and query timeouts",
                        }
                    )

            except Exception:
                continue

        return findings

    async def _analyze_database_schemas(self) -> List[Dict[str, Any]]:
        """Analyze database schema security"""
        findings = []

        # Look for migration files and schema definitions
        import glob

        migration_files = []
        migration_files.extend(glob.glob("**/migrations/**/*.py", recursive=True))
        migration_files.extend(glob.glob("**/migrate/**/*.sql", recursive=True))
        migration_files.extend(glob.glob("**/schema/**/*.sql", recursive=True))

        for migration_file in migration_files:
            try:
                with open(migration_file, "r") as f:
                    content = f.read()

                # Overly permissive table creation
                if re.search(r"GRANT ALL", content, re.IGNORECASE):
                    findings.append(
                        {
                            "type": "db_schema_overly_permissive",
                            "severity": "HIGH",
                            "file": migration_file,
                            "issue": "Database schema grants excessive permissions",
                            "recommendation": "Follow principle of least privilege for database permissions",
                        }
                    )

                # Missing indexes on sensitive columns
                if (
                    re.search(r"email.*VARCHAR", content, re.IGNORECASE)
                    and "INDEX" not in content.upper()
                ):
                    findings.append(
                        {
                            "type": "db_schema_missing_index",
                            "severity": "LOW",
                            "file": migration_file,
                            "issue": "Email column without index - performance and security concern",
                            "recommendation": "Add indexes on searchable sensitive columns",
                        }
                    )

            except Exception:
                continue

        return findings

    async def _analyze_database_access_controls(self) -> List[Dict[str, Any]]:
        """Analyze database access control patterns"""
        findings = []

        # Look for access control patterns in code
        import glob

        code_files = glob.glob("**/*.py", recursive=True)

        for code_file in code_files:
            try:
                with open(code_file, "r") as f:
                    content = f.read()

                # Direct database access without authorization
                if (
                    re.search(r"\.objects\.all\(\)", content)
                    and "permission" not in content.lower()
                ):
                    findings.append(
                        {
                            "type": "db_access_uncontrolled_query",
                            "severity": "MEDIUM",
                            "file": code_file,
                            "issue": "Database query without access control checks",
                            "recommendation": "Implement proper authorization checks before database access",
                        }
                    )

                # Admin-level database operations
                if re.search(r"\.filter\(\)\.delete\(\)", content):
                    findings.append(
                        {
                            "type": "db_access_bulk_delete",
                            "severity": "HIGH",
                            "file": code_file,
                            "issue": "Bulk delete operation without proper safeguards",
                            "recommendation": "Add confirmation and audit logging for bulk operations",
                        }
                    )

            except Exception:
                continue

        return findings

    def _calculate_database_risk_score(
        self, findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate database security risk score"""
        critical_count = len([f for f in findings if f.get("severity") == "CRITICAL"])
        high_count = len([f for f in findings if f.get("severity") == "HIGH"])
        medium_count = len([f for f in findings if f.get("severity") == "MEDIUM"])

        # Risk calculation
        risk_score = (critical_count * 25) + (high_count * 15) + (medium_count * 5)
        security_score = max(0, 100 - risk_score)

        return {
            "security_score": security_score,
            "risk_level": "CRITICAL"
            if security_score < 40
            else "HIGH"
            if security_score < 70
            else "MEDIUM"
            if security_score < 90
            else "LOW",
            "total_findings": len(findings),
            "critical_findings": critical_count,
            "high_findings": high_count,
            "medium_findings": medium_count,
        }

    def _generate_database_remediation_plan(
        self, findings: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate database security remediation plan"""
        plan = []

        finding_types = [f.get("type") for f in findings]

        if any("sql_injection" in ft for ft in finding_types):
            plan.append("Implement parameterized queries and prepared statements")

        if any("hardcoded" in ft for ft in finding_types):
            plan.append("Move database credentials to secure configuration management")

        if any("unencrypted" in ft for ft in finding_types):
            plan.append("Enable SSL/TLS encryption for all database connections")

        if any("access" in ft for ft in finding_types):
            plan.append("Implement proper database access controls and authorization")

        plan.append(
            "Conduct regular database security audits and vulnerability assessments"
        )

        return plan

    def _assess_database_security_posture(
        self, findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess overall database security posture"""
        risk_score = self._calculate_database_risk_score(findings)

        posture = {
            "overall_rating": risk_score["risk_level"],
            "security_score": risk_score["security_score"],
            "key_strengths": [],
            "critical_weaknesses": [],
            "improvement_areas": [],
        }

        # Analyze findings to identify patterns
        finding_types = [f.get("type") for f in findings]

        if not any("sql_injection" in ft for ft in finding_types):
            posture["key_strengths"].append(
                "No obvious SQL injection vulnerabilities detected"
            )

        if any("hardcoded" in ft for ft in finding_types):
            posture["critical_weaknesses"].append(
                "Hardcoded database credentials present"
            )

        if any("unencrypted" in ft for ft in finding_types):
            posture["improvement_areas"].append("Database connection encryption")

        return posture

    def _identify_database_compliance_gaps(
        self, findings: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify database compliance gaps"""
        gaps = []

        finding_types = [f.get("type") for f in findings]

        if any("hardcoded" in ft for ft in finding_types):
            gaps.append("PCI-DSS: Credentials not properly protected")

        if any("unencrypted" in ft for ft in finding_types):
            gaps.append("GDPR/HIPAA: Data transmission not encrypted")

        if any("access" in ft for ft in finding_types):
            gaps.append("SOC2: Access controls not properly implemented")

        return gaps
