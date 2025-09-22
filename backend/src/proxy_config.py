"""
Proxy Configuration Module
Supports HTTP, HTTPS, and SOCKS proxy configurations with authentication
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import httpx
import re
from urllib.parse import urlparse


class ProxyType(Enum):
    """Supported proxy types"""

    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"
    SYSTEM = "system"
    NONE = "none"


class ProxyAuth(BaseModel):
    """Proxy authentication configuration"""

    username: str
    password: str


class ProxyConfig(BaseModel):
    """Proxy configuration model"""

    enabled: bool = False
    type: ProxyType = ProxyType.HTTP
    host: str = ""
    port: int = 8080
    auth: Optional[ProxyAuth] = None
    bypass_list: List[str] = Field(default_factory=list)
    use_system_proxy: bool = False

    # Advanced settings
    tunnel_https: bool = True  # Use HTTP CONNECT tunneling for HTTPS
    verify_ssl: bool = True
    timeout: int = 30

    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        if v < 1 or v > 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("host")
    @classmethod
    def validate_host(cls, v, info):
        if info.data.get("enabled") and not v and not info.data.get("use_system_proxy"):
            raise ValueError("Host is required when proxy is enabled")
        return v

    def get_proxy_url(self) -> Optional[str]:
        """Get the formatted proxy URL"""
        if not self.enabled:
            return None

        if self.use_system_proxy:
            # Use system proxy settings
            import os

            return os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")

        if not self.host:
            return None

        # Build proxy URL
        if self.auth:
            auth_str = f"{self.auth.username}:{self.auth.password}@"
        else:
            auth_str = ""

        proxy_url = f"{self.type.value}://{auth_str}{self.host}:{self.port}"
        return proxy_url

    def should_bypass(self, url: str) -> bool:
        """Check if URL should bypass proxy"""
        if not self.bypass_list:
            return False

        parsed = urlparse(url)
        host = parsed.hostname or ""

        for pattern in self.bypass_list:
            # Support wildcards
            regex_pattern = pattern.replace("*", ".*")
            if re.match(regex_pattern, host):
                return True

            # Support CIDR notation for IP ranges
            if "/" in pattern:
                # TODO: Implement CIDR matching
                pass

        return False

    def to_httpx_proxies(self) -> Optional[Dict[str, str]]:
        """Convert to httpx-compatible proxy configuration"""
        proxy_url = self.get_proxy_url()
        if not proxy_url:
            return None

        # httpx uses different format for proxies
        if self.type in [ProxyType.HTTP, ProxyType.HTTPS]:
            return {"http://": proxy_url, "https://": proxy_url}
        elif self.type in [ProxyType.SOCKS4, ProxyType.SOCKS5]:
            # For SOCKS proxies, need to use httpx-socks
            return {"all://": proxy_url}

        return None


class ProxyManager:
    """Manages proxy configurations for API requests"""

    def __init__(self):
        self.configs: Dict[str, ProxyConfig] = {}
        self.global_config: Optional[ProxyConfig] = None

    def set_global_proxy(self, config: ProxyConfig):
        """Set global proxy configuration"""
        self.global_config = config

    def add_workspace_proxy(self, workspace_id: str, config: ProxyConfig):
        """Add workspace-specific proxy configuration"""
        self.configs[f"workspace_{workspace_id}"] = config

    def add_environment_proxy(self, env_id: str, config: ProxyConfig):
        """Add environment-specific proxy configuration"""
        self.configs[f"env_{env_id}"] = config

    def get_proxy_for_request(
        self, url: str, workspace_id: Optional[str] = None, env_id: Optional[str] = None
    ) -> Optional[ProxyConfig]:
        """
        Get appropriate proxy configuration for a request
        Priority: Environment > Workspace > Global
        """
        # Check environment-specific proxy
        if env_id and f"env_{env_id}" in self.configs:
            config = self.configs[f"env_{env_id}"]
            if config.enabled and not config.should_bypass(url):
                return config

        # Check workspace-specific proxy
        if workspace_id and f"workspace_{workspace_id}" in self.configs:
            config = self.configs[f"workspace_{workspace_id}"]
            if config.enabled and not config.should_bypass(url):
                return config

        # Check global proxy
        if self.global_config and self.global_config.enabled:
            if not self.global_config.should_bypass(url):
                return self.global_config

        return None

    def create_http_client(
        self,
        url: str,
        workspace_id: Optional[str] = None,
        env_id: Optional[str] = None,
        **kwargs,
    ) -> httpx.AsyncClient:
        """Create an HTTP client with appropriate proxy configuration"""
        proxy_config = self.get_proxy_for_request(url, workspace_id, env_id)

        client_kwargs = kwargs.copy()

        if proxy_config:
            proxies = proxy_config.to_httpx_proxies()
            if proxies:
                client_kwargs["proxies"] = proxies

            client_kwargs["verify"] = proxy_config.verify_ssl
            client_kwargs["timeout"] = proxy_config.timeout

        return httpx.AsyncClient(**client_kwargs)


# Global proxy manager instance
proxy_manager = ProxyManager()


class ProxySettings(BaseModel):
    """User proxy settings stored in database"""

    user_id: int
    global_proxy: Optional[ProxyConfig] = None
    workspace_proxies: Dict[str, ProxyConfig] = Field(default_factory=dict)
    environment_proxies: Dict[str, ProxyConfig] = Field(default_factory=dict)

    # Presets for common proxy servers
    presets: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"name": "Local Proxy", "type": "http", "host": "localhost", "port": 8080},
            {
                "name": "Corporate Proxy",
                "type": "http",
                "host": "proxy.company.com",
                "port": 3128,
            },
            {
                "name": "SOCKS5 Proxy",
                "type": "socks5",
                "host": "localhost",
                "port": 1080,
            },
        ]
    )

    # Auto-detect settings
    auto_detect: bool = False
    pac_url: Optional[str] = None  # Proxy Auto-Configuration URL

    def apply_to_manager(self, manager: ProxyManager):
        """Apply settings to proxy manager"""
        if self.global_proxy:
            manager.set_global_proxy(self.global_proxy)

        for workspace_id, config in self.workspace_proxies.items():
            manager.add_workspace_proxy(workspace_id, config)

        for env_id, config in self.environment_proxies.items():
            manager.add_environment_proxy(env_id, config)


class ProxyTestResult(BaseModel):
    """Result of proxy connectivity test"""

    success: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    proxy_type: Optional[str] = None
    authenticated: bool = False


async def test_proxy_connection(
    config: ProxyConfig, test_url: str = "http://httpbin.org/ip"
) -> ProxyTestResult:
    """Test proxy connectivity"""
    import time

    try:
        proxies = config.to_httpx_proxies()
        start_time = time.time()

        async with httpx.AsyncClient(
            proxies=proxies, verify=config.verify_ssl, timeout=10
        ) as client:
            response = await client.get(test_url)
            response.raise_for_status()

        latency_ms = (time.time() - start_time) * 1000

        return ProxyTestResult(
            success=True,
            latency_ms=latency_ms,
            proxy_type=config.type.value,
            authenticated=config.auth is not None,
        )
    except httpx.ProxyError as e:
        return ProxyTestResult(
            success=False, error=f"Proxy error: {str(e)}", proxy_type=config.type.value
        )
    except httpx.TimeoutException:
        return ProxyTestResult(
            success=False,
            error="Proxy connection timeout",
            proxy_type=config.type.value,
        )
    except Exception as e:
        return ProxyTestResult(
            success=False, error=str(e), proxy_type=config.type.value
        )


# System proxy detection utilities
def detect_system_proxy() -> Optional[ProxyConfig]:
    """Detect system proxy settings"""
    import os
    import platform

    proxy_env_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
    no_proxy = os.environ.get("NO_PROXY", os.environ.get("no_proxy", ""))

    for var in proxy_env_vars:
        proxy_url = os.environ.get(var)
        if proxy_url:
            parsed = urlparse(proxy_url)

            config = ProxyConfig(
                enabled=True,
                type=ProxyType.HTTP if parsed.scheme == "http" else ProxyType.HTTPS,
                host=parsed.hostname or "",
                port=parsed.port or 8080,
                use_system_proxy=True,
            )

            if parsed.username and parsed.password:
                config.auth = ProxyAuth(
                    username=parsed.username, password=parsed.password
                )

            if no_proxy:
                config.bypass_list = [h.strip() for h in no_proxy.split(",")]

            return config

    # Platform-specific detection
    if platform.system() == "Windows":
        # Windows proxy detection via registry
        try:
            pass
            # TODO: Implement Windows registry proxy detection
        except ImportError:
            pass
    elif platform.system() == "Darwin":
        # macOS proxy detection via networksetup
        try:
            import subprocess

            result = subprocess.run(
                ["networksetup", "-getwebproxy", "Wi-Fi"],
                capture_output=True,
                text=True,
            )
            # TODO: Parse networksetup output
        except Exception:
            pass

    return None
