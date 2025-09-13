"""
Scheduled API Monitoring System
Cron-based scheduling for health checks and monitors
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Session, relationship
from pydantic import BaseModel, Field
import httpx
import json
import logging

from src.database import Base, get_db
from src.health_monitoring import HealthMonitor, ServiceStatus
from src.email_service import EmailService

logger = logging.getLogger(__name__)

class MonitorSchedule(Base):
    """Database model for scheduled monitors"""
    __tablename__ = "monitor_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    # Monitor details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    endpoints = Column(JSON)  # List of endpoints to monitor
    
    # Schedule configuration
    schedule_type = Column(String(50))  # cron, interval, once
    cron_expression = Column(String(100))  # e.g., "*/5 * * * *" (every 5 minutes)
    interval_seconds = Column(Integer)  # For interval-based scheduling
    timezone = Column(String(50), default="UTC")
    
    # Monitor configuration
    timeout_seconds = Column(Integer, default=30)
    retry_count = Column(Integer, default=3)
    expected_status_codes = Column(JSON, default=[200, 201, 204])
    headers = Column(JSON, default={})
    
    # Alert configuration
    alert_enabled = Column(Boolean, default=True)
    alert_emails = Column(JSON, default=[])
    alert_webhooks = Column(JSON, default=[])
    alert_threshold = Column(Integer, default=3)  # Failures before alert
    
    # Status
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    last_status = Column(String(50))  # success, partial, failed
    consecutive_failures = Column(Integer, default=0)
    
    # Results storage
    recent_results = Column(JSON, default=[])  # Last 100 results
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="monitor_schedules")
    project = relationship("Project", backref="monitor_schedules")

class MonitorResult(BaseModel):
    """Result of a monitor execution"""
    monitor_id: int
    timestamp: datetime
    endpoints_checked: int
    endpoints_healthy: int
    endpoints_failed: int
    overall_status: str  # operational, degraded, down
    response_times: Dict[str, float]
    errors: List[str]
    alerts_sent: bool

class ScheduledMonitorManager:
    """Manage scheduled monitors with cron support"""
    
    def __init__(self, db: Session):
        self.db = db
        self.scheduler = None
        self.health_monitor = HealthMonitor()
        self.email_service = EmailService()
        self._init_scheduler()
    
    def _init_scheduler(self):
        """Initialize the APScheduler"""
        jobstores = {
            'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            job_defaults={
                'coalesce': True,
                'max_instances': 3,
                'misfire_grace_time': 30
            },
            timezone='UTC'
        )
    
    def start_scheduler(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Monitor scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Monitor scheduler stopped")
    
    def create_monitor(self, monitor_data: Dict[str, Any]) -> MonitorSchedule:
        """Create a new scheduled monitor"""
        monitor = MonitorSchedule(**monitor_data)
        self.db.add(monitor)
        self.db.commit()
        self.db.refresh(monitor)
        
        # Schedule the monitor
        self._schedule_monitor(monitor)
        
        return monitor
    
    def _schedule_monitor(self, monitor: MonitorSchedule):
        """Schedule a monitor based on its configuration"""
        job_id = f"monitor_{monitor.id}"
        
        # Remove existing job if any
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        if not monitor.is_active:
            return
        
        # Create trigger based on schedule type
        if monitor.schedule_type == "cron":
            trigger = CronTrigger.from_crontab(
                monitor.cron_expression,
                timezone=monitor.timezone
            )
        elif monitor.schedule_type == "interval":
            trigger = IntervalTrigger(
                seconds=monitor.interval_seconds,
                timezone=monitor.timezone
            )
        else:
            logger.error(f"Unknown schedule type: {monitor.schedule_type}")
            return
        
        # Add job to scheduler
        self.scheduler.add_job(
            self._execute_monitor,
            trigger=trigger,
            args=[monitor.id],
            id=job_id,
            name=f"Monitor: {monitor.name}",
            replace_existing=True
        )
        
        logger.info(f"Scheduled monitor {monitor.id}: {monitor.name}")
    
    async def _execute_monitor(self, monitor_id: int):
        """Execute a scheduled monitor"""
        monitor = self.db.query(MonitorSchedule).filter_by(id=monitor_id).first()
        if not monitor:
            logger.error(f"Monitor {monitor_id} not found")
            return
        
        results = []
        errors = []
        response_times = {}
        
        # Check each endpoint
        for endpoint in monitor.endpoints:
            try:
                result = await self.health_monitor.check_endpoint({
                    'url': endpoint['url'],
                    'method': endpoint.get('method', 'GET'),
                    'headers': {**monitor.headers, **endpoint.get('headers', {})},
                    'expected_status': endpoint.get('expected_status', 200),
                    'timeout': monitor.timeout_seconds
                })
                
                results.append(result)
                response_times[endpoint['url']] = result.response_time_ms
                
                if not result.is_healthy:
                    errors.append(f"{endpoint['url']}: {result.error}")
                    
            except Exception as e:
                errors.append(f"{endpoint['url']}: {str(e)}")
                results.append({
                    'endpoint': endpoint['url'],
                    'is_healthy': False,
                    'error': str(e)
                })
        
        # Calculate overall status
        healthy_count = sum(1 for r in results if r.is_healthy if hasattr(r, 'is_healthy') else r.get('is_healthy'))
        total_count = len(results)
        
        if healthy_count == total_count:
            overall_status = "operational"
            monitor.consecutive_failures = 0
        elif healthy_count > 0:
            overall_status = "degraded"
            monitor.consecutive_failures += 1
        else:
            overall_status = "down"
            monitor.consecutive_failures += 1
        
        # Create result
        result = MonitorResult(
            monitor_id=monitor_id,
            timestamp=datetime.utcnow(),
            endpoints_checked=total_count,
            endpoints_healthy=healthy_count,
            endpoints_failed=total_count - healthy_count,
            overall_status=overall_status,
            response_times=response_times,
            errors=errors,
            alerts_sent=False
        )
        
        # Store result
        if not monitor.recent_results:
            monitor.recent_results = []
        
        monitor.recent_results.append(result.dict())
        monitor.recent_results = monitor.recent_results[-100:]  # Keep last 100
        
        # Update monitor status
        monitor.last_run = datetime.utcnow()
        monitor.last_status = overall_status
        
        # Send alerts if needed
        if monitor.alert_enabled and monitor.consecutive_failures >= monitor.alert_threshold:
            await self._send_alerts(monitor, result)
            result.alerts_sent = True
        
        self.db.commit()
        
        logger.info(f"Monitor {monitor.name} executed: {overall_status}")
        return result
    
    async def _send_alerts(self, monitor: MonitorSchedule, result: MonitorResult):
        """Send alerts for monitor failures"""
        
        # Prepare alert message
        message = f"""
        Monitor Alert: {monitor.name}
        Status: {result.overall_status.upper()}
        Time: {result.timestamp}
        
        Endpoints Checked: {result.endpoints_checked}
        Healthy: {result.endpoints_healthy}
        Failed: {result.endpoints_failed}
        
        Consecutive Failures: {monitor.consecutive_failures}
        
        Errors:
        {chr(10).join(result.errors)}
        """
        
        # Send email alerts
        for email in monitor.alert_emails:
            try:
                await self.email_service.send_alert(
                    to_email=email,
                    subject=f"Monitor Alert: {monitor.name} is {result.overall_status}",
                    body=message
                )
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
        
        # Send webhook alerts
        for webhook_url in monitor.alert_webhooks:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(webhook_url, json={
                        "monitor_name": monitor.name,
                        "status": result.overall_status,
                        "timestamp": result.timestamp.isoformat(),
                        "details": result.dict()
                    })
            except Exception as e:
                logger.error(f"Failed to send webhook alert: {e}")
    
    def get_monitor_status(self, monitor_id: int) -> Dict[str, Any]:
        """Get current status and history of a monitor"""
        monitor = self.db.query(MonitorSchedule).filter_by(id=monitor_id).first()
        if not monitor:
            return None
        
        # Calculate uptime percentage
        if monitor.recent_results:
            total = len(monitor.recent_results)
            successful = sum(1 for r in monitor.recent_results 
                           if r.get('overall_status') == 'operational')
            uptime_percentage = (successful / total) * 100
        else:
            uptime_percentage = 100.0
        
        return {
            "id": monitor.id,
            "name": monitor.name,
            "current_status": monitor.last_status,
            "uptime_percentage": uptime_percentage,
            "last_check": monitor.last_run,
            "next_check": self._get_next_run_time(monitor),
            "consecutive_failures": monitor.consecutive_failures,
            "recent_results": monitor.recent_results[-10:] if monitor.recent_results else [],
            "is_active": monitor.is_active
        }
    
    def _get_next_run_time(self, monitor: MonitorSchedule) -> Optional[datetime]:
        """Get next scheduled run time for a monitor"""
        job = self.scheduler.get_job(f"monitor_{monitor.id}")
        if job:
            return job.next_run_time
        return None
    
    def pause_monitor(self, monitor_id: int):
        """Pause a scheduled monitor"""
        monitor = self.db.query(MonitorSchedule).filter_by(id=monitor_id).first()
        if monitor:
            monitor.is_active = False
            self.db.commit()
            self.scheduler.pause_job(f"monitor_{monitor.id}")
    
    def resume_monitor(self, monitor_id: int):
        """Resume a paused monitor"""
        monitor = self.db.query(MonitorSchedule).filter_by(id=monitor_id).first()
        if monitor:
            monitor.is_active = True
            self.db.commit()
            self.scheduler.resume_job(f"monitor_{monitor.id}")
    
    def delete_monitor(self, monitor_id: int):
        """Delete a scheduled monitor"""
        monitor = self.db.query(MonitorSchedule).filter_by(id=monitor_id).first()
        if monitor:
            self.scheduler.remove_job(f"monitor_{monitor.id}")
            self.db.delete(monitor)
            self.db.commit()

# Common cron expressions for quick setup
CRON_PRESETS = {
    "every_minute": "* * * * *",
    "every_5_minutes": "*/5 * * * *",
    "every_15_minutes": "*/15 * * * *",
    "every_30_minutes": "*/30 * * * *",
    "every_hour": "0 * * * *",
    "every_6_hours": "0 */6 * * *",
    "every_day": "0 0 * * *",
    "every_week": "0 0 * * 0",
    "business_hours": "*/15 9-17 * * 1-5",  # Every 15 min, 9-5, Mon-Fri
}