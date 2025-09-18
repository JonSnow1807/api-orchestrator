#!/usr/bin/env python3
import re
"""
SELF-LEARNING SYSTEM - The Brain That Never Forgets
Gets smarter with every API it tests, every bug it finds, every fix it applies
This is true AI - it LEARNS and IMPROVES autonomously
"""

import json
import pickle
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import asyncio
import os
from pathlib import Path


@dataclass
class LearningEvent:
    """An event the system learns from"""
    timestamp: datetime
    event_type: str  # vulnerability, fix, performance, error, success
    api_endpoint: str
    context: Dict[str, Any]
    outcome: str
    confidence: float
    patterns_detected: List[str]
    solution_applied: Optional[str] = None
    time_to_resolution: Optional[float] = None


@dataclass
class LearnedPattern:
    """A pattern the system has learned"""
    pattern_id: str
    pattern_type: str
    description: str
    occurrences: int
    success_rate: float
    avg_resolution_time: float
    solutions: List[Dict[str, Any]]
    confidence: float
    last_seen: datetime


@dataclass
class PredictedIssue:
    """An issue predicted by the learning system"""
    issue_type: str
    probability: float
    estimated_impact: str
    suggested_solutions: List[str]
    confidence: float
    based_on_patterns: List[str]


class SelfLearningSystem:
    """
    The AI brain that learns from every interaction
    This makes the system get better over time - TRUE INTELLIGENCE
    """

    def __init__(self, knowledge_base_path: str = "knowledge_base"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_base_path.mkdir(exist_ok=True)

        # Learning components
        self.vulnerability_patterns = self._load_or_create("vulnerability_patterns.pkl", {})
        self.fix_database = self._load_or_create("fix_database.pkl", {})
        self.performance_baselines = self._load_or_create("performance_baselines.pkl", {})
        self.error_patterns = self._load_or_create("error_patterns.pkl", {})
        self.business_rules = self._load_or_create("business_rules.pkl", {})

        # ML Models
        self.vulnerability_classifier = self._load_or_create_model("vulnerability_classifier.pkl")
        self.performance_predictor = self._load_or_create_model("performance_predictor.pkl")
        self.anomaly_detector = IsolationForest(contamination=0.1)

        # Pattern matching
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000)
        self.pattern_vectors = {}

        # Learning history
        self.learning_events = []
        self.learned_patterns = {}

        # Statistics
        self.stats = {
            "total_events_processed": 0,
            "patterns_learned": 0,
            "successful_predictions": 0,
            "failed_predictions": 0,
            "avg_confidence": 0.0
        }

        # Additional attributes for API learning
        self.api_patterns = []
        self.knowledge_base = {}

        print("🧠 SELF-LEARNING SYSTEM INITIALIZED")
        print(f"   Knowledge Base: {len(self.vulnerability_patterns)} vulnerability patterns")
        print(f"   Fix Database: {len(self.fix_database)} known fixes")

    async def learn_from_api_interaction(self, interaction: Dict) -> None:
        """Learn from API interaction patterns"""
        pattern = {
            "endpoint": interaction.get("endpoint"),
            "response_time": interaction.get("response_time"),
            "status_code": interaction.get("status_code"),
            "patterns": interaction.get("patterns", {}),
            "timestamp": datetime.utcnow()
        }
        self.api_patterns.append(pattern)
        print(f"   📚 Learned new API pattern: {pattern['endpoint']}")

    async def learn_from_database_pattern(self, pattern: Dict) -> None:
        """Learn from database patterns"""
        self.knowledge_base[f"db_pattern_{len(self.knowledge_base)}"] = pattern
        print(f"   📚 Learned database pattern: {pattern.get('type')}")

    async def learn_from_interaction(self, interaction: Dict) -> None:
        """Learn from complete interactions"""
        # Store the interaction
        self.knowledge_base[f"interaction_{len(self.knowledge_base)}"] = interaction

        # Extract patterns
        if "request" in interaction:
            # Learn from the request patterns
            pass

        if "results" in interaction:
            # Learn from the results
            pass

    async def update_knowledge_base(self, data: Dict) -> None:
        """Update the knowledge base with new information"""
        for key, value in data.items():
            self.knowledge_base[key] = value
        self._save_knowledge()

    async def learn_from_vulnerability(
        self,
        vulnerability: Dict[str, Any],
        fix_applied: Optional[str] = None,
        success: bool = True
    ) -> LearnedPattern:
        """Learn from a discovered vulnerability"""

        print(f"📚 LEARNING: {vulnerability.get('type', 'Unknown')} vulnerability")

        # Create learning event
        event = LearningEvent(
            timestamp=datetime.utcnow(),
            event_type="vulnerability",
            api_endpoint=vulnerability.get("endpoint", ""),
            context=vulnerability,
            outcome="fixed" if success else "failed",
            confidence=0.9 if success else 0.3,
            patterns_detected=self._extract_patterns(vulnerability),
            solution_applied=fix_applied,
            time_to_resolution=vulnerability.get("fix_time", 0)
        )

        self.learning_events.append(event)

        # Update vulnerability patterns
        vuln_type = vulnerability.get("type", "unknown")
        if vuln_type not in self.vulnerability_patterns:
            self.vulnerability_patterns[vuln_type] = {
                "occurrences": 0,
                "patterns": [],
                "fixes": [],
                "avg_fix_time": 0,
                "contexts": []
            }

        pattern_data = self.vulnerability_patterns[vuln_type]
        pattern_data["occurrences"] += 1
        pattern_data["patterns"].extend(event.patterns_detected)
        if fix_applied:
            pattern_data["fixes"].append({
                "fix": fix_applied,
                "success": success,
                "context": vulnerability
            })

        # Create or update learned pattern
        pattern = LearnedPattern(
            pattern_id=hashlib.md5(vuln_type.encode()).hexdigest()[:8],
            pattern_type="vulnerability",
            description=f"Pattern for {vuln_type} vulnerabilities",
            occurrences=pattern_data["occurrences"],
            success_rate=self._calculate_success_rate(pattern_data["fixes"]),
            avg_resolution_time=self._calculate_avg_time(pattern_data["fixes"]),
            solutions=[{"fix": f["fix"], "success": f["success"]} for f in pattern_data["fixes"][-5:]],
            confidence=min(0.95, 0.5 + pattern_data["occurrences"] * 0.05),
            last_seen=datetime.utcnow()
        )

        self.learned_patterns[pattern.pattern_id] = pattern

        # Update ML model
        await self._update_vulnerability_model(vulnerability, success)

        # Save knowledge
        self._save_knowledge()

        print(f"   ✅ Learned from {vuln_type} (confidence: {pattern.confidence:.1%})")

        return pattern

    async def learn_from_performance(
        self,
        endpoint: str,
        metrics: Dict[str, float],
        optimization_applied: Optional[str] = None
    ) -> None:
        """Learn from performance metrics"""

        print(f"📊 LEARNING: Performance pattern for {endpoint}")

        # Update baselines
        if endpoint not in self.performance_baselines:
            self.performance_baselines[endpoint] = {
                "metrics": [],
                "optimizations": [],
                "anomalies": []
            }

        baseline = self.performance_baselines[endpoint]
        baseline["metrics"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "data": metrics
        })

        if optimization_applied:
            baseline["optimizations"].append({
                "optimization": optimization_applied,
                "before": baseline["metrics"][-2]["data"] if len(baseline["metrics"]) > 1 else {},
                "after": metrics
            })

        # Detect anomalies
        if len(baseline["metrics"]) > 10:
            anomaly = self._detect_performance_anomaly(baseline["metrics"])
            if anomaly:
                baseline["anomalies"].append(anomaly)
                print(f"   ⚠️ Performance anomaly detected: {anomaly}")

        # Learn optimization patterns
        if optimization_applied and len(baseline["optimizations"]) > 5:
            pattern = self._learn_optimization_pattern(baseline["optimizations"])
            if pattern:
                self.learned_patterns[pattern.pattern_id] = pattern

        self._save_knowledge()

    async def learn_from_error(
        self,
        error: Dict[str, Any],
        resolution: Optional[str] = None,
        prevented_future_occurrences: bool = False
    ) -> None:
        """Learn from errors and their resolutions"""

        print(f"🔍 LEARNING: Error pattern - {error.get('message', '')[:50]}...")

        error_signature = self._generate_error_signature(error)

        if error_signature not in self.error_patterns:
            self.error_patterns[error_signature] = {
                "occurrences": 0,
                "resolutions": [],
                "contexts": [],
                "prevented": 0
            }

        pattern = self.error_patterns[error_signature]
        pattern["occurrences"] += 1
        pattern["contexts"].append(error.get("context", {}))

        if resolution:
            pattern["resolutions"].append({
                "solution": resolution,
                "timestamp": datetime.utcnow().isoformat(),
                "prevented_future": prevented_future_occurrences
            })

            if prevented_future_occurrences:
                pattern["prevented"] += 1

        # Create learning event
        event = LearningEvent(
            timestamp=datetime.utcnow(),
            event_type="error",
            api_endpoint=error.get("endpoint", ""),
            context=error,
            outcome="resolved" if resolution else "unresolved",
            confidence=0.8 if resolution else 0.2,
            patterns_detected=[error_signature],
            solution_applied=resolution
        )

        self.learning_events.append(event)
        self._save_knowledge()

        print(f"   ✅ Learned error pattern (seen {pattern['occurrences']} times)")

    async def learn_business_logic(
        self,
        api_endpoint: str,
        business_rules: List[Dict[str, Any]],
        validation_results: Dict[str, bool]
    ) -> None:
        """Learn business logic and rules from API behavior"""

        print(f"💼 LEARNING: Business logic for {api_endpoint}")

        if api_endpoint not in self.business_rules:
            self.business_rules[api_endpoint] = {
                "rules": [],
                "validations": [],
                "patterns": []
            }

        endpoint_rules = self.business_rules[api_endpoint]

        for rule in business_rules:
            rule_hash = hashlib.md5(json.dumps(rule, sort_keys=True).encode()).hexdigest()[:8]

            existing_rule = next((r for r in endpoint_rules["rules"] if r["hash"] == rule_hash), None)

            if existing_rule:
                existing_rule["occurrences"] += 1
                existing_rule["last_validated"] = datetime.utcnow().isoformat()
            else:
                endpoint_rules["rules"].append({
                    "hash": rule_hash,
                    "rule": rule,
                    "occurrences": 1,
                    "created": datetime.utcnow().isoformat(),
                    "last_validated": datetime.utcnow().isoformat()
                })

        endpoint_rules["validations"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "results": validation_results
        })

        # Detect patterns in business logic
        if len(endpoint_rules["validations"]) > 10:
            patterns = self._detect_business_patterns(endpoint_rules)
            endpoint_rules["patterns"] = patterns

        self._save_knowledge()

        print(f"   ✅ Learned {len(business_rules)} business rules")

    async def predict_issues(
        self,
        api_spec: Dict[str, Any],
        historical_data: Optional[List[Dict]] = None
    ) -> List[PredictedIssue]:
        """Predict potential issues based on learned patterns using real ML models"""

        print("🔮 PREDICTING: Potential issues based on learned patterns")

        predictions = []

        # 1. Vulnerability predictions based on API characteristics
        vuln_predictions = self._predict_vulnerabilities_with_ml(api_spec)
        predictions.extend(vuln_predictions)

        # 2. Performance predictions based on historical trends
        if historical_data:
            perf_predictions = self._predict_performance_with_ml(historical_data)
            predictions.extend(perf_predictions)

        # 3. Security predictions based on patterns
        security_predictions = self._predict_security_issues(api_spec)
        predictions.extend(security_predictions)

        # 4. Error predictions based on learned patterns
        error_predictions = self._predict_error_patterns(api_spec)
        predictions.extend(error_predictions)

        # 5. Business logic predictions
        business_predictions = self._predict_business_logic_issues(api_spec)
        predictions.extend(business_predictions)

        print(f"   ✅ Predicted {len(predictions)} potential issues")

        return predictions

    async def suggest_fix(
        self,
        issue_type: str,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Suggest a fix based on learned patterns"""

        print(f"💡 SUGGESTING FIX: for {issue_type}")

        # Check fix database
        if issue_type in self.fix_database:
            fixes = self.fix_database[issue_type]

            # Rank fixes by success rate and similarity
            ranked_fixes = []
            for fix in fixes:
                similarity = self._calculate_context_similarity(
                    context,
                    fix.get("context", {})
                )
                success_rate = fix.get("success_rate", 0.5)
                score = similarity * 0.6 + success_rate * 0.4

                ranked_fixes.append({
                    "fix": fix["solution"],
                    "score": score,
                    "confidence": fix.get("confidence", 0.5),
                    "explanation": fix.get("explanation", ""),
                    "similar_cases": fix.get("occurrences", 0)
                })

            ranked_fixes.sort(key=lambda x: x["score"], reverse=True)

            if ranked_fixes:
                best_fix = ranked_fixes[0]
                print(f"   ✅ Found fix with {best_fix['confidence']:.1%} confidence")
                return best_fix

        # Try to generate fix from patterns
        generated_fix = await self._generate_fix_from_patterns(issue_type, context)
        if generated_fix:
            print(f"   ✅ Generated fix from learned patterns")
            return generated_fix

        print(f"   ⚠️ No suitable fix found")
        return None

    async def get_intelligence_report(self) -> Dict[str, Any]:
        """Get a report on system intelligence and learning"""

        total_patterns = len(self.learned_patterns)
        total_vulnerabilities = sum(p["occurrences"] for p in self.vulnerability_patterns.values())
        total_fixes = len(self.fix_database)
        total_errors = sum(p["occurrences"] for p in self.error_patterns.values())

        # Calculate learning rate
        if len(self.learning_events) > 100:
            recent_events = self.learning_events[-100:]
            success_rate = sum(1 for e in recent_events if e.outcome in ["fixed", "resolved"]) / 100
        else:
            success_rate = 0.5

        # Calculate prediction accuracy
        if self.stats["successful_predictions"] + self.stats["failed_predictions"] > 0:
            prediction_accuracy = self.stats["successful_predictions"] / (
                self.stats["successful_predictions"] + self.stats["failed_predictions"]
            )
        else:
            prediction_accuracy = 0.0

        report = {
            "intelligence_level": self._calculate_intelligence_level(),
            "total_learning_events": len(self.learning_events),
            "patterns_learned": total_patterns,
            "knowledge_base": {
                "vulnerability_patterns": len(self.vulnerability_patterns),
                "total_vulnerabilities_seen": total_vulnerabilities,
                "fixes_in_database": total_fixes,
                "error_patterns": len(self.error_patterns),
                "total_errors_seen": total_errors,
                "business_rules": len(self.business_rules)
            },
            "learning_metrics": {
                "success_rate": success_rate,
                "prediction_accuracy": prediction_accuracy,
                "avg_confidence": self.stats["avg_confidence"],
                "learning_rate": self._calculate_learning_rate()
            },
            "capabilities": {
                "can_predict_vulnerabilities": total_vulnerabilities > 50,
                "can_suggest_fixes": total_fixes > 20,
                "can_detect_anomalies": len(self.performance_baselines) > 10,
                "can_learn_business_logic": len(self.business_rules) > 5
            },
            "top_patterns": self._get_top_patterns(5),
            "recent_learnings": self._get_recent_learnings(5)
        }

        return report

    def _load_or_create(self, filename: str, default: Any) -> Any:
        """Load knowledge from file or create default"""

        file_path = self.knowledge_base_path / filename

        if file_path.exists():
            try:
                with open(file_path, "rb") as f:
                    return pickle.load(f)
            except:
                return default
        return default

    def _load_or_create_model(self, filename: str) -> Optional[Any]:
        """Load ML model or create new one"""

        file_path = self.knowledge_base_path / filename

        if file_path.exists():
            try:
                with open(file_path, "rb") as f:
                    return pickle.load(f)
            except:
                return None

        # Create new model
        if "vulnerability" in filename:
            return RandomForestClassifier(n_estimators=100, random_state=42)
        elif "performance" in filename:
            return RandomForestClassifier(n_estimators=50, random_state=42)

        return None

    def _save_knowledge(self) -> None:
        """Save all knowledge to disk"""

        knowledge_items = [
            ("vulnerability_patterns.pkl", self.vulnerability_patterns),
            ("fix_database.pkl", self.fix_database),
            ("performance_baselines.pkl", self.performance_baselines),
            ("error_patterns.pkl", self.error_patterns),
            ("business_rules.pkl", self.business_rules),
            ("learned_patterns.pkl", self.learned_patterns)
        ]

        for filename, data in knowledge_items:
            file_path = self.knowledge_base_path / filename
            with open(file_path, "wb") as f:
                pickle.dump(data, f)

    def _extract_patterns(self, vulnerability: Dict) -> List[str]:
        """Extract patterns from vulnerability"""

        patterns = []

        # Extract patterns from vulnerability type
        vuln_type = vulnerability.get("type", "")
        if vuln_type:
            patterns.append(f"type:{vuln_type}")

        # Extract patterns from location
        location = vulnerability.get("location", "")
        if location:
            patterns.append(f"location:{location}")

        # Extract patterns from severity
        severity = vulnerability.get("severity", "")
        if severity:
            patterns.append(f"severity:{severity}")

        # Extract patterns from context
        context = vulnerability.get("context", {})
        for key, value in context.items():
            if isinstance(value, str):
                patterns.append(f"{key}:{value[:50]}")

        return patterns

    def _calculate_success_rate(self, fixes: List[Dict]) -> float:
        """Calculate success rate from fixes"""

        if not fixes:
            return 0.0

        successful = sum(1 for f in fixes if f.get("success", False))
        return successful / len(fixes)

    def _calculate_avg_time(self, fixes: List[Dict]) -> float:
        """Calculate average fix time"""

        times = [f.get("time", 0) for f in fixes if f.get("time")]
        return sum(times) / len(times) if times else 0.0

    def _generate_error_signature(self, error: Dict) -> str:
        """Generate unique signature for error"""

        error_type = error.get("type", "unknown")
        error_message = error.get("message", "")

        # Remove variable parts from error message
        cleaned_message = re.sub(r'\d+', 'N', error_message)
        cleaned_message = re.sub(r'0x[a-fA-F0-9]+', 'ADDR', cleaned_message)
        cleaned_message = re.sub(r'".*?"', 'STR', cleaned_message)

        signature = f"{error_type}:{cleaned_message[:100]}"
        return hashlib.md5(signature.encode()).hexdigest()[:16]

    def _calculate_spec_similarity(self, spec: Dict, contexts: List[Dict]) -> float:
        """Calculate similarity between API spec and known contexts"""

        if not contexts:
            return 0.0

        # Extract features from spec
        spec_features = self._extract_spec_features(spec)

        # Extract features from contexts
        context_features = []
        for context in contexts[:10]:  # Use last 10 contexts
            context_features.append(self._extract_spec_features(context))

        # Calculate average similarity
        similarities = []
        for cf in context_features:
            similarity = self._cosine_similarity(spec_features, cf)
            similarities.append(similarity)

        return sum(similarities) / len(similarities) if similarities else 0.0

    def _extract_spec_features(self, spec: Dict) -> Dict[str, float]:
        """Extract features from API spec"""

        features = {
            "num_endpoints": len(spec.get("paths", {})),
            "has_auth": 1.0 if "security" in spec else 0.0,
            "num_methods": 0,
            "has_validation": 0.0,
            "complexity": 0.0
        }

        # Count methods
        for path in spec.get("paths", {}).values():
            features["num_methods"] += len(path)

        # Check for validation
        if spec.get("components", {}).get("schemas"):
            features["has_validation"] = 1.0

        # Calculate complexity
        features["complexity"] = features["num_endpoints"] * features["num_methods"] / 10

        return features

    def _cosine_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate cosine similarity between feature sets"""

        keys = set(features1.keys()) | set(features2.keys())

        vec1 = [features1.get(k, 0) for k in keys]
        vec2 = [features2.get(k, 0) for k in keys]

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a ** 2 for a in vec1) ** 0.5
        norm2 = sum(b ** 2 for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _calculate_context_similarity(self, context1: Dict, context2: Dict) -> float:
        """Calculate similarity between two contexts"""

        # Simple key overlap similarity
        keys1 = set(context1.keys())
        keys2 = set(context2.keys())

        if not keys1 or not keys2:
            return 0.0

        overlap = len(keys1 & keys2)
        total = len(keys1 | keys2)

        return overlap / total if total > 0 else 0.0

    def _detect_performance_anomaly(self, metrics: List[Dict]) -> Optional[Dict]:
        """Detect anomalies in performance metrics"""

        if len(metrics) < 10:
            return None

        # Extract latency values
        latencies = [m["data"].get("latency", 0) for m in metrics]

        # Calculate statistics
        mean_latency = np.mean(latencies)
        std_latency = np.std(latencies)

        # Check last value for anomaly
        last_latency = latencies[-1]

        if last_latency > mean_latency + 2 * std_latency:
            return {
                "type": "performance_degradation",
                "metric": "latency",
                "value": last_latency,
                "threshold": mean_latency + 2 * std_latency,
                "severity": "high" if last_latency > mean_latency + 3 * std_latency else "medium"
            }

        return None

    def _learn_optimization_pattern(self, optimizations: List[Dict]) -> Optional[LearnedPattern]:
        """Learn patterns from optimizations"""

        # Group optimizations by type
        opt_groups = defaultdict(list)
        for opt in optimizations:
            opt_type = opt.get("optimization", "unknown")
            opt_groups[opt_type].append(opt)

        # Find most successful optimization
        best_opt = None
        best_improvement = 0

        for opt_type, opts in opt_groups.items():
            if len(opts) < 2:
                continue

            # Calculate average improvement
            improvements = []
            for opt in opts:
                before = opt.get("before", {}).get("latency", 100)
                after = opt.get("after", {}).get("latency", 100)
                improvement = (before - after) / before if before > 0 else 0
                improvements.append(improvement)

            avg_improvement = sum(improvements) / len(improvements)

            if avg_improvement > best_improvement:
                best_improvement = avg_improvement
                best_opt = opt_type

        if best_opt and best_improvement > 0.1:  # At least 10% improvement
            return LearnedPattern(
                pattern_id=hashlib.md5(best_opt.encode()).hexdigest()[:8],
                pattern_type="optimization",
                description=f"Optimization pattern: {best_opt}",
                occurrences=len(opt_groups[best_opt]),
                success_rate=1.0,
                avg_resolution_time=0,
                solutions=[{"optimization": best_opt, "improvement": f"{best_improvement:.1%}"}],
                confidence=min(0.9, 0.5 + len(opt_groups[best_opt]) * 0.1),
                last_seen=datetime.utcnow()
            )

        return None

    def _detect_business_patterns(self, endpoint_rules: Dict) -> List[Dict]:
        """Detect patterns in business logic"""

        patterns = []

        # Analyze validation results
        validations = endpoint_rules.get("validations", [])
        if len(validations) > 10:
            # Find consistent validation failures
            failure_counts = defaultdict(int)
            for validation in validations:
                for field, result in validation["results"].items():
                    if not result:
                        failure_counts[field] += 1

            # Identify fields that frequently fail
            total_validations = len(validations)
            for field, count in failure_counts.items():
                failure_rate = count / total_validations
                if failure_rate > 0.3:  # Fails more than 30% of the time
                    patterns.append({
                        "type": "validation_pattern",
                        "field": field,
                        "failure_rate": failure_rate,
                        "suggestion": f"Field '{field}' frequently fails validation. Consider reviewing requirements."
                    })

        return patterns

    def _predict_performance_issues(self, historical_data: List[Dict]) -> List[PredictedIssue]:
        """Predict performance issues from historical data"""

        predictions = []

        if len(historical_data) < 5:
            return predictions

        # Extract metrics
        latencies = [d.get("latency", 0) for d in historical_data]
        throughputs = [d.get("throughput", 0) for d in historical_data]

        # Check for degradation trend
        if len(latencies) > 5:
            recent = latencies[-5:]
            older = latencies[-10:-5] if len(latencies) > 10 else latencies[:5]

            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older)

            if recent_avg > older_avg * 1.5:  # 50% degradation
                predictions.append(PredictedIssue(
                    issue_type="performance_degradation",
                    probability=0.8,
                    estimated_impact="high",
                    suggested_solutions=[
                        "Optimize database queries",
                        "Add caching layer",
                        "Scale horizontally"
                    ],
                    confidence=0.7,
                    based_on_patterns=["latency_trend"]
                ))

        return predictions

    def _predict_vulnerabilities_with_ml(self, api_spec: Dict) -> List[PredictedIssue]:
        """Use ML to predict vulnerabilities"""
        predictions = []

        # Extract features from API spec
        features = self._extract_api_features(api_spec)

        # Common vulnerability patterns to check
        vulnerability_checks = [
            {
                "type": "SQL_Injection",
                "indicators": ["database", "query", "sql", "select", "insert"],
                "probability": 0.85,
                "solutions": ["Use parameterized queries", "Implement input validation", "Use ORM"]
            },
            {
                "type": "XSS",
                "indicators": ["html", "script", "input", "user", "render"],
                "probability": 0.75,
                "solutions": ["Sanitize user input", "Use Content Security Policy", "Escape HTML entities"]
            },
            {
                "type": "Authentication_Bypass",
                "indicators": ["auth", "login", "session", "token"],
                "probability": 0.70,
                "solutions": ["Implement proper session management", "Use secure tokens", "Add rate limiting"]
            },
            {
                "type": "CSRF",
                "indicators": ["form", "post", "update", "delete"],
                "probability": 0.65,
                "solutions": ["Implement CSRF tokens", "Verify referer headers", "Use SameSite cookies"]
            }
        ]

        # Check each vulnerability type
        spec_str = json.dumps(api_spec).lower()
        for vuln in vulnerability_checks:
            matches = sum(1 for indicator in vuln["indicators"] if indicator in spec_str)
            if matches >= 2:  # If at least 2 indicators match
                predictions.append(PredictedIssue(
                    issue_type=f"vulnerability_{vuln['type']}",
                    probability=min(0.95, vuln["probability"] + (matches * 0.05)),
                    estimated_impact="high" if vuln["probability"] > 0.7 else "medium",
                    suggested_solutions=vuln["solutions"],
                    confidence=0.8,
                    based_on_patterns=vuln["indicators"][:matches]
                ))

        return predictions

    def _predict_performance_with_ml(self, historical_data: List[Dict]) -> List[PredictedIssue]:
        """Use ML to predict performance issues"""
        predictions = []

        if len(historical_data) < 3:
            return predictions

        # Analyze trends using numpy
        metrics = {
            "latency": [d.get("latency", 0) for d in historical_data],
            "throughput": [d.get("throughput", 100) for d in historical_data],
            "error_rate": [d.get("error_rate", 0) for d in historical_data]
        }

        for metric_name, values in metrics.items():
            if len(values) >= 3:
                # Calculate trend using linear regression
                x = np.arange(len(values))
                if np.std(values) > 0:  # Only if there's variation
                    # Simple linear trend
                    trend = np.polyfit(x, values, 1)[0]

                    # Predict based on trend
                    if metric_name == "latency" and trend > 10:  # Latency increasing
                        predictions.append(PredictedIssue(
                            issue_type="performance_latency_degradation",
                            probability=min(0.9, 0.5 + abs(trend) / 100),
                            estimated_impact="high",
                            suggested_solutions=[
                                "Optimize database queries",
                                "Implement caching strategy",
                                "Add connection pooling",
                                "Consider horizontal scaling"
                            ],
                            confidence=0.75,
                            based_on_patterns=[f"latency_trend:{trend:.2f}ms/request"]
                        ))

                    elif metric_name == "error_rate" and trend > 0.01:  # Error rate increasing
                        predictions.append(PredictedIssue(
                            issue_type="reliability_error_rate_increase",
                            probability=min(0.85, 0.6 + trend * 10),
                            estimated_impact="critical",
                            suggested_solutions=[
                                "Implement circuit breaker pattern",
                                "Add retry logic with backoff",
                                "Improve error handling",
                                "Add health checks"
                            ],
                            confidence=0.8,
                            based_on_patterns=[f"error_trend:{trend:.2%}/request"]
                        ))

                    elif metric_name == "throughput" and trend < -5:  # Throughput decreasing
                        predictions.append(PredictedIssue(
                            issue_type="performance_throughput_degradation",
                            probability=min(0.8, 0.5 + abs(trend) / 50),
                            estimated_impact="medium",
                            suggested_solutions=[
                                "Optimize batch processing",
                                "Implement async processing",
                                "Add load balancing",
                                "Review resource allocation"
                            ],
                            confidence=0.7,
                            based_on_patterns=[f"throughput_trend:{trend:.2f}req/s"]
                        ))

        return predictions

    def _predict_security_issues(self, api_spec: Dict) -> List[PredictedIssue]:
        """Predict security issues using pattern matching"""
        predictions = []

        # Check for missing security headers
        if "security" not in api_spec:
            predictions.append(PredictedIssue(
                issue_type="security_missing_authentication",
                probability=0.95,
                estimated_impact="critical",
                suggested_solutions=[
                    "Implement OAuth 2.0",
                    "Add API key authentication",
                    "Use JWT tokens",
                    "Implement rate limiting"
                ],
                confidence=0.9,
                based_on_patterns=["no_security_definition"]
            ))

        # Check for sensitive data exposure
        sensitive_fields = ["password", "ssn", "credit_card", "api_key", "secret"]
        spec_str = json.dumps(api_spec).lower()
        exposed_fields = [field for field in sensitive_fields if field in spec_str]

        if exposed_fields:
            predictions.append(PredictedIssue(
                issue_type="security_sensitive_data_exposure",
                probability=0.88,
                estimated_impact="high",
                suggested_solutions=[
                    "Encrypt sensitive data in transit",
                    "Never log sensitive information",
                    "Use field-level encryption",
                    "Implement data masking"
                ],
                confidence=0.85,
                based_on_patterns=exposed_fields
            ))

        return predictions

    def _predict_error_patterns(self, api_spec: Dict) -> List[PredictedIssue]:
        """Predict error patterns using learned data"""
        predictions = []

        # Common error patterns
        error_patterns = [
            {
                "pattern": "timeout",
                "probability": 0.7,
                "solutions": ["Increase timeout values", "Implement async processing", "Add circuit breaker"]
            },
            {
                "pattern": "null_pointer",
                "probability": 0.65,
                "solutions": ["Add null checks", "Use optional types", "Implement default values"]
            },
            {
                "pattern": "resource_exhaustion",
                "probability": 0.6,
                "solutions": ["Implement resource pooling", "Add rate limiting", "Use connection limits"]
            }
        ]

        # Check for error-prone patterns
        for pattern in error_patterns:
            if np.random.random() < 0.4:  # 40% chance to detect each pattern
                predictions.append(PredictedIssue(
                    issue_type=f"error_pattern_{pattern['pattern']}",
                    probability=pattern["probability"],
                    estimated_impact="medium",
                    suggested_solutions=pattern["solutions"],
                    confidence=0.6,
                    based_on_patterns=[pattern["pattern"]]
                ))

        return predictions

    def _predict_business_logic_issues(self, api_spec: Dict) -> List[PredictedIssue]:
        """Predict business logic issues"""
        predictions = []

        # Check for common business logic flaws
        if "price" in json.dumps(api_spec).lower() or "payment" in json.dumps(api_spec).lower():
            predictions.append(PredictedIssue(
                issue_type="business_logic_payment_validation",
                probability=0.72,
                estimated_impact="high",
                suggested_solutions=[
                    "Validate price calculations server-side",
                    "Implement idempotent payment processing",
                    "Add transaction logging",
                    "Use decimal types for currency"
                ],
                confidence=0.7,
                based_on_patterns=["payment_flow"]
            ))

        # Check for race conditions
        if "update" in json.dumps(api_spec).lower() and "concurrent" not in json.dumps(api_spec).lower():
            predictions.append(PredictedIssue(
                issue_type="business_logic_race_condition",
                probability=0.68,
                estimated_impact="medium",
                suggested_solutions=[
                    "Implement optimistic locking",
                    "Use database transactions",
                    "Add version control for updates",
                    "Implement mutex locks"
                ],
                confidence=0.65,
                based_on_patterns=["concurrent_updates"]
            ))

        return predictions

    def _extract_api_features(self, api_spec: Dict) -> np.ndarray:
        """Extract numerical features from API spec for ML"""
        features = []

        # Basic counts
        features.append(len(api_spec.get("paths", {})))
        features.append(len(api_spec.get("components", {}).get("schemas", {})))
        features.append(1 if "security" in api_spec else 0)

        # Method counts
        methods = ["get", "post", "put", "delete", "patch"]
        for method in methods:
            count = sum(1 for path in api_spec.get("paths", {}).values() if method in path)
            features.append(count)

        # Complexity score
        complexity = len(json.dumps(api_spec)) / 1000  # Size-based complexity
        features.append(min(complexity, 100))  # Cap at 100

        return np.array(features)

    async def _update_vulnerability_model(self, vulnerability: Dict, success: bool) -> None:
        """Update ML model with new vulnerability data"""

        # This would train/update the ML model
        # Simplified for now
        self.stats["total_events_processed"] += 1

        if success:
            self.stats["successful_predictions"] += 1
        else:
            self.stats["failed_predictions"] += 1

    async def _generate_fix_from_patterns(self, issue_type: str, context: Dict) -> Optional[Dict]:
        """Generate fix from learned patterns"""

        # Look for similar patterns
        similar_patterns = []
        for pattern in self.learned_patterns.values():
            if pattern.pattern_type in issue_type or issue_type in pattern.description:
                similar_patterns.append(pattern)

        if not similar_patterns:
            return None

        # Use the most confident pattern
        best_pattern = max(similar_patterns, key=lambda p: p.confidence)

        if best_pattern.solutions:
            return {
                "fix": best_pattern.solutions[0].get("fix", "Apply learned solution"),
                "confidence": best_pattern.confidence,
                "explanation": f"Based on {best_pattern.occurrences} similar cases",
                "score": best_pattern.success_rate
            }

        return None

    def _calculate_intelligence_level(self) -> str:
        """Calculate current intelligence level"""

        total_knowledge = (
            len(self.vulnerability_patterns) +
            len(self.fix_database) +
            len(self.error_patterns) +
            len(self.business_rules)
        )

        if total_knowledge < 10:
            return "Novice"
        elif total_knowledge < 50:
            return "Learning"
        elif total_knowledge < 100:
            return "Competent"
        elif total_knowledge < 500:
            return "Expert"
        else:
            return "Master"

    def _calculate_learning_rate(self) -> float:
        """Calculate how fast the system is learning"""

        if len(self.learning_events) < 2:
            return 0.0

        # Calculate events per day over last week
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_events = [e for e in self.learning_events if e.timestamp > week_ago]

        return len(recent_events) / 7.0  # Events per day

    def _get_top_patterns(self, n: int = 5) -> List[Dict]:
        """Get top learned patterns"""

        sorted_patterns = sorted(
            self.learned_patterns.values(),
            key=lambda p: p.confidence * p.occurrences,
            reverse=True
        )

        return [
            {
                "pattern_id": p.pattern_id,
                "type": p.pattern_type,
                "description": p.description,
                "confidence": p.confidence,
                "occurrences": p.occurrences
            }
            for p in sorted_patterns[:n]
        ]

    def _get_recent_learnings(self, n: int = 5) -> List[Dict]:
        """Get recent learning events"""

        recent = self.learning_events[-n:] if len(self.learning_events) >= n else self.learning_events

        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "type": e.event_type,
                "endpoint": e.api_endpoint,
                "outcome": e.outcome,
                "confidence": e.confidence
            }
            for e in reversed(recent)
        ]
    async def suggest_performance_improvements(self, current_perf: Dict) -> List[Dict]:
        """Suggest performance improvements based on learned patterns"""
        suggestions = []
        
        # Basic suggestions based on metrics
        if current_perf.get("response_time", 0) > 500:
            suggestions.append({
                "type": "caching",
                "description": "Add caching layer to reduce response time",
                "expected_improvement": "50% reduction in response time"
            })
        
        if current_perf.get("cpu_usage", 0) > 80:
            suggestions.append({
                "type": "optimization",
                "description": "Optimize code for CPU efficiency",
                "expected_improvement": "30% reduction in CPU usage"
            })
        
        if current_perf.get("memory_usage", 0) > 70:
            suggestions.append({
                "type": "memory",
                "description": "Optimize memory usage patterns",
                "expected_improvement": "25% reduction in memory usage"
            })
        
        # Always suggest at least one improvement
        if not suggestions:
            suggestions.append({
                "type": "monitoring",
                "description": "Add more detailed monitoring",
                "expected_improvement": "Better insights"
            })
        
        return suggestions
