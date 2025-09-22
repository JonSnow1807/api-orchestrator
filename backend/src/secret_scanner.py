"""
Secret Scanner with Vault Integration - Enterprise Security
Detect exposed secrets and integrate with secret management systems
"""

import re
import hashlib
import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass

# Vault integrations
try:
    import hvac  # HashiCorp Vault

    HASHICORP_VAULT_AVAILABLE = True
except ImportError:
    HASHICORP_VAULT_AVAILABLE = False

try:
    import boto3  # AWS Secrets Manager

    AWS_SECRETS_AVAILABLE = True
except ImportError:
    AWS_SECRETS_AVAILABLE = False

try:
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential

    AZURE_KEYVAULT_AVAILABLE = True
except ImportError:
    AZURE_KEYVAULT_AVAILABLE = False


class SecretType(Enum):
    """Types of secrets to detect"""

    API_KEY = "api_key"
    AWS_ACCESS_KEY = "aws_access_key"
    AWS_SECRET_KEY = "aws_secret_key"
    GITHUB_TOKEN = "github_token"
    GITLAB_TOKEN = "gitlab_token"
    SLACK_TOKEN = "slack_token"
    DATABASE_URL = "database_url"
    PRIVATE_KEY = "private_key"
    JWT_SECRET = "jwt_secret"
    OAUTH_TOKEN = "oauth_token"
    STRIPE_KEY = "stripe_key"
    SENDGRID_KEY = "sendgrid_key"
    TWILIO_AUTH = "twilio_auth"
    GOOGLE_API_KEY = "google_api_key"
    AZURE_KEY = "azure_key"
    CUSTOM = "custom"


class SecretSeverity(Enum):
    """Severity levels for detected secrets"""

    CRITICAL = "critical"  # Production keys, database passwords
    HIGH = "high"  # API keys with write access
    MEDIUM = "medium"  # API keys with read access
    LOW = "low"  # Development keys, expired tokens


class VaultProvider(Enum):
    """Supported secret vault providers"""

    HASHICORP = "hashicorp_vault"
    AWS_SECRETS_MANAGER = "aws_secrets_manager"
    AZURE_KEYVAULT = "azure_keyvault"
    GOOGLE_SECRET_MANAGER = "google_secret_manager"
    KUBERNETES_SECRETS = "kubernetes_secrets"
    CUSTOM = "custom"


@dataclass
class SecretPattern:
    """Pattern for detecting secrets"""

    name: str
    type: SecretType
    pattern: str
    severity: SecretSeverity
    description: str
    entropy_threshold: float = 3.5
    min_length: int = 10


class DetectedSecret(BaseModel):
    """Detected secret information"""

    id: str = Field(
        default_factory=lambda: hashlib.sha256(
            str(datetime.now()).encode()
        ).hexdigest()[:16]
    )
    type: SecretType
    severity: SecretSeverity
    value_hash: str  # SHA256 hash of the secret
    masked_value: str  # Partially masked for display
    location: Dict[str, Any]  # file, line, column, context
    pattern_matched: str
    confidence: float  # 0-1 confidence score
    detected_at: datetime = Field(default_factory=datetime.now)
    false_positive: bool = False
    remediation_status: str = "pending"  # pending, ignored, fixed, vaulted


class SecretScanResult(BaseModel):
    """Results of a secret scan"""

    scan_id: str
    workspace_id: str
    scan_type: str  # full, incremental, realtime
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_files_scanned: int = 0
    total_secrets_found: int = 0
    secrets_by_severity: Dict[str, int] = {}
    secrets_by_type: Dict[str, int] = {}
    detected_secrets: List[DetectedSecret] = []
    scan_errors: List[str] = []
    recommendations: List[str] = []


class VaultConfig(BaseModel):
    """Configuration for vault integration"""

    provider: VaultProvider
    connection_string: str
    auth_method: str  # token, userpass, aws, azure, kubernetes
    namespace: Optional[str] = None
    mount_point: str = "secret"
    credentials: Dict[str, Any] = {}
    auto_rotate: bool = False
    rotation_interval_days: int = 90


class SecretScanner:
    """Advanced secret scanner with vault integration"""

    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.custom_patterns: List[SecretPattern] = []
        self.whitelist: Set[str] = set()
        self.scan_history: List[SecretScanResult] = []
        self.vault_configs: Dict[str, VaultConfig] = {}
        self.vault_clients: Dict[str, Any] = {}

    def _initialize_patterns(self) -> List[SecretPattern]:
        """Initialize default secret detection patterns"""
        return [
            # AWS
            SecretPattern(
                name="AWS Access Key",
                type=SecretType.AWS_ACCESS_KEY,
                pattern=r"(?:AKIA|A3T|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
                severity=SecretSeverity.CRITICAL,
                description="AWS Access Key ID",
            ),
            SecretPattern(
                name="AWS Secret Key",
                type=SecretType.AWS_SECRET_KEY,
                pattern=r"(?i)aws[_\-\s]?(?:secret|sec)[_\-\s]?(?:access[_\-\s]?)?key[_\-\s]?['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
                severity=SecretSeverity.CRITICAL,
                description="AWS Secret Access Key",
            ),
            # GitHub
            SecretPattern(
                name="GitHub Personal Access Token",
                type=SecretType.GITHUB_TOKEN,
                pattern=r"ghp_[A-Za-z0-9]{36}",
                severity=SecretSeverity.HIGH,
                description="GitHub Personal Access Token",
            ),
            SecretPattern(
                name="GitHub OAuth Token",
                type=SecretType.GITHUB_TOKEN,
                pattern=r"gho_[A-Za-z0-9]{36}",
                severity=SecretSeverity.HIGH,
                description="GitHub OAuth Access Token",
            ),
            # API Keys
            SecretPattern(
                name="Generic API Key",
                type=SecretType.API_KEY,
                pattern=r"(?i)(?:api[_\-\s]?key|apikey)[_\-\s]?['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{32,})['\"]?",
                severity=SecretSeverity.MEDIUM,
                description="Generic API Key",
                entropy_threshold=3.0,
            ),
            # Stripe
            SecretPattern(
                name="Stripe Secret Key",
                type=SecretType.STRIPE_KEY,
                pattern=r"sk_(?:test|live)_[A-Za-z0-9]{24,}",
                severity=SecretSeverity.CRITICAL,
                description="Stripe Secret Key",
            ),
            SecretPattern(
                name="Stripe Restricted Key",
                type=SecretType.STRIPE_KEY,
                pattern=r"rk_(?:test|live)_[A-Za-z0-9]{24,}",
                severity=SecretSeverity.HIGH,
                description="Stripe Restricted Key",
            ),
            # Database URLs
            SecretPattern(
                name="PostgreSQL URL",
                type=SecretType.DATABASE_URL,
                pattern=r"postgres(?:ql)?:\/\/[^:]+:[^@]+@[^\/]+\/\w+",
                severity=SecretSeverity.CRITICAL,
                description="PostgreSQL Connection String",
            ),
            SecretPattern(
                name="MySQL URL",
                type=SecretType.DATABASE_URL,
                pattern=r"mysql:\/\/[^:]+:[^@]+@[^\/]+\/\w+",
                severity=SecretSeverity.CRITICAL,
                description="MySQL Connection String",
            ),
            SecretPattern(
                name="MongoDB URL",
                type=SecretType.DATABASE_URL,
                pattern=r"mongodb(?:\+srv)?:\/\/[^:]+:[^@]+@[^\/]+",
                severity=SecretSeverity.CRITICAL,
                description="MongoDB Connection String",
            ),
            # Private Keys
            SecretPattern(
                name="RSA Private Key",
                type=SecretType.PRIVATE_KEY,
                pattern=r"-----BEGIN (?:RSA|EC|DSA|OPENSSH) PRIVATE KEY-----",
                severity=SecretSeverity.CRITICAL,
                description="Private Cryptographic Key",
            ),
            # JWT
            SecretPattern(
                name="JWT Token",
                type=SecretType.JWT_SECRET,
                pattern=r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
                severity=SecretSeverity.HIGH,
                description="JSON Web Token",
            ),
            # Slack
            SecretPattern(
                name="Slack Token",
                type=SecretType.SLACK_TOKEN,
                pattern=r"xox[baprs]-[A-Za-z0-9]{10,48}",
                severity=SecretSeverity.MEDIUM,
                description="Slack API Token",
            ),
            # Google
            SecretPattern(
                name="Google API Key",
                type=SecretType.GOOGLE_API_KEY,
                pattern=r"AIza[A-Za-z0-9_-]{35}",
                severity=SecretSeverity.HIGH,
                description="Google API Key",
            ),
            # SendGrid
            SecretPattern(
                name="SendGrid API Key",
                type=SecretType.SENDGRID_KEY,
                pattern=r"SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}",
                severity=SecretSeverity.HIGH,
                description="SendGrid API Key",
            ),
            # Twilio
            SecretPattern(
                name="Twilio Auth Token",
                type=SecretType.TWILIO_AUTH,
                pattern=r"(?i)twilio[_\-\s]?(?:auth[_\-\s]?)?token[_\-\s]?['\"]?\s*[:=]\s*['\"]?([A-Fa-f0-9]{32})['\"]?",
                severity=SecretSeverity.HIGH,
                description="Twilio Auth Token",
            ),
        ]

    async def scan_content(
        self, content: str, file_path: str = "unknown", workspace_id: str = "default"
    ) -> SecretScanResult:
        """Scan content for secrets"""

        scan_result = SecretScanResult(
            scan_id=hashlib.sha256(
                f"{workspace_id}{datetime.now()}".encode()
            ).hexdigest()[:16],
            workspace_id=workspace_id,
            scan_type="content",
            started_at=datetime.now(),
        )

        # Scan with each pattern
        for pattern in self.patterns + self.custom_patterns:
            matches = re.finditer(
                pattern.pattern, content, re.MULTILINE | re.IGNORECASE
            )

            for match in matches:
                secret_value = match.group(0)

                # Check whitelist
                if self._is_whitelisted(secret_value):
                    continue

                # Check entropy
                if not self._check_entropy(secret_value, pattern.entropy_threshold):
                    continue

                # Check length
                if len(secret_value) < pattern.min_length:
                    continue

                # Create detected secret
                detected = DetectedSecret(
                    type=pattern.type,
                    severity=pattern.severity,
                    value_hash=hashlib.sha256(secret_value.encode()).hexdigest(),
                    masked_value=self._mask_secret(secret_value),
                    location={
                        "file": file_path,
                        "line": content[: match.start()].count("\n") + 1,
                        "column": match.start() - content.rfind("\n", 0, match.start()),
                        "context": content[
                            max(0, match.start() - 50) : min(
                                len(content), match.end() + 50
                            )
                        ],
                    },
                    pattern_matched=pattern.name,
                    confidence=self._calculate_confidence(secret_value, pattern),
                )

                scan_result.detected_secrets.append(detected)
                scan_result.total_secrets_found += 1

                # Update severity counts
                severity_key = pattern.severity.value
                scan_result.secrets_by_severity[severity_key] = (
                    scan_result.secrets_by_severity.get(severity_key, 0) + 1
                )

                # Update type counts
                type_key = pattern.type.value
                scan_result.secrets_by_type[type_key] = (
                    scan_result.secrets_by_type.get(type_key, 0) + 1
                )

        scan_result.completed_at = datetime.now()
        scan_result.total_files_scanned = 1

        # Generate recommendations
        scan_result.recommendations = self._generate_recommendations(scan_result)

        # Store scan history
        self.scan_history.append(scan_result)

        return scan_result

    async def scan_workspace(
        self,
        workspace_path: str,
        workspace_id: str,
        file_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
    ) -> SecretScanResult:
        """Scan entire workspace for secrets"""

        import os
        import fnmatch

        scan_result = SecretScanResult(
            scan_id=hashlib.sha256(
                f"{workspace_id}{datetime.now()}".encode()
            ).hexdigest()[:16],
            workspace_id=workspace_id,
            scan_type="full",
            started_at=datetime.now(),
        )

        # Default patterns
        if not file_patterns:
            file_patterns = ["*"]

        if not exclude_patterns:
            exclude_patterns = [
                "*.pyc",
                "__pycache__",
                ".git",
                "node_modules",
                ".env.example",
            ]

        # Walk through workspace
        for root, dirs, files in os.walk(workspace_path):
            # Filter directories
            dirs[:] = [
                d
                for d in dirs
                if not any(fnmatch.fnmatch(d, p) for p in exclude_patterns)
            ]

            for file in files:
                # Check if file matches patterns
                if not any(fnmatch.fnmatch(file, p) for p in file_patterns):
                    continue

                # Skip excluded patterns
                if any(fnmatch.fnmatch(file, p) for p in exclude_patterns):
                    continue

                file_path = os.path.join(root, file)

                try:
                    # Read file content
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Scan content
                    file_result = await self.scan_content(
                        content, file_path, workspace_id
                    )

                    # Merge results
                    scan_result.detected_secrets.extend(file_result.detected_secrets)
                    scan_result.total_secrets_found += file_result.total_secrets_found
                    scan_result.total_files_scanned += 1

                    # Merge severity counts
                    for severity, count in file_result.secrets_by_severity.items():
                        scan_result.secrets_by_severity[severity] = (
                            scan_result.secrets_by_severity.get(severity, 0) + count
                        )

                    # Merge type counts
                    for secret_type, count in file_result.secrets_by_type.items():
                        scan_result.secrets_by_type[secret_type] = (
                            scan_result.secrets_by_type.get(secret_type, 0) + count
                        )

                except Exception as e:
                    scan_result.scan_errors.append(
                        f"Error scanning {file_path}: {str(e)}"
                    )

        scan_result.completed_at = datetime.now()
        scan_result.recommendations = self._generate_recommendations(scan_result)

        # Store scan history
        self.scan_history.append(scan_result)

        return scan_result

    async def add_custom_pattern(
        self,
        name: str,
        pattern: str,
        type: SecretType = SecretType.CUSTOM,
        severity: SecretSeverity = SecretSeverity.MEDIUM,
        description: str = "",
        entropy_threshold: float = 3.5,
    ):
        """Add custom secret detection pattern"""

        custom = SecretPattern(
            name=name,
            type=type,
            pattern=pattern,
            severity=severity,
            description=description,
            entropy_threshold=entropy_threshold,
        )

        self.custom_patterns.append(custom)

    async def configure_vault(
        self,
        provider: VaultProvider,
        connection_string: str,
        auth_method: str,
        credentials: Dict[str, Any],
        **kwargs,
    ) -> VaultConfig:
        """Configure vault integration"""

        config = VaultConfig(
            provider=provider,
            connection_string=connection_string,
            auth_method=auth_method,
            credentials=credentials,
            **kwargs,
        )

        # Initialize vault client
        if provider == VaultProvider.HASHICORP and HASHICORP_VAULT_AVAILABLE:
            client = hvac.Client(url=connection_string)

            if auth_method == "token":
                client.token = credentials.get("token")
            elif auth_method == "userpass":
                client.auth.userpass.login(
                    username=credentials.get("username"),
                    password=credentials.get("password"),
                )

            self.vault_clients[provider.value] = client

        elif provider == VaultProvider.AWS_SECRETS_MANAGER and AWS_SECRETS_AVAILABLE:
            client = boto3.client(
                "secretsmanager",
                region_name=credentials.get("region", "us-east-1"),
                aws_access_key_id=credentials.get("access_key"),
                aws_secret_access_key=credentials.get("secret_key"),
            )
            self.vault_clients[provider.value] = client

        elif provider == VaultProvider.AZURE_KEYVAULT and AZURE_KEYVAULT_AVAILABLE:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=connection_string, credential=credential)
            self.vault_clients[provider.value] = client

        self.vault_configs[provider.value] = config

        return config

    async def store_secret_in_vault(
        self,
        secret_name: str,
        secret_value: str,
        provider: VaultProvider,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Store secret in configured vault"""

        if provider.value not in self.vault_clients:
            raise ValueError(f"Vault provider {provider.value} not configured")

        client = self.vault_clients[provider.value]
        config = self.vault_configs[provider.value]

        result = {"success": False, "message": "", "secret_path": ""}

        try:
            if provider == VaultProvider.HASHICORP:
                path = f"{config.mount_point}/{secret_name}"
                client.secrets.kv.v2.create_or_update_secret(
                    path=path,
                    secret={"value": secret_value, **metadata}
                    if metadata
                    else {"value": secret_value},
                )
                result["success"] = True
                result["secret_path"] = path
                result["message"] = "Secret stored in HashiCorp Vault"

            elif provider == VaultProvider.AWS_SECRETS_MANAGER:
                response = client.create_secret(
                    Name=secret_name,
                    SecretString=secret_value,
                    Tags=[{"Key": k, "Value": str(v)} for k, v in metadata.items()]
                    if metadata
                    else [],
                )
                result["success"] = True
                result["secret_path"] = response["ARN"]
                result["message"] = "Secret stored in AWS Secrets Manager"

            elif provider == VaultProvider.AZURE_KEYVAULT:
                client.set_secret(secret_name, secret_value)
                result["success"] = True
                result[
                    "secret_path"
                ] = f"{config.connection_string}/secrets/{secret_name}"
                result["message"] = "Secret stored in Azure Key Vault"

        except Exception as e:
            result["message"] = f"Failed to store secret: {str(e)}"

        return result

    async def retrieve_secret_from_vault(
        self, secret_name: str, provider: VaultProvider
    ) -> Optional[str]:
        """Retrieve secret from vault"""

        if provider.value not in self.vault_clients:
            raise ValueError(f"Vault provider {provider.value} not configured")

        client = self.vault_clients[provider.value]
        config = self.vault_configs[provider.value]

        try:
            if provider == VaultProvider.HASHICORP:
                path = f"{config.mount_point}/{secret_name}"
                response = client.secrets.kv.v2.read_secret_version(path=path)
                return response["data"]["data"]["value"]

            elif provider == VaultProvider.AWS_SECRETS_MANAGER:
                response = client.get_secret_value(SecretId=secret_name)
                return response["SecretString"]

            elif provider == VaultProvider.AZURE_KEYVAULT:
                secret = client.get_secret(secret_name)
                return secret.value

        except Exception as e:
            print(f"Failed to retrieve secret: {str(e)}")
            return None

    async def remediate_secret(
        self,
        detected_secret: DetectedSecret,
        action: str,  # ignore, vault, rotate, remove
        vault_provider: Optional[VaultProvider] = None,
    ) -> Dict[str, Any]:
        """Remediate detected secret"""

        result = {"success": False, "action": action, "message": ""}

        if action == "ignore":
            detected_secret.false_positive = True
            detected_secret.remediation_status = "ignored"
            self.whitelist.add(detected_secret.value_hash)
            result["success"] = True
            result["message"] = "Secret marked as false positive"

        elif action == "vault":
            if not vault_provider:
                result["message"] = "Vault provider required for vaulting"
                return result

            # Generate secret name from location
            secret_name = f"{detected_secret.type.value}_{detected_secret.id}"

            # Store in vault (would need actual secret value, not hash)
            # This is a placeholder - in real implementation, you'd need the actual value
            vault_result = await self.store_secret_in_vault(
                secret_name=secret_name,
                secret_value="<actual_secret_value>",  # Placeholder
                provider=vault_provider,
                metadata={
                    "detected_at": detected_secret.detected_at.isoformat(),
                    "severity": detected_secret.severity.value,
                    "location": json.dumps(detected_secret.location),
                },
            )

            if vault_result["success"]:
                detected_secret.remediation_status = "vaulted"
                result["success"] = True
                result["message"] = f"Secret vaulted at {vault_result['secret_path']}"
                result["vault_path"] = vault_result["secret_path"]
            else:
                result["message"] = vault_result["message"]

        elif action == "rotate":
            # Placeholder for secret rotation logic
            detected_secret.remediation_status = "rotated"
            result["success"] = True
            result["message"] = "Secret marked for rotation"

        elif action == "remove":
            detected_secret.remediation_status = "removed"
            result["success"] = True
            result["message"] = "Secret marked for removal"

        return result

    def _check_entropy(self, value: str, threshold: float) -> bool:
        """Calculate Shannon entropy of a string"""
        if not value:
            return False

        entropy = 0
        for i in range(256):
            char = chr(i)
            freq = value.count(char)
            if freq > 0:
                prob = float(freq) / len(value)
                entropy -= prob * (prob and prob * 2)

        return entropy >= threshold

    def _is_whitelisted(self, value: str) -> bool:
        """Check if secret is whitelisted"""
        value_hash = hashlib.sha256(value.encode()).hexdigest()
        return value_hash in self.whitelist

    def _mask_secret(self, value: str) -> str:
        """Mask secret value for display"""
        if len(value) <= 8:
            return "*" * len(value)

        visible_chars = 4
        return (
            value[:visible_chars]
            + "*" * (len(value) - visible_chars * 2)
            + value[-visible_chars:]
        )

    def _calculate_confidence(self, value: str, pattern: SecretPattern) -> float:
        """Calculate confidence score for detected secret"""
        confidence = 0.5  # Base confidence

        # Check entropy
        if self._check_entropy(value, pattern.entropy_threshold):
            confidence += 0.2

        # Check length
        if len(value) >= pattern.min_length * 1.5:
            confidence += 0.1

        # Check for common test/example values
        test_indicators = ["test", "demo", "example", "sample", "dummy", "xxx", "123"]
        if any(indicator in value.lower() for indicator in test_indicators):
            confidence -= 0.3

        # High severity patterns have higher confidence
        if pattern.severity == SecretSeverity.CRITICAL:
            confidence += 0.2

        return min(max(confidence, 0.0), 1.0)

    def _generate_recommendations(self, scan_result: SecretScanResult) -> List[str]:
        """Generate recommendations based on scan results"""
        recommendations = []

        if scan_result.total_secrets_found == 0:
            recommendations.append(
                "✅ No secrets detected. Good job maintaining security!"
            )
            return recommendations

        # Critical secrets
        critical_count = scan_result.secrets_by_severity.get(
            SecretSeverity.CRITICAL.value, 0
        )
        if critical_count > 0:
            recommendations.append(
                f"🚨 CRITICAL: Found {critical_count} critical secrets. "
                "Rotate these immediately and store in a secure vault."
            )

        # Database URLs
        db_count = scan_result.secrets_by_type.get(SecretType.DATABASE_URL.value, 0)
        if db_count > 0:
            recommendations.append(
                "🔐 Use environment variables or secret management services for database URLs"
            )

        # API Keys
        api_key_count = scan_result.secrets_by_type.get(SecretType.API_KEY.value, 0)
        if api_key_count > 0:
            recommendations.append(
                "🔑 Store API keys in a secure vault (HashiCorp Vault, AWS Secrets Manager, etc.)"
            )

        # Private Keys
        private_key_count = scan_result.secrets_by_type.get(
            SecretType.PRIVATE_KEY.value, 0
        )
        if private_key_count > 0:
            recommendations.append(
                "⚠️ Never commit private keys to version control. Use key management services."
            )

        # General recommendations
        recommendations.extend(
            [
                "📋 Add a .gitignore file to exclude sensitive files",
                "🔄 Implement secret rotation policies",
                "🛡️ Use pre-commit hooks to prevent secret commits",
                "📊 Enable secret scanning in your CI/CD pipeline",
                "🔐 Consider using tools like git-secrets or truffleHog",
            ]
        )

        return recommendations


# Global scanner instance
secret_scanner = SecretScanner()
