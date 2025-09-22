#!/usr/bin/env python3
"""
Advanced ML Models for Smart API Discovery
Deep learning models for API pattern recognition, behavior prediction, and anomaly detection
"""

import asyncio
import logging
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re
import hashlib
from collections import defaultdict, deque
import pickle
import os

# Optional deep learning imports
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    HAS_PYTORCH = True
except ImportError:
    HAS_PYTORCH = False

try:
    import tensorflow as tf
    from tensorflow.keras import layers, models, callbacks
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, accuracy_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

class ModelType(Enum):
    PATTERN_RECOGNITION = "pattern_recognition"
    BEHAVIOR_PREDICTION = "behavior_prediction"
    ANOMALY_DETECTION = "anomaly_detection"
    ENDPOINT_CLUSTERING = "endpoint_clustering"
    PARAMETER_PREDICTION = "parameter_prediction"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_PREDICTION = "performance_prediction"

@dataclass
class APIFeature:
    """Feature vector for ML models"""
    url_length: int
    path_depth: int
    has_parameters: bool
    has_versioning: bool
    method_type: str
    response_time: float
    status_code: int
    payload_size: int
    authentication_required: bool
    ssl_enabled: bool

    # Advanced features
    url_entropy: float
    parameter_count: int
    subdomain_count: int
    path_segments: List[str]
    query_parameters: Dict[str, str]
    headers: Dict[str, str]

    # Behavioral features
    request_frequency: float
    error_rate: float
    response_time_variance: float
    peak_usage_hours: List[int]

    # Security features
    has_auth_header: bool
    uses_https: bool
    has_cors_headers: bool
    rate_limited: bool

@dataclass
class ModelPrediction:
    """ML model prediction result"""
    model_type: ModelType
    prediction: Any
    confidence: float
    features_used: List[str]
    model_version: str
    prediction_timestamp: datetime = field(default_factory=datetime.utcnow)
    explanation: Optional[str] = None

class APIPatternRecognitionModel:
    """Deep learning model for API pattern recognition"""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.label_encoder = LabelEncoder()
        self.feature_scaler = StandardScaler()
        self.is_trained = False

    async def train_model(self, training_data: List[Dict[str, Any]]):
        """Train the pattern recognition model"""
        if not HAS_SKLEARN:
            logging.warning("Scikit-learn not available for pattern recognition")
            return

        logging.info("🧠 Training API pattern recognition model")

        # Prepare features and labels
        features, labels = self._prepare_training_data(training_data)

        if len(features) < 10:
            logging.warning("Insufficient training data for pattern recognition")
            return

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=0.2, random_state=42
        )

        # Scale features
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        X_test_scaled = self.feature_scaler.transform(X_test)

        # Train Random Forest model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )

        self.model.fit(X_train_scaled, y_train)

        # Evaluate model
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)

        logging.info(f"✅ Pattern recognition model trained with accuracy: {accuracy:.3f}")
        self.is_trained = True

    def _prepare_training_data(self, training_data: List[Dict[str, Any]]) -> Tuple[List[List[float]], List[str]]:
        """Prepare training features and labels"""
        features = []
        labels = []

        for item in training_data:
            feature_vector = self._extract_features(item)
            api_category = item.get('category', 'unknown')

            features.append(feature_vector)
            labels.append(api_category)

        return features, labels

    def _extract_features(self, api_data: Dict[str, Any]) -> List[float]:
        """Extract numerical features from API data"""
        url = api_data.get('url', '')
        method = api_data.get('method', 'GET')

        features = [
            len(url),  # URL length
            url.count('/'),  # Path depth
            1 if '?' in url else 0,  # Has parameters
            1 if re.search(r'/v\d+/', url) else 0,  # Has versioning
            hash(method) % 1000,  # Method hash
            api_data.get('response_time', 0),
            api_data.get('status_code', 200),
            api_data.get('payload_size', 0),
            1 if api_data.get('auth_required', False) else 0,
            1 if url.startswith('https') else 0,
            self._calculate_entropy(url),  # URL entropy
            url.count('='),  # Parameter count
            url.count('.'),  # Subdomain count
        ]

        return features

    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        if not text:
            return 0.0

        # Calculate frequency of each character
        char_counts = defaultdict(int)
        for char in text:
            char_counts[char] += 1

        # Calculate entropy
        entropy = 0.0
        text_len = len(text)
        for count in char_counts.values():
            if count > 0:
                probability = count / text_len
                entropy -= probability * np.log2(probability)

        return entropy

    async def predict_api_pattern(self, api_data: Dict[str, Any]) -> ModelPrediction:
        """Predict API pattern type"""
        if not self.is_trained or not self.model:
            return ModelPrediction(
                model_type=ModelType.PATTERN_RECOGNITION,
                prediction="unknown",
                confidence=0.0,
                features_used=[],
                model_version="1.0",
                explanation="Model not trained"
            )

        # Extract features
        features = self._extract_features(api_data)
        features_scaled = self.feature_scaler.transform([features])

        # Predict
        prediction = self.model.predict(features_scaled)[0]
        confidence = np.max(self.model.predict_proba(features_scaled)[0])

        return ModelPrediction(
            model_type=ModelType.PATTERN_RECOGNITION,
            prediction=prediction,
            confidence=float(confidence),
            features_used=['url_length', 'path_depth', 'has_parameters', 'entropy'],
            model_version="1.0"
        )

class BehaviorPredictionModel:
    """Model for predicting API behavior patterns"""

    def __init__(self):
        self.lstm_model = None
        self.sequence_length = 10
        self.is_trained = False

    async def train_behavior_model(self, traffic_data: List[Dict[str, Any]]):
        """Train behavior prediction model using LSTM"""
        if not HAS_TENSORFLOW:
            logging.warning("TensorFlow not available for behavior prediction")
            return

        logging.info("🧠 Training API behavior prediction model")

        # Prepare sequences
        sequences, targets = self._prepare_sequences(traffic_data)

        if len(sequences) < 50:
            logging.warning("Insufficient data for behavior prediction training")
            return

        # Build LSTM model
        self.lstm_model = self._build_lstm_model(sequences[0].shape[1])

        # Train model
        self.lstm_model.fit(
            np.array(sequences),
            np.array(targets),
            epochs=50,
            batch_size=32,
            validation_split=0.2,
            verbose=0
        )

        self.is_trained = True
        logging.info("✅ Behavior prediction model trained successfully")

    def _prepare_sequences(self, traffic_data: List[Dict[str, Any]]) -> Tuple[List, List]:
        """Prepare sequential data for LSTM training"""
        # Group traffic by endpoint
        endpoint_traffic = defaultdict(list)

        for item in traffic_data:
            endpoint = item.get('url', '')
            endpoint_traffic[endpoint].append({
                'timestamp': item.get('timestamp', datetime.utcnow()),
                'response_time': item.get('response_time', 0),
                'status_code': item.get('status_code', 200),
                'payload_size': item.get('payload_size', 0)
            })

        sequences = []
        targets = []

        for endpoint, traffic in endpoint_traffic.items():
            if len(traffic) < self.sequence_length + 1:
                continue

            # Sort by timestamp
            traffic.sort(key=lambda x: x['timestamp'])

            # Create sequences
            for i in range(len(traffic) - self.sequence_length):
                sequence = []
                for j in range(self.sequence_length):
                    sequence.append([
                        traffic[i + j]['response_time'],
                        traffic[i + j]['status_code'],
                        traffic[i + j]['payload_size']
                    ])

                target = traffic[i + self.sequence_length]['response_time']

                sequences.append(sequence)
                targets.append(target)

        return sequences, targets

    def _build_lstm_model(self, feature_count: int):
        """Build LSTM model architecture"""
        model = tf.keras.Sequential([
            layers.LSTM(50, return_sequences=True, input_shape=(self.sequence_length, feature_count)),
            layers.Dropout(0.2),
            layers.LSTM(50, return_sequences=False),
            layers.Dropout(0.2),
            layers.Dense(25),
            layers.Dense(1)
        ])

        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model

    async def predict_behavior(self, historical_data: List[Dict[str, Any]]) -> ModelPrediction:
        """Predict future API behavior"""
        if not self.is_trained or not self.lstm_model:
            return ModelPrediction(
                model_type=ModelType.BEHAVIOR_PREDICTION,
                prediction=0.0,
                confidence=0.0,
                features_used=[],
                model_version="1.0",
                explanation="Model not trained"
            )

        if len(historical_data) < self.sequence_length:
            return ModelPrediction(
                model_type=ModelType.BEHAVIOR_PREDICTION,
                prediction=0.0,
                confidence=0.5,
                features_used=[],
                model_version="1.0",
                explanation="Insufficient historical data"
            )

        # Prepare input sequence
        sequence = []
        for item in historical_data[-self.sequence_length:]:
            sequence.append([
                item.get('response_time', 0),
                item.get('status_code', 200),
                item.get('payload_size', 0)
            ])

        # Predict
        prediction = self.lstm_model.predict(np.array([sequence]))[0][0]

        return ModelPrediction(
            model_type=ModelType.BEHAVIOR_PREDICTION,
            prediction=float(prediction),
            confidence=0.8,  # Would be calculated based on prediction variance
            features_used=['response_time', 'status_code', 'payload_size'],
            model_version="1.0"
        )

class AnomalyDetectionModel:
    """Advanced anomaly detection for API behavior"""

    def __init__(self):
        self.autoencoder = None
        self.threshold = None
        self.feature_scaler = StandardScaler()
        self.is_trained = False

    async def train_anomaly_detector(self, normal_traffic: List[Dict[str, Any]]):
        """Train autoencoder for anomaly detection"""
        if not HAS_TENSORFLOW:
            logging.warning("TensorFlow not available for anomaly detection")
            return

        logging.info("🧠 Training API anomaly detection model")

        # Prepare features
        features = self._extract_anomaly_features(normal_traffic)

        if len(features) < 100:
            logging.warning("Insufficient data for anomaly detection training")
            return

        # Scale features
        features_scaled = self.feature_scaler.fit_transform(features)

        # Build autoencoder
        self.autoencoder = self._build_autoencoder(features_scaled.shape[1])

        # Train autoencoder
        history = self.autoencoder.fit(
            features_scaled,
            features_scaled,
            epochs=100,
            batch_size=32,
            validation_split=0.1,
            verbose=0
        )

        # Calculate threshold
        reconstructed = self.autoencoder.predict(features_scaled)
        mse = np.mean(np.power(features_scaled - reconstructed, 2), axis=1)
        self.threshold = np.percentile(mse, 95)  # 95th percentile as threshold

        self.is_trained = True
        logging.info("✅ Anomaly detection model trained successfully")

    def _extract_anomaly_features(self, traffic_data: List[Dict[str, Any]]) -> List[List[float]]:
        """Extract features for anomaly detection"""
        features = []

        for item in traffic_data:
            feature_vector = [
                item.get('response_time', 0),
                item.get('status_code', 200),
                item.get('payload_size', 0),
                len(item.get('url', '')),
                item.get('url', '').count('/'),
                1 if item.get('method', 'GET') == 'POST' else 0,
                1 if item.get('url', '').startswith('https') else 0,
                item.get('request_count', 1),
                item.get('error_rate', 0)
            ]
            features.append(feature_vector)

        return features

    def _build_autoencoder(self, input_dim: int):
        """Build autoencoder architecture"""
        # Encoder
        input_layer = layers.Input(shape=(input_dim,))
        encoded = layers.Dense(32, activation='relu')(input_layer)
        encoded = layers.Dense(16, activation='relu')(encoded)
        encoded = layers.Dense(8, activation='relu')(encoded)

        # Decoder
        decoded = layers.Dense(16, activation='relu')(encoded)
        decoded = layers.Dense(32, activation='relu')(decoded)
        decoded = layers.Dense(input_dim, activation='linear')(decoded)

        # Autoencoder model
        autoencoder = tf.keras.Model(input_layer, decoded)
        autoencoder.compile(optimizer='adam', loss='mse')

        return autoencoder

    async def detect_anomalies(self, traffic_data: List[Dict[str, Any]]) -> List[ModelPrediction]:
        """Detect anomalies in API traffic"""
        if not self.is_trained or not self.autoencoder:
            return []

        # Extract features
        features = self._extract_anomaly_features(traffic_data)
        if not features:
            return []

        # Scale features
        features_scaled = self.feature_scaler.transform(features)

        # Predict and calculate reconstruction error
        reconstructed = self.autoencoder.predict(features_scaled)
        mse = np.mean(np.power(features_scaled - reconstructed, 2), axis=1)

        # Identify anomalies
        anomalies = []
        for i, error in enumerate(mse):
            if error > self.threshold:
                anomaly_score = min(error / self.threshold, 2.0)  # Cap at 2.0

                anomalies.append(ModelPrediction(
                    model_type=ModelType.ANOMALY_DETECTION,
                    prediction={
                        "is_anomaly": True,
                        "anomaly_score": float(anomaly_score),
                        "reconstruction_error": float(error),
                        "data_point": traffic_data[i]
                    },
                    confidence=min(anomaly_score, 1.0),
                    features_used=['response_time', 'status_code', 'payload_size', 'url_features'],
                    model_version="1.0",
                    explanation=f"Reconstruction error {error:.3f} exceeds threshold {self.threshold:.3f}"
                ))

        return anomalies

class SecurityAnalysisModel:
    """ML model for API security analysis"""

    def __init__(self):
        self.security_classifier = None
        self.feature_extractor = None
        self.is_trained = False

    async def train_security_model(self, security_data: List[Dict[str, Any]]):
        """Train security analysis model"""
        if not HAS_SKLEARN:
            logging.warning("Scikit-learn not available for security analysis")
            return

        logging.info("🧠 Training API security analysis model")

        # Prepare features and labels
        features, labels = self._prepare_security_data(security_data)

        if len(features) < 20:
            logging.warning("Insufficient data for security model training")
            return

        # Train gradient boosting classifier
        self.security_classifier = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )

        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=0.2, random_state=42
        )

        self.security_classifier.fit(X_train, y_train)

        # Evaluate
        y_pred = self.security_classifier.predict(X_test)
        score = self.security_classifier.score(X_test, y_test)

        logging.info(f"✅ Security analysis model trained with R² score: {score:.3f}")
        self.is_trained = True

    def _prepare_security_data(self, security_data: List[Dict[str, Any]]) -> Tuple[List, List]:
        """Prepare security training data"""
        features = []
        labels = []

        for item in security_data:
            feature_vector = self._extract_security_features(item)
            security_score = item.get('security_score', 0.5)

            features.append(feature_vector)
            labels.append(security_score)

        return features, labels

    def _extract_security_features(self, api_data: Dict[str, Any]) -> List[float]:
        """Extract security-relevant features"""
        url = api_data.get('url', '')
        headers = api_data.get('headers', {})

        features = [
            1 if url.startswith('https') else 0,  # HTTPS usage
            1 if 'authorization' in str(headers).lower() else 0,  # Auth header
            1 if 'x-api-key' in str(headers).lower() else 0,  # API key
            1 if 'cors' in str(headers).lower() else 0,  # CORS headers
            len(re.findall(r'\{.*?\}', url)),  # Path parameters
            1 if api_data.get('rate_limited', False) else 0,  # Rate limiting
            api_data.get('auth_failures', 0),  # Authentication failures
            1 if api_data.get('sensitive_data', False) else 0,  # Sensitive data
            len(api_data.get('exposed_endpoints', [])),  # Exposed endpoints
            api_data.get('vulnerability_count', 0)  # Known vulnerabilities
        ]

        return features

    async def analyze_security(self, api_data: Dict[str, Any]) -> ModelPrediction:
        """Analyze API security"""
        if not self.is_trained or not self.security_classifier:
            return ModelPrediction(
                model_type=ModelType.SECURITY_ANALYSIS,
                prediction=0.5,
                confidence=0.0,
                features_used=[],
                model_version="1.0",
                explanation="Model not trained"
            )

        # Extract features
        features = self._extract_security_features(api_data)

        # Predict security score
        security_score = self.security_classifier.predict([features])[0]

        # Generate security recommendations
        recommendations = self._generate_security_recommendations(features, api_data)

        return ModelPrediction(
            model_type=ModelType.SECURITY_ANALYSIS,
            prediction={
                "security_score": float(security_score),
                "risk_level": "high" if security_score < 0.3 else "medium" if security_score < 0.7 else "low",
                "recommendations": recommendations
            },
            confidence=0.85,
            features_used=['https_usage', 'auth_headers', 'rate_limiting', 'vulnerabilities'],
            model_version="1.0"
        )

    def _generate_security_recommendations(self, features: List[float], api_data: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on analysis"""
        recommendations = []

        if features[0] == 0:  # No HTTPS
            recommendations.append("Enable HTTPS encryption for all API endpoints")

        if features[1] == 0:  # No auth header
            recommendations.append("Implement proper authentication mechanisms")

        if features[5] == 0:  # No rate limiting
            recommendations.append("Implement rate limiting to prevent abuse")

        if features[9] > 0:  # Has vulnerabilities
            recommendations.append("Address identified security vulnerabilities")

        if not recommendations:
            recommendations.append("Security configuration appears adequate")

        return recommendations

class AdvancedAPIDiscoveryEngine:
    """Main engine combining all ML models for API discovery"""

    def __init__(self):
        self.pattern_model = APIPatternRecognitionModel()
        self.behavior_model = BehaviorPredictionModel()
        self.anomaly_model = AnomalyDetectionModel()
        self.security_model = SecurityAnalysisModel()

        self.training_data = {
            'patterns': [],
            'behaviors': [],
            'security': [],
            'anomalies': []
        }

        self.models_trained = False

    async def initialize_models(self):
        """Initialize all ML models"""
        logging.info("🚀 Initializing advanced ML models for API discovery")

        # Load any existing training data
        await self._load_training_data()

        # Train models if we have sufficient data
        if len(self.training_data['patterns']) >= 10:
            await self.pattern_model.train_model(self.training_data['patterns'])

        if len(self.training_data['behaviors']) >= 50:
            await self.behavior_model.train_behavior_model(self.training_data['behaviors'])

        if len(self.training_data['anomalies']) >= 100:
            await self.anomaly_model.train_anomaly_detector(self.training_data['anomalies'])

        if len(self.training_data['security']) >= 20:
            await self.security_model.train_security_model(self.training_data['security'])

        self.models_trained = True
        logging.info("✅ Advanced ML models initialized")

    async def _load_training_data(self):
        """Load training data from storage"""
        # In production, this would load from a database
        # For now, we'll use mock data

        self.training_data = {
            'patterns': [
                {'url': '/api/v1/users', 'method': 'GET', 'category': 'rest_api'},
                {'url': '/api/v1/products', 'method': 'POST', 'category': 'rest_api'},
                {'url': '/graphql', 'method': 'POST', 'category': 'graphql'},
                {'url': '/ws/chat', 'method': 'GET', 'category': 'websocket'},
            ],
            'behaviors': [],  # Would be populated with real traffic data
            'security': [
                {'url': 'https://api.example.com/users', 'security_score': 0.8},
                {'url': 'http://api.example.com/admin', 'security_score': 0.3},
            ],
            'anomalies': []  # Would be populated with normal traffic patterns
        }

    async def comprehensive_analysis(self, api_data: Dict[str, Any]) -> Dict[str, ModelPrediction]:
        """Run comprehensive ML analysis on API data"""
        results = {}

        # Pattern recognition
        pattern_result = await self.pattern_model.predict_api_pattern(api_data)
        results['pattern_recognition'] = pattern_result

        # Security analysis
        security_result = await self.security_model.analyze_security(api_data)
        results['security_analysis'] = security_result

        # Behavior prediction (if historical data available)
        if 'historical_data' in api_data:
            behavior_result = await self.behavior_model.predict_behavior(api_data['historical_data'])
            results['behavior_prediction'] = behavior_result

        return results

    async def detect_api_anomalies(self, traffic_data: List[Dict[str, Any]]) -> List[ModelPrediction]:
        """Detect anomalies in API traffic using ML"""
        return await self.anomaly_model.detect_anomalies(traffic_data)

    async def update_training_data(self, data_type: str, new_data: List[Dict[str, Any]]):
        """Update training data and retrain models if necessary"""
        if data_type in self.training_data:
            self.training_data[data_type].extend(new_data)

            # Retrain specific model if enough new data
            if data_type == 'patterns' and len(new_data) >= 5:
                await self.pattern_model.train_model(self.training_data['patterns'])
            elif data_type == 'security' and len(new_data) >= 10:
                await self.security_model.train_security_model(self.training_data['security'])

    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all ML models"""
        return {
            "models_initialized": self.models_trained,
            "pattern_model_trained": self.pattern_model.is_trained,
            "behavior_model_trained": self.behavior_model.is_trained,
            "anomaly_model_trained": self.anomaly_model.is_trained,
            "security_model_trained": self.security_model.is_trained,
            "training_data_counts": {
                "patterns": len(self.training_data['patterns']),
                "behaviors": len(self.training_data['behaviors']),
                "security": len(self.training_data['security']),
                "anomalies": len(self.training_data['anomalies'])
            },
            "available_libraries": {
                "pytorch": HAS_PYTORCH,
                "tensorflow": HAS_TENSORFLOW,
                "sklearn": HAS_SKLEARN
            }
        }

# Global instance
advanced_discovery_engine = AdvancedAPIDiscoveryEngine()

# Convenience functions
async def initialize_advanced_models():
    """Initialize the advanced ML models"""
    await advanced_discovery_engine.initialize_models()

async def analyze_api_with_ml(api_data: Dict[str, Any]) -> Dict[str, ModelPrediction]:
    """Analyze API using all available ML models"""
    return await advanced_discovery_engine.comprehensive_analysis(api_data)

async def detect_traffic_anomalies(traffic_data: List[Dict[str, Any]]) -> List[ModelPrediction]:
    """Detect anomalies in API traffic"""
    return await advanced_discovery_engine.detect_api_anomalies(traffic_data)