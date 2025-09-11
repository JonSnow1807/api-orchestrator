"""
API Health Monitoring and Status Pages
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import statistics
from dataclasses import dataclass, asdict
from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, Float, ForeignKey
from src.database import Base

class ServiceStatus(Enum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    PARTIAL_OUTAGE = "partial_outage"
    MAJOR_OUTAGE = "major_outage"
    MAINTENANCE = "maintenance"

@dataclass
class HealthCheckResult:
    """Single health check result"""
    timestamp: datetime
    endpoint: str
    status_code: int
    response_time_ms: float
    is_healthy: bool
    error: Optional[str] = None

@dataclass
class ServiceHealth:
    """Service health summary"""
    name: str
    status: ServiceStatus
    uptime_percentage: float
    avg_response_time_ms: float
    last_check: datetime
    incidents_today: int
    incidents_this_week: int
    incidents_this_month: int

class HealthMonitor:
    """Monitor API endpoints health"""
    
    def __init__(self):
        self.checks: Dict[str, List[HealthCheckResult]] = {}
        self.is_monitoring = {}
        
    async def check_endpoint(self, endpoint_config: Dict[str, Any]) -> HealthCheckResult:
        """Check a single endpoint health"""
        
        url = endpoint_config.get('url')
        method = endpoint_config.get('method', 'GET')
        headers = endpoint_config.get('headers', {})
        expected_status = endpoint_config.get('expected_status', 200)
        timeout = endpoint_config.get('timeout', 10)
        
        start_time = datetime.utcnow()
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(method, url, headers=headers)
                
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                is_healthy = response.status_code == expected_status
                
                return HealthCheckResult(
                    timestamp=start_time,
                    endpoint=url,
                    status_code=response.status_code,
                    response_time_ms=response_time,
                    is_healthy=is_healthy,
                    error=None if is_healthy else f"Expected {expected_status}, got {response.status_code}"
                )
                
        except httpx.TimeoutException:
            return HealthCheckResult(
                timestamp=start_time,
                endpoint=url,
                status_code=0,
                response_time_ms=timeout * 1000,
                is_healthy=False,
                error="Request timeout"
            )
        except Exception as e:
            return HealthCheckResult(
                timestamp=start_time,
                endpoint=url,
                status_code=0,
                response_time_ms=0,
                is_healthy=False,
                error=str(e)
            )
    
    async def start_monitoring(self, monitor_id: str, endpoints: List[Dict], interval_seconds: int = 60):
        """Start monitoring multiple endpoints"""
        
        self.is_monitoring[monitor_id] = True
        
        while self.is_monitoring.get(monitor_id, False):
            for endpoint in endpoints:
                if not self.is_monitoring.get(monitor_id, False):
                    break
                    
                result = await self.check_endpoint(endpoint)
                
                # Store result
                if monitor_id not in self.checks:
                    self.checks[monitor_id] = []
                
                self.checks[monitor_id].append(result)
                
                # Keep only last 1000 checks per monitor
                if len(self.checks[monitor_id]) > 1000:
                    self.checks[monitor_id] = self.checks[monitor_id][-1000:]
            
            await asyncio.sleep(interval_seconds)
    
    def stop_monitoring(self, monitor_id: str):
        """Stop monitoring"""
        self.is_monitoring[monitor_id] = False
    
    def get_service_health(self, monitor_id: str) -> Optional[ServiceHealth]:
        """Get current health status for a service"""
        
        if monitor_id not in self.checks or not self.checks[monitor_id]:
            return None
        
        checks = self.checks[monitor_id]
        now = datetime.utcnow()
        
        # Calculate metrics for different time periods
        last_hour = [c for c in checks if (now - c.timestamp).seconds <= 3600]
        last_day = [c for c in checks if (now - c.timestamp).days < 1]
        last_week = [c for c in checks if (now - c.timestamp).days < 7]
        last_month = [c for c in checks if (now - c.timestamp).days < 30]
        
        if not last_hour:
            return None
        
        # Calculate uptime
        uptime_checks = last_day if last_day else last_hour
        healthy_count = sum(1 for c in uptime_checks if c.is_healthy)
        uptime_percentage = (healthy_count / len(uptime_checks) * 100) if uptime_checks else 0
        
        # Calculate average response time
        response_times = [c.response_time_ms for c in last_hour if c.is_healthy]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        # Count incidents
        incidents_today = sum(1 for c in last_day if not c.is_healthy)
        incidents_week = sum(1 for c in last_week if not c.is_healthy)
        incidents_month = sum(1 for c in last_month if not c.is_healthy)
        
        # Determine status
        if uptime_percentage >= 99.9:
            status = ServiceStatus.OPERATIONAL
        elif uptime_percentage >= 95:
            status = ServiceStatus.DEGRADED
        elif uptime_percentage >= 80:
            status = ServiceStatus.PARTIAL_OUTAGE
        else:
            status = ServiceStatus.MAJOR_OUTAGE
        
        return ServiceHealth(
            name=monitor_id,
            status=status,
            uptime_percentage=uptime_percentage,
            avg_response_time_ms=avg_response_time,
            last_check=checks[-1].timestamp,
            incidents_today=incidents_today,
            incidents_this_week=incidents_week,
            incidents_this_month=incidents_month
        )
    
    def get_uptime_history(self, monitor_id: str, days: int = 90) -> List[Dict]:
        """Get uptime history for status page"""
        
        if monitor_id not in self.checks:
            return []
        
        checks = self.checks[monitor_id]
        now = datetime.utcnow()
        history = []
        
        for day in range(days):
            date = now - timedelta(days=day)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_checks = [
                c for c in checks 
                if day_start <= c.timestamp < day_end
            ]
            
            if day_checks:
                healthy = sum(1 for c in day_checks if c.is_healthy)
                uptime = (healthy / len(day_checks) * 100)
                
                # Determine color based on uptime
                if uptime >= 99.9:
                    color = "green"
                elif uptime >= 95:
                    color = "yellow"
                elif uptime >= 80:
                    color = "orange"
                else:
                    color = "red"
                
                history.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "uptime": uptime,
                    "color": color,
                    "incidents": len(day_checks) - healthy
                })
            else:
                history.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "uptime": None,
                    "color": "gray",
                    "incidents": 0
                })
        
        return list(reversed(history))
    
    def get_incident_timeline(self, monitor_id: str) -> List[Dict]:
        """Get incident timeline for status page"""
        
        if monitor_id not in self.checks:
            return []
        
        checks = self.checks[monitor_id]
        incidents = []
        current_incident = None
        
        for i, check in enumerate(checks):
            if not check.is_healthy:
                if current_incident is None:
                    # Start of new incident
                    current_incident = {
                        "start": check.timestamp,
                        "end": None,
                        "duration_minutes": 0,
                        "error": check.error,
                        "checks_failed": 1
                    }
                else:
                    # Continuing incident
                    current_incident["checks_failed"] += 1
                    current_incident["error"] = check.error
            else:
                if current_incident is not None:
                    # End of incident
                    current_incident["end"] = check.timestamp
                    duration = (current_incident["end"] - current_incident["start"]).total_seconds() / 60
                    current_incident["duration_minutes"] = round(duration, 1)
                    incidents.append(current_incident)
                    current_incident = None
        
        # Handle ongoing incident
        if current_incident is not None:
            current_incident["end"] = datetime.utcnow()
            duration = (current_incident["end"] - current_incident["start"]).total_seconds() / 60
            current_incident["duration_minutes"] = round(duration, 1)
            current_incident["ongoing"] = True
            incidents.append(current_incident)
        
        return incidents

class StatusPage(Base):
    """Status page configuration"""
    __tablename__ = "status_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    
    # Configuration
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)  # URL slug
    description = Column(String(500))
    
    # Services to monitor
    services = Column(JSON)  # List of endpoint configurations
    
    # Display settings
    is_public = Column(Boolean, default=True)
    show_uptime_history = Column(Boolean, default=True)
    show_incident_timeline = Column(Boolean, default=True)
    show_response_times = Column(Boolean, default=True)
    custom_domain = Column(String(255))
    
    # Branding
    logo_url = Column(String(500))
    primary_color = Column(String(7), default="#8B5CF6")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)