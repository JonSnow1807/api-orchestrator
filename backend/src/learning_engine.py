#!/usr/bin/env python3
"""
Learning and Adaptation Engine
Enables autonomous security system to learn from past scans and improve
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class SecurityContext:
    """Context information for security scans"""
    project_type: str
    language: str
    framework: str
    business_domain: str
    compliance_requirements: List[str]
    endpoint_patterns: List[str]

@dataclass
class LearningRecord:
    """Record of a security scan and its outcomes"""
    scan_id: str
    timestamp: datetime
    context: SecurityContext
    vulnerabilities_found: List[Dict[str, Any]]
    fixes_applied: List[Dict[str, Any]]
    user_feedback: Optional[Dict[str, Any]]
    effectiveness_score: float

class LearningEngine:
    """AI learning engine for continuous improvement"""

    def __init__(self, storage_path: str = "learning_data"):
        self.storage_path = storage_path
        self.learning_records: List[LearningRecord] = []
        self.patterns_learned: Dict[str, Any] = {}
        self.context_weights: Dict[str, float] = {}

        # Ensure storage directory exists
        os.makedirs(storage_path, exist_ok=True)

        # Load existing learning data
        self._load_learning_data()

    def _generate_scan_id(self, context: SecurityContext) -> str:
        """Generate unique scan ID based on context"""
        context_str = f"{context.project_type}_{context.language}_{context.framework}_{datetime.now().isoformat()}"
        return hashlib.md5(context_str.encode()).hexdigest()[:12]

    def _save_learning_data(self):
        """Persist learning data to storage"""
        try:
            # Save learning records
            records_data = []
            for record in self.learning_records:
                record_dict = asdict(record)
                record_dict['timestamp'] = record.timestamp.isoformat()
                record_dict['context'] = asdict(record.context)
                records_data.append(record_dict)

            with open(os.path.join(self.storage_path, 'learning_records.json'), 'w') as f:
                json.dump(records_data, f, indent=2)

            # Save learned patterns
            with open(os.path.join(self.storage_path, 'learned_patterns.json'), 'w') as f:
                json.dump(self.patterns_learned, f, indent=2)

            # Save context weights
            with open(os.path.join(self.storage_path, 'context_weights.json'), 'w') as f:
                json.dump(self.context_weights, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save learning data: {e}")

    def _load_learning_data(self):
        """Load learning data from storage"""
        try:
            # Load learning records
            records_file = os.path.join(self.storage_path, 'learning_records.json')
            if os.path.exists(records_file):
                with open(records_file, 'r') as f:
                    records_data = json.load(f)

                for record_dict in records_data:
                    context = SecurityContext(**record_dict['context'])
                    record = LearningRecord(
                        scan_id=record_dict['scan_id'],
                        timestamp=datetime.fromisoformat(record_dict['timestamp']),
                        context=context,
                        vulnerabilities_found=record_dict['vulnerabilities_found'],
                        fixes_applied=record_dict['fixes_applied'],
                        user_feedback=record_dict.get('user_feedback'),
                        effectiveness_score=record_dict['effectiveness_score']
                    )
                    self.learning_records.append(record)

            # Load learned patterns
            patterns_file = os.path.join(self.storage_path, 'learned_patterns.json')
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r') as f:
                    self.patterns_learned = json.load(f)

            # Load context weights
            weights_file = os.path.join(self.storage_path, 'context_weights.json')
            if os.path.exists(weights_file):
                with open(weights_file, 'r') as f:
                    self.context_weights = json.load(f)

        except Exception as e:
            print(f"Warning: Could not load learning data: {e}")

    def record_scan_outcome(self, context: SecurityContext, vulnerabilities: List[Dict[str, Any]],
                           fixes: List[Dict[str, Any]], effectiveness: float) -> str:
        """Record the outcome of a security scan"""

        scan_id = self._generate_scan_id(context)

        record = LearningRecord(
            scan_id=scan_id,
            timestamp=datetime.now(),
            context=context,
            vulnerabilities_found=vulnerabilities,
            fixes_applied=fixes,
            user_feedback=None,
            effectiveness_score=effectiveness
        )

        self.learning_records.append(record)

        # Update learned patterns
        self._update_learned_patterns(context, vulnerabilities, fixes, effectiveness)

        # Save learning data
        self._save_learning_data()

        return scan_id

    def _update_learned_patterns(self, context: SecurityContext, vulnerabilities: List[Dict[str, Any]],
                                fixes: List[Dict[str, Any]], effectiveness: float):
        """Update learned patterns based on scan outcomes"""

        # Learn vulnerability patterns by project type
        project_key = f"{context.project_type}_{context.language}"

        if project_key not in self.patterns_learned:
            self.patterns_learned[project_key] = {
                "common_vulnerabilities": {},
                "effective_fixes": {},
                "scan_count": 0,
                "avg_effectiveness": 0.0
            }

        pattern = self.patterns_learned[project_key]
        pattern["scan_count"] += 1

        # Update vulnerability frequency
        for vuln in vulnerabilities:
            vuln_type = vuln.get('type', 'unknown')
            if vuln_type not in pattern["common_vulnerabilities"]:
                pattern["common_vulnerabilities"][vuln_type] = 0
            pattern["common_vulnerabilities"][vuln_type] += 1

        # Update fix effectiveness
        for fix in fixes:
            fix_type = fix.get('type', 'unknown')
            if fix_type not in pattern["effective_fixes"]:
                pattern["effective_fixes"][fix_type] = {"count": 0, "total_effectiveness": 0.0}

            pattern["effective_fixes"][fix_type]["count"] += 1
            pattern["effective_fixes"][fix_type]["total_effectiveness"] += effectiveness

        # Update average effectiveness
        pattern["avg_effectiveness"] = (
            (pattern["avg_effectiveness"] * (pattern["scan_count"] - 1) + effectiveness) /
            pattern["scan_count"]
        )

        # Update context weights
        context_key = f"{context.business_domain}_{context.framework}"
        if context_key not in self.context_weights:
            self.context_weights[context_key] = 1.0

        # Increase weight for contexts with higher effectiveness
        if effectiveness > 0.8:
            self.context_weights[context_key] = min(2.0, self.context_weights[context_key] + 0.1)
        elif effectiveness < 0.5:
            self.context_weights[context_key] = max(0.5, self.context_weights[context_key] - 0.1)

    def get_recommendations(self, context: SecurityContext) -> Dict[str, Any]:
        """Get AI-powered recommendations based on learned patterns"""

        project_key = f"{context.project_type}_{context.language}"
        context_key = f"{context.business_domain}_{context.framework}"

        recommendations = {
            "priority_scan_types": [],
            "likely_vulnerabilities": [],
            "recommended_fixes": [],
            "confidence_score": 0.0,
            "learning_insights": {}
        }

        # Get patterns for similar projects
        if project_key in self.patterns_learned:
            pattern = self.patterns_learned[project_key]

            # Recommend vulnerability scans based on frequency
            vulns = pattern["common_vulnerabilities"]
            if vulns:
                sorted_vulns = sorted(vulns.items(), key=lambda x: x[1], reverse=True)
                recommendations["likely_vulnerabilities"] = [
                    {"type": vuln_type, "probability": count / pattern["scan_count"]}
                    for vuln_type, count in sorted_vulns[:5]
                ]

            # Recommend fixes based on effectiveness
            fixes = pattern["effective_fixes"]
            if fixes:
                effective_fixes = []
                for fix_type, fix_data in fixes.items():
                    if fix_data["count"] > 0:
                        avg_effectiveness = fix_data["total_effectiveness"] / fix_data["count"]
                        if avg_effectiveness > 0.6:
                            effective_fixes.append({
                                "type": fix_type,
                                "effectiveness": avg_effectiveness,
                                "usage_count": fix_data["count"]
                            })

                recommendations["recommended_fixes"] = sorted(
                    effective_fixes, key=lambda x: x["effectiveness"], reverse=True
                )[:5]

            recommendations["confidence_score"] = min(1.0, pattern["scan_count"] / 10.0)

        # Add context-specific insights
        context_weight = self.context_weights.get(context_key, 1.0)

        recommendations["learning_insights"] = {
            "total_scans_recorded": len(self.learning_records),
            "similar_project_scans": self.patterns_learned.get(project_key, {}).get("scan_count", 0),
            "context_weight": context_weight,
            "avg_effectiveness": self.patterns_learned.get(project_key, {}).get("avg_effectiveness", 0.0)
        }

        # Prioritize scan types based on learned patterns
        if recommendations["likely_vulnerabilities"]:
            high_prob_vulns = [v for v in recommendations["likely_vulnerabilities"] if v["probability"] > 0.3]
            if high_prob_vulns:
                recommendations["priority_scan_types"] = [
                    "security_vulnerability_scan",
                    "database_security_audit" if any("sql" in v["type"].lower() for v in high_prob_vulns) else "devops_security_scan"
                ]

        return recommendations

    def add_user_feedback(self, scan_id: str, feedback: Dict[str, Any]):
        """Add user feedback to improve learning"""

        for record in self.learning_records:
            if record.scan_id == scan_id:
                record.user_feedback = feedback

                # Adjust effectiveness based on feedback
                if feedback.get("helpful", False):
                    record.effectiveness_score = min(1.0, record.effectiveness_score + 0.1)
                elif feedback.get("not_helpful", False):
                    record.effectiveness_score = max(0.0, record.effectiveness_score - 0.2)

                # Update learned patterns with feedback
                self._update_learned_patterns(
                    record.context, record.vulnerabilities_found,
                    record.fixes_applied, record.effectiveness_score
                )

                self._save_learning_data()
                break

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about the learning system"""

        if not self.learning_records:
            return {
                "total_scans": 0,
                "avg_effectiveness": 0.0,
                "learning_coverage": {},
                "improvement_trend": "No data"
            }

        recent_records = [
            r for r in self.learning_records
            if r.timestamp > datetime.now() - timedelta(days=30)
        ]

        stats = {
            "total_scans": len(self.learning_records),
            "recent_scans": len(recent_records),
            "avg_effectiveness": sum(r.effectiveness_score for r in self.learning_records) / len(self.learning_records),
            "learning_coverage": {},
            "patterns_learned": len(self.patterns_learned),
            "context_variations": len(self.context_weights)
        }

        # Calculate learning coverage by language/framework
        coverage = {}
        for record in self.learning_records:
            key = f"{record.context.language}_{record.context.framework}"
            if key not in coverage:
                coverage[key] = 0
            coverage[key] += 1

        stats["learning_coverage"] = coverage

        # Calculate improvement trend
        if len(self.learning_records) >= 5:
            recent_avg = sum(r.effectiveness_score for r in self.learning_records[-5:]) / 5
            older_avg = sum(r.effectiveness_score for r in self.learning_records[:5]) / 5

            if recent_avg > older_avg + 0.1:
                stats["improvement_trend"] = "Improving"
            elif recent_avg < older_avg - 0.1:
                stats["improvement_trend"] = "Declining"
            else:
                stats["improvement_trend"] = "Stable"

        return stats

    def clear_old_data(self, days: int = 90):
        """Clear learning data older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)

        original_count = len(self.learning_records)
        self.learning_records = [
            record for record in self.learning_records
            if record.timestamp > cutoff_date
        ]

        removed_count = original_count - len(self.learning_records)

        # Rebuild patterns from remaining data
        self.patterns_learned = {}
        self.context_weights = {}

        for record in self.learning_records:
            self._update_learned_patterns(
                record.context, record.vulnerabilities_found,
                record.fixes_applied, record.effectiveness_score
            )

        self._save_learning_data()

        return {"removed_records": removed_count, "remaining_records": len(self.learning_records)}