"""
Proxy Configuration API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from src.database import get_db
from src.auth import get_current_user
from src.proxy_config import (
    ProxyConfig, ProxyType, ProxyAuth, ProxySettings,
    ProxyTestResult, test_proxy_connection, detect_system_proxy,
    proxy_manager
)

router = APIRouter(prefix="/api/proxy", tags=["Proxy Configuration"])

class ProxyConfigRequest(BaseModel):
    """Request model for proxy configuration"""
    enabled: bool = False
    type: str = "http"
    host: str = ""
    port: int = 8080
    username: Optional[str] = None
    password: Optional[str] = None
    bypass_list: List[str] = []
    use_system_proxy: bool = False
    tunnel_https: bool = True
    verify_ssl: bool = True
    timeout: int = 30

class ProxyTestRequest(BaseModel):
    """Request model for testing proxy connection"""
    config: ProxyConfigRequest
    test_url: str = "http://httpbin.org/ip"

@router.get("/settings")
async def get_proxy_settings(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get user's proxy settings"""
    # TODO: Load from database
    # For now, return current in-memory settings
    
    return {
        "success": True,
        "settings": {
            "global_proxy": proxy_manager.global_config.dict() if proxy_manager.global_config else None,
            "workspace_proxies": {
                key: config.dict() 
                for key, config in proxy_manager.configs.items() 
                if key.startswith("workspace_")
            },
            "environment_proxies": {
                key: config.dict() 
                for key, config in proxy_manager.configs.items() 
                if key.startswith("env_")
            },
            "system_proxy": None  # Will be detected below
        }
    }

@router.post("/global")
async def set_global_proxy(
    request: ProxyConfigRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Set global proxy configuration"""
    
    # Create proxy config
    config = ProxyConfig(
        enabled=request.enabled,
        type=ProxyType(request.type),
        host=request.host,
        port=request.port,
        bypass_list=request.bypass_list,
        use_system_proxy=request.use_system_proxy,
        tunnel_https=request.tunnel_https,
        verify_ssl=request.verify_ssl,
        timeout=request.timeout
    )
    
    # Add authentication if provided
    if request.username and request.password:
        config.auth = ProxyAuth(
            username=request.username,
            password=request.password
        )
    
    # Set in proxy manager
    proxy_manager.set_global_proxy(config)
    
    # TODO: Save to database
    
    return {
        "success": True,
        "message": "Global proxy configuration updated",
        "proxy_url": config.get_proxy_url()
    }

@router.post("/workspace/{workspace_id}")
async def set_workspace_proxy(
    workspace_id: str,
    request: ProxyConfigRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Set workspace-specific proxy configuration"""
    
    # Create proxy config
    config = ProxyConfig(
        enabled=request.enabled,
        type=ProxyType(request.type),
        host=request.host,
        port=request.port,
        bypass_list=request.bypass_list,
        use_system_proxy=request.use_system_proxy,
        tunnel_https=request.tunnel_https,
        verify_ssl=request.verify_ssl,
        timeout=request.timeout
    )
    
    # Add authentication if provided
    if request.username and request.password:
        config.auth = ProxyAuth(
            username=request.username,
            password=request.password
        )
    
    # Set in proxy manager
    proxy_manager.add_workspace_proxy(workspace_id, config)
    
    # TODO: Save to database
    
    return {
        "success": True,
        "message": f"Workspace proxy configuration updated for {workspace_id}",
        "proxy_url": config.get_proxy_url()
    }

@router.post("/environment/{env_id}")
async def set_environment_proxy(
    env_id: str,
    request: ProxyConfigRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Set environment-specific proxy configuration"""
    
    # Create proxy config
    config = ProxyConfig(
        enabled=request.enabled,
        type=ProxyType(request.type),
        host=request.host,
        port=request.port,
        bypass_list=request.bypass_list,
        use_system_proxy=request.use_system_proxy,
        tunnel_https=request.tunnel_https,
        verify_ssl=request.verify_ssl,
        timeout=request.timeout
    )
    
    # Add authentication if provided
    if request.username and request.password:
        config.auth = ProxyAuth(
            username=request.username,
            password=request.password
        )
    
    # Set in proxy manager
    proxy_manager.add_environment_proxy(env_id, config)
    
    # TODO: Save to database
    
    return {
        "success": True,
        "message": f"Environment proxy configuration updated for {env_id}",
        "proxy_url": config.get_proxy_url()
    }

@router.post("/test")
async def test_proxy(
    request: ProxyTestRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Test proxy connection"""
    
    # Create proxy config
    config = ProxyConfig(
        enabled=True,
        type=ProxyType(request.config.type),
        host=request.config.host,
        port=request.config.port,
        bypass_list=request.config.bypass_list,
        use_system_proxy=request.config.use_system_proxy,
        tunnel_https=request.config.tunnel_https,
        verify_ssl=request.config.verify_ssl,
        timeout=request.config.timeout
    )
    
    # Add authentication if provided
    if request.config.username and request.config.password:
        config.auth = ProxyAuth(
            username=request.config.username,
            password=request.config.password
        )
    
    # Test connection
    result = await test_proxy_connection(config, request.test_url)
    
    return {
        "success": result.success,
        "result": result.dict()
    }

@router.get("/detect-system")
async def detect_system_proxy_settings(
    current_user = Depends(get_current_user)
):
    """Detect system proxy settings"""
    
    system_proxy = detect_system_proxy()
    
    if system_proxy:
        return {
            "success": True,
            "detected": True,
            "proxy": system_proxy.dict()
        }
    else:
        return {
            "success": True,
            "detected": False,
            "message": "No system proxy detected"
        }

@router.delete("/global")
async def delete_global_proxy(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete global proxy configuration"""
    
    proxy_manager.global_config = None
    
    # TODO: Delete from database
    
    return {
        "success": True,
        "message": "Global proxy configuration deleted"
    }

@router.delete("/workspace/{workspace_id}")
async def delete_workspace_proxy(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete workspace-specific proxy configuration"""
    
    key = f"workspace_{workspace_id}"
    if key in proxy_manager.configs:
        del proxy_manager.configs[key]
    
    # TODO: Delete from database
    
    return {
        "success": True,
        "message": f"Workspace proxy configuration deleted for {workspace_id}"
    }

@router.delete("/environment/{env_id}")
async def delete_environment_proxy(
    env_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete environment-specific proxy configuration"""
    
    key = f"env_{env_id}"
    if key in proxy_manager.configs:
        del proxy_manager.configs[key]
    
    # TODO: Delete from database
    
    return {
        "success": True,
        "message": f"Environment proxy configuration deleted for {env_id}"
    }

@router.get("/presets")
async def get_proxy_presets(
    current_user = Depends(get_current_user)
):
    """Get common proxy presets"""
    
    presets = [
        {
            "name": "No Proxy",
            "description": "Direct connection without proxy",
            "config": {
                "enabled": False,
                "type": "none"
            }
        },
        {
            "name": "System Proxy",
            "description": "Use system proxy settings",
            "config": {
                "enabled": True,
                "use_system_proxy": True,
                "type": "system"
            }
        },
        {
            "name": "Local HTTP Proxy",
            "description": "Local proxy server (localhost:8080)",
            "config": {
                "enabled": True,
                "type": "http",
                "host": "localhost",
                "port": 8080
            }
        },
        {
            "name": "Local SOCKS5",
            "description": "Local SOCKS5 proxy (localhost:1080)",
            "config": {
                "enabled": True,
                "type": "socks5",
                "host": "localhost",
                "port": 1080
            }
        },
        {
            "name": "Corporate Proxy",
            "description": "Typical corporate proxy setup",
            "config": {
                "enabled": True,
                "type": "http",
                "host": "proxy.company.com",
                "port": 3128,
                "bypass_list": ["localhost", "127.0.0.1", "*.company.local"]
            }
        },
        {
            "name": "Burp Suite",
            "description": "Burp Suite proxy for security testing",
            "config": {
                "enabled": True,
                "type": "http",
                "host": "127.0.0.1",
                "port": 8080,
                "verify_ssl": False
            }
        },
        {
            "name": "Charles Proxy",
            "description": "Charles Web Debugging Proxy",
            "config": {
                "enabled": True,
                "type": "http",
                "host": "127.0.0.1",
                "port": 8888,
                "verify_ssl": False
            }
        }
    ]
    
    return {
        "success": True,
        "presets": presets
    }