#!/usr/bin/env python3
"""
RAG Knowledge System - Production Implementation
Provides intelligent industry-specific security knowledge
"""

import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import OpenAI for embeddings
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class RAGKnowledgeSystem:
    """Production RAG system for security intelligence"""

    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        self.openai_client = None

        # Initialize OpenAI client if available
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                print("✅ OpenAI client initialized for RAG embeddings")

    def _load_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load security knowledge base"""
        return [
            {
                "title": "Healthcare Security Compliance",
                "content": "HIPAA requires PHI protection with administrative, physical, and technical safeguards. Key requirements include access controls, audit logs, encryption, and minimum necessary access principle.",
                "domain": "healthcare",
                "frameworks": ["HIPAA", "HITECH", "FDA"]
            },
            {
                "title": "Financial Services Security",
                "content": "PCI-DSS mandates payment card data protection. SOX requires financial reporting controls. Key controls include encryption, access restrictions, audit trails, and incident response.",
                "domain": "financial",
                "frameworks": ["PCI-DSS", "SOX", "AML", "KYC"]
            },
            {
                "title": "API Security Best Practices",
                "content": "OWASP API Security Top 10 covers broken authentication, excessive data exposure, lack of rate limiting, and injection attacks. Implement proper authentication, authorization, and input validation.",
                "domain": "general",
                "frameworks": ["OWASP", "NIST"]
            },
            {
                "title": "Zero-Trust Architecture",
                "content": "Never trust, always verify. Implement continuous verification, least privilege access, and assume breach. Key components include identity verification, device security, and micro-segmentation.",
                "domain": "security",
                "frameworks": ["NIST", "CISA"]
            },
            {
                "title": "Cryptocurrency Security",
                "content": "Digital asset security requires multi-signature wallets, cold storage, and regulatory compliance. Key risks include private key management, smart contract vulnerabilities, and regulatory changes.",
                "domain": "cryptocurrency",
                "frameworks": ["AML", "KYC", "FATF"]
            },
            {
                "title": "GDPR Data Protection",
                "content": "General Data Protection Regulation requires explicit consent, data minimization, purpose limitation, and individual rights (access, rectification, erasure). Technical measures include encryption, pseudonymization, and privacy by design.",
                "domain": "privacy",
                "frameworks": ["GDPR", "ePrivacy", "CCPA"]
            },
            {
                "title": "SOC2 Security Controls",
                "content": "SOC2 Type II focuses on security, availability, processing integrity, confidentiality, and privacy. Key controls include access management, change management, monitoring, and incident response procedures.",
                "domain": "security",
                "frameworks": ["SOC2", "ISO27001", "NIST"]
            },
            {
                "title": "Cloud Security Architecture",
                "content": "Cloud security requires shared responsibility model understanding, identity federation, network segmentation, data encryption in transit and at rest, and continuous monitoring of cloud resources.",
                "domain": "cloud",
                "frameworks": ["CSA", "NIST", "ISO27017"]
            },
            {
                "title": "DevSecOps Integration",
                "content": "DevSecOps integrates security throughout development lifecycle with automated security testing, container security, infrastructure as code scanning, and continuous compliance monitoring.",
                "domain": "devsecops",
                "frameworks": ["NIST", "OWASP", "CIS"]
            }
        ]

    async def get_industry_intelligence(self, business_context: str, endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get industry-specific intelligence"""

        # Determine industry from context
        industry = self._classify_industry(business_context, endpoint_data)

        # Find relevant knowledge
        relevant_docs = self._retrieve_relevant_documents(business_context, industry)

        # Generate industry intelligence
        intelligence = {
            "industry": industry,
            "knowledge_source": "RAG",
            "documents_retrieved": len(relevant_docs),
            "key_regulations": self._extract_regulations(relevant_docs),
            "specific_risks": [],
            "recommendations": [],
            "specific_vulnerabilities": [],
            "mitigation_strategies": [],
            "risk_score": self._calculate_risk_score(business_context, endpoint_data),
            "compliance_gaps": self._identify_compliance_gaps(business_context, endpoint_data, relevant_docs),
            "confidence_score": self._calculate_confidence(relevant_docs),
            "retrieval_timestamp": datetime.now().isoformat()
        }

        return intelligence

    def _classify_industry(self, business_context: str, endpoint_data: Dict[str, Any]) -> str:
        """Classify the industry based on context"""
        context_lower = business_context.lower()
        path_lower = endpoint_data.get('path', '').lower()

        if any(term in context_lower + path_lower for term in ['healthcare', 'medical', 'patient', 'hipaa']):
            return "Healthcare"
        elif any(term in context_lower + path_lower for term in ['financial', 'payment', 'banking', 'fintech']):
            return "Financial Services"
        elif any(term in context_lower + path_lower for term in ['crypto', 'blockchain', 'bitcoin']):
            return "Cryptocurrency"
        elif any(term in context_lower + path_lower for term in ['gdpr', 'privacy', 'personal data', 'consent']):
            return "Privacy"
        elif any(term in context_lower + path_lower for term in ['cloud', 'aws', 'azure', 'gcp', 'kubernetes']):
            return "Cloud"
        elif any(term in context_lower + path_lower for term in ['devops', 'ci/cd', 'pipeline', 'deployment']):
            return "DevSecOps"
        else:
            return "General"

    def _retrieve_relevant_documents(self, business_context: str, industry: str) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from knowledge base"""
        relevant_docs = []

        for doc in self.knowledge_base:
            # Match by domain
            if doc['domain'] == industry.lower() or doc['domain'] == 'general':
                relevant_docs.append(doc)

            # Match by content similarity (simple keyword matching)
            if any(keyword in business_context.lower() for keyword in doc['content'].lower().split()):
                if doc not in relevant_docs:
                    relevant_docs.append(doc)

        return relevant_docs

    def _extract_regulations(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Extract relevant regulations from documents"""
        regulations = set()

        for doc in documents:
            regulations.update(doc.get('frameworks', []))

        return list(regulations)

    def _identify_compliance_gaps(self, business_context: str, endpoint_data: Dict[str, Any], documents: List[Dict[str, Any]]) -> List[str]:
        """Identify compliance gaps"""
        gaps = []

        # Check for missing authentication
        if not endpoint_data.get('security'):
            gaps.append("Missing authentication mechanism")

        # Check for sensitive data exposure
        path = endpoint_data.get('path', '').lower()
        if any(term in path for term in ['patient', 'payment', 'personal']):
            gaps.append("Sensitive endpoint without proper protection")

        # Industry-specific gaps
        if 'healthcare' in business_context.lower():
            gaps.append("HIPAA compliance validation needed")

        if 'financial' in business_context.lower():
            gaps.append("PCI-DSS compliance validation needed")

        return gaps

    def _calculate_risk_score(self, business_context: str, endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk score"""
        base_score = 5  # Medium risk baseline

        # Increase risk for sensitive industries
        if any(term in business_context.lower() for term in ['healthcare', 'financial', 'payment']):
            base_score += 2

        # Increase risk for missing security
        if not endpoint_data.get('security'):
            base_score += 3

        # Increase risk for sensitive endpoints
        path = endpoint_data.get('path', '').lower()
        if any(term in path for term in ['admin', 'user', 'payment', 'personal']):
            base_score += 1

        return {
            "overall": min(10, base_score),
            "confidentiality": min(10, base_score + 1),
            "integrity": min(10, base_score),
            "availability": min(10, base_score - 1)
        }

    def _calculate_confidence(self, documents: List[Dict[str, Any]]) -> float:
        """Calculate confidence in the analysis"""
        if not documents:
            return 0.0

        # Higher confidence with more relevant documents
        confidence = min(1.0, len(documents) * 0.3)

        return confidence