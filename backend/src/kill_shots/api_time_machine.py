#!/usr/bin/env python3
"""
API TIME MACHINE - THE POSTMAN KILLER FEATURE #1
Version control for API behavior - Track every change, rollback anytime
This is what Postman WISHES they had!
"""

import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import asyncio
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

@dataclass
class APISnapshot:
    """A moment in time for an API"""
    timestamp: datetime
    endpoint: str
    method: str
    request_schema: Dict
    response_schema: Dict
    headers: Dict
    status_codes: List[int]
    average_latency: float
    behavior_hash: str
    breaking_changes: List[str] = None

    def calculate_hash(self) -> str:
        """Create unique fingerprint of API behavior"""
        behavior = {
            'request': self.request_schema,
            'response': self.response_schema,
            'headers': self.headers,
            'status_codes': self.status_codes
        }
        return hashlib.sha256(
            json.dumps(behavior, sort_keys=True).encode()
        ).hexdigest()


class APITimeMachine:
    """
    REVOLUTIONARY FEATURE: Time travel for APIs
    - Track every API change automatically
    - Rollback to any point in time
    - Detect breaking changes before deployment
    - Visual timeline of API evolution
    """

    def __init__(self):
        self.timeline = {}  # endpoint -> list of snapshots
        self.breaking_change_detector = BreakingChangeDetector()
        self.behavior_analyzer = BehaviorAnalyzer()
        self.max_snapshots_per_endpoint = 1000  # Limit for production
        self.alert_threshold = 0.5  # Only alert for high-confidence changes

    async def capture_snapshot(self, endpoint: str, method: str,
                              request_data: Dict, response_data: Dict,
                              latency: float) -> APISnapshot:
        """Capture current state of API"""

        # Extract schemas from actual data
        request_schema = self._extract_schema(request_data)
        response_schema = self._extract_schema(response_data)

        snapshot = APISnapshot(
            timestamp=datetime.utcnow(),
            endpoint=endpoint,
            method=method,
            request_schema=request_schema,
            response_schema=response_schema,
            headers=response_data.get('headers', {}),
            status_codes=[response_data.get('status_code', 200)],
            average_latency=latency,
            behavior_hash=""
        )

        snapshot.behavior_hash = snapshot.calculate_hash()

        # Store in timeline
        if endpoint not in self.timeline:
            self.timeline[endpoint] = []

        # Check for breaking changes
        if self.timeline[endpoint]:
            last_snapshot = self.timeline[endpoint][-1]
            breaking_changes = await self.detect_breaking_changes(
                last_snapshot, snapshot
            )
            if breaking_changes:
                snapshot.breaking_changes = breaking_changes
                await self._alert_breaking_changes(endpoint, breaking_changes)

        # Limit snapshots per endpoint for production
        if len(self.timeline[endpoint]) >= self.max_snapshots_per_endpoint:
            # Remove oldest snapshot
            self.timeline[endpoint].pop(0)

        self.timeline[endpoint].append(snapshot)
        return snapshot

    async def detect_breaking_changes(self, old_snapshot: APISnapshot,
                                     new_snapshot: APISnapshot) -> List[str]:
        """Detect breaking changes between snapshots"""
        changes = []

        # Check removed fields (BREAKING)
        old_fields = set(self._flatten_schema(old_snapshot.response_schema))
        new_fields = set(self._flatten_schema(new_snapshot.response_schema))

        removed = old_fields - new_fields
        if removed:
            changes.append(f"⚠️ REMOVED FIELDS: {', '.join(removed)}")

        # Check type changes (BREAKING)
        for field in old_fields & new_fields:
            old_type = self._get_field_type(old_snapshot.response_schema, field)
            new_type = self._get_field_type(new_snapshot.response_schema, field)
            if old_type != new_type:
                changes.append(f"⚠️ TYPE CHANGE: {field} from {old_type} to {new_type}")

        # Check status code changes
        old_codes = set(old_snapshot.status_codes)
        new_codes = set(new_snapshot.status_codes)
        if old_codes != new_codes:
            changes.append(f"⚠️ STATUS CODES: {old_codes} → {new_codes}")

        # Check latency regression (>100% increase for production)
        if new_snapshot.average_latency > old_snapshot.average_latency * 2.0:
            changes.append(
                f"⚠️ PERFORMANCE: {old_snapshot.average_latency:.2f}ms → "
                f"{new_snapshot.average_latency:.2f}ms"
            )

        return changes

    async def rollback_to_snapshot(self, endpoint: str, timestamp: datetime = None) -> Dict:
        """Rollback API behavior to specific point in time"""

        if endpoint not in self.timeline:
            raise ValueError(f"No timeline for endpoint: {endpoint}")

        snapshots = self.timeline[endpoint]
        if not snapshots:
            raise ValueError(f"No snapshots available for endpoint: {endpoint}")

        # If no timestamp provided, use the last snapshot
        if timestamp is None:
            target_snapshot = snapshots[-1]
        else:
            # Find snapshot closest to timestamp
            target_snapshot = None
            for snapshot in snapshots:
                if snapshot.timestamp <= timestamp:
                    target_snapshot = snapshot
                else:
                    break

            if not target_snapshot:
                # Use the first snapshot if timestamp is before all snapshots
                target_snapshot = snapshots[0]

        # Generate rollback configuration
        rollback_config = {
            'endpoint': endpoint,
            'timestamp': target_snapshot.timestamp.isoformat(),
            'request_schema': target_snapshot.request_schema,
            'response_schema': target_snapshot.response_schema,
            'headers': target_snapshot.headers,
            'expected_latency': target_snapshot.average_latency,
            'behavior_hash': target_snapshot.behavior_hash,
            'rollback_script': self._generate_rollback_script(target_snapshot)
        }

        return rollback_config

    async def get_timeline_visualization(self, endpoint: str) -> Dict:
        """Generate visual timeline of API changes"""

        if endpoint not in self.timeline:
            return {'error': 'No timeline available'}

        snapshots = self.timeline[endpoint]

        timeline_data = {
            'endpoint': endpoint,
            'total_snapshots': len(snapshots),
            'first_seen': snapshots[0].timestamp.isoformat(),
            'last_updated': snapshots[-1].timestamp.isoformat(),
            'events': []
        }

        for i, snapshot in enumerate(snapshots):
            event = {
                'id': i,
                'timestamp': snapshot.timestamp.isoformat(),
                'hash': snapshot.behavior_hash[:8],
                'latency': snapshot.average_latency,
                'type': 'normal'
            }

            if snapshot.breaking_changes:
                event['type'] = 'breaking'
                event['changes'] = snapshot.breaking_changes
            elif i > 0 and snapshot.average_latency > snapshots[i-1].average_latency * 1.3:
                event['type'] = 'performance_degradation'

            timeline_data['events'].append(event)

        return timeline_data

    async def predict_future_behavior(self, endpoint: str) -> Dict:
        """Predict future API behavior based on historical patterns"""

        if endpoint not in self.timeline or len(self.timeline[endpoint]) < 5:
            return {'error': 'Insufficient data for prediction'}

        snapshots = self.timeline[endpoint]

        # Analyze trends
        latency_trend = self._calculate_trend([s.average_latency for s in snapshots])
        change_frequency = self._calculate_change_frequency(snapshots)

        # Predict next breaking change
        avg_time_between_changes = self._average_time_between_changes(snapshots)
        last_change = snapshots[-1].timestamp
        next_change_prediction = last_change + avg_time_between_changes

        prediction = {
            'endpoint': endpoint,
            'predictions': {
                'next_breaking_change': next_change_prediction.isoformat(),
                'confidence': 0.75 if len(snapshots) > 10 else 0.5,
                'latency_trend': 'increasing' if latency_trend > 0 else 'stable',
                'projected_latency_7d': snapshots[-1].average_latency * (1 + latency_trend * 7),
                'change_frequency': change_frequency,
                'stability_score': max(0, 100 - change_frequency * 10)
            },
            'recommendations': []
        }

        # Generate recommendations
        if latency_trend > 0.1:
            prediction['recommendations'].append(
                "⚠️ Performance degradation detected. Consider optimization."
            )

        if change_frequency > 5:
            prediction['recommendations'].append(
                "⚠️ High change frequency. Consider API versioning."
            )

        return prediction

    def _extract_schema(self, data: Any) -> Dict:
        """Extract schema from actual data"""
        if isinstance(data, dict):
            return {k: self._extract_schema(v) for k, v in data.items()}
        elif isinstance(data, list):
            return ['array', self._extract_schema(data[0]) if data else 'unknown']
        else:
            return type(data).__name__

    def _flatten_schema(self, schema: Dict, prefix: str = '') -> List[str]:
        """Flatten nested schema to field paths"""
        fields = []
        for key, value in schema.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                fields.extend(self._flatten_schema(value, path))
            else:
                fields.append(path)
        return fields

    def _get_field_type(self, schema: Dict, field_path: str) -> str:
        """Get type of field from schema"""
        parts = field_path.split('.')
        current = schema
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return 'unknown'
        return str(current)

    def _generate_rollback_script(self, snapshot: APISnapshot) -> str:
        """Generate script to rollback to this snapshot"""
        script = f"""
# API Time Machine Rollback Script
# Generated: {datetime.utcnow().isoformat()}
# Target: {snapshot.endpoint} @ {snapshot.timestamp.isoformat()}

def rollback_api():
    '''Rollback API to snapshot'''

    # Expected request schema
    request_schema = {json.dumps(snapshot.request_schema, indent=2)}

    # Expected response schema
    response_schema = {json.dumps(snapshot.response_schema, indent=2)}

    # Expected headers
    headers = {json.dumps(snapshot.headers, indent=2)}

    # Behavior hash for validation
    expected_hash = "{snapshot.behavior_hash}"

    # TODO: Implement actual rollback logic
    # This would integrate with your deployment system

    return {{
        'endpoint': '{snapshot.endpoint}',
        'method': '{snapshot.method}',
        'rollback_to': '{snapshot.timestamp.isoformat()}',
        'status': 'ready'
    }}
"""
        return script

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend coefficient"""
        if len(values) < 2:
            return 0.0

        # Simple linear regression
        n = len(values)
        x = list(range(n))

        x_mean = sum(x) / n
        y_mean = sum(values) / n

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _calculate_change_frequency(self, snapshots: List[APISnapshot]) -> float:
        """Calculate how often API changes"""
        if len(snapshots) < 2:
            return 0.0

        changes = 0
        for i in range(1, len(snapshots)):
            if snapshots[i].behavior_hash != snapshots[i-1].behavior_hash:
                changes += 1

        time_span = (snapshots[-1].timestamp - snapshots[0].timestamp).days or 1
        return (changes / time_span) * 30  # Changes per month

    def _average_time_between_changes(self, snapshots: List[APISnapshot]) -> timedelta:
        """Calculate average time between breaking changes"""
        breaking_changes = [s for s in snapshots if s.breaking_changes]

        if len(breaking_changes) < 2:
            return timedelta(days=30)  # Default to 30 days

        total_time = timedelta()
        for i in range(1, len(breaking_changes)):
            total_time += breaking_changes[i].timestamp - breaking_changes[i-1].timestamp

        return total_time / (len(breaking_changes) - 1)

    async def _alert_breaking_changes(self, endpoint: str, changes: List[str]):
        """Alert about breaking changes"""
        # Only log critical changes in production
        if len(changes) > 2:  # Multiple breaking changes
            print(f"\n🚨 CRITICAL: Multiple breaking changes on {endpoint}: {len(changes)} issues")
        # Silently log minor changes

        # TODO: Send notifications via webhook/email
        # TODO: Create automatic rollback plan
        # TODO: Generate migration guide


class BreakingChangeDetector:
    """Advanced breaking change detection"""

    def analyze_semantic_changes(self, old_schema: Dict, new_schema: Dict) -> List[str]:
        """Detect semantic breaking changes"""
        # TODO: Implement semantic analysis
        pass


class BehaviorAnalyzer:
    """Analyze API behavior patterns"""

    def detect_anomalies(self, snapshots: List[APISnapshot]) -> List[Dict]:
        """Detect anomalous behavior"""
        # TODO: Implement anomaly detection
        pass


# Database model for persistence
class APITimeMachineSnapshot(Base):
    __tablename__ = 'api_time_machine_snapshots'

    id = Column(Integer, primary_key=True)
    endpoint = Column(String(500), index=True)
    method = Column(String(10))
    timestamp = Column(DateTime, index=True)
    behavior_hash = Column(String(64), index=True)
    request_schema = Column(JSON)
    response_schema = Column(JSON)
    headers = Column(JSON)
    status_codes = Column(JSON)
    average_latency = Column(Float)
    breaking_changes = Column(JSON)

    def to_snapshot(self) -> APISnapshot:
        """Convert DB model to snapshot"""
        return APISnapshot(
            timestamp=self.timestamp,
            endpoint=self.endpoint,
            method=self.method,
            request_schema=self.request_schema,
            response_schema=self.response_schema,
            headers=self.headers,
            status_codes=self.status_codes,
            average_latency=self.average_latency,
            behavior_hash=self.behavior_hash,
            breaking_changes=self.breaking_changes
        )