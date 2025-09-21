#!/usr/bin/env python3
"""
RAG Knowledge System - Production Implementation
Provides intelligent industry-specific security knowledge
"""

import asyncio
import json
import os
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from pathlib import Path

# Import OpenAI for embeddings
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️ FAISS not available, using basic numpy similarity")

class EnhancedRAGKnowledgeSystem:
    """Enhanced RAG system with vector embeddings and semantic search"""

    def __init__(self, knowledge_base_path: str = "knowledge_base"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_base_path.mkdir(exist_ok=True)

        # Load static knowledge base
        self.knowledge_base = self._load_knowledge_base()

        # Initialize vector components with performance optimizations
        self.embeddings_cache = {}
        self.document_embeddings = {}
        self.conversation_memory = {}
        self.vector_store = None

        # Performance optimization parameters
        self.embedding_batch_size = 32  # Batch processing for efficiency
        self.cache_max_size = 10000  # LRU cache limit
        self.embedding_queue = []  # Queue for batch processing
        self.similarity_threshold = 0.3  # Configurable threshold
        self.use_approximate_search = True  # Use FAISS approximate search when available
        self.embedding_dim = 1536  # OpenAI text-embedding-3-small dimension

        # Initialize OpenAI client with fallback support
        self.openai_client = None
        self.use_mock_embeddings = False

        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                print("✅ OpenAI client initialized for RAG embeddings")
            else:
                print("⚠️ OpenAI API key not found, using mock embeddings for testing")
                self.use_mock_embeddings = True
        else:
            print("⚠️ OpenAI not available, using mock embeddings for testing")
            self.use_mock_embeddings = True

        # Initialize optimized FAISS index
        if FAISS_AVAILABLE:
            self.embedding_dim = 1536  # OpenAI text-embedding-3-small dimension
            if self.use_approximate_search:
                # Use IndexIVFFlat for faster approximate search with large datasets
                quantizer = faiss.IndexFlatIP(self.embedding_dim)
                self.vector_store = faiss.IndexIVFFlat(quantizer, self.embedding_dim, 100, faiss.METRIC_INNER_PRODUCT)
                # Add dummy training data to enable search
                training_data = np.random.random((1000, self.embedding_dim)).astype('float32')
                self.vector_store.train(training_data)
                print("✅ FAISS approximate vector store initialized with IVF indexing")
            else:
                self.vector_store = faiss.IndexFlatIP(self.embedding_dim)
                print("✅ FAISS exact vector store initialized")

            # Set search parameters for better performance
            self.vector_store.nprobe = 10  # Number of clusters to search

        # Load existing embeddings
        self._load_embeddings_cache()

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

    async def get_industry_intelligence(self, business_context: str, endpoint_data: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
        """Get industry-specific intelligence with conversation context"""

        # Add conversation context if available
        enhanced_context = self._enhance_with_conversation_context(business_context, user_id)

        # Determine industry from context
        industry = self._classify_industry(enhanced_context, endpoint_data)

        # Find relevant knowledge using enhanced retrieval
        relevant_docs = await self._retrieve_relevant_documents(enhanced_context, industry)

        # Store conversation context
        if user_id:
            self._update_conversation_memory(user_id, business_context, industry, relevant_docs)

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

    async def _retrieve_relevant_documents(self, business_context: str, industry: str) -> List[Dict[str, Any]]:
        """Enhanced document retrieval with semantic search"""

        # First try semantic search if available
        if self.openai_client:
            semantic_docs = await self._semantic_retrieval(business_context)
            if semantic_docs:
                return semantic_docs

        # Fallback to keyword matching
        return self._keyword_retrieval(business_context, industry)

    async def _semantic_retrieval(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Optimized semantic document retrieval using batch processing"""
        try:
            # Get query embedding
            query_embedding = await self._get_embedding(query)
            if query_embedding is None:
                return []

            # Get all document embeddings (batch processing)
            doc_embeddings = []
            valid_docs = []

            for doc in self.knowledge_base:
                doc_embedding = await self._get_document_embedding(doc)
                if doc_embedding is not None:
                    doc_embeddings.append(doc_embedding)
                    valid_docs.append(doc)

            if not doc_embeddings:
                return []

            # Use batch similarity calculation for better performance
            similarities = self._calculate_similarities_batch(query_embedding, doc_embeddings)

            # Create list of (doc, similarity) pairs
            doc_similarities = list(zip(valid_docs, similarities))

            # Sort by similarity and return top_k results above threshold
            doc_similarities.sort(key=lambda x: x[1], reverse=True)
            results = [doc for doc, similarity in doc_similarities[:top_k] if similarity > self.similarity_threshold]

            print(f"✅ Semantic retrieval found {len(results)} relevant documents (threshold: {self.similarity_threshold})")
            return results

        except Exception as e:
            print(f"⚠️ Semantic retrieval failed: {e}")
            return []

    def _keyword_retrieval(self, business_context: str, industry: str) -> List[Dict[str, Any]]:
        """Fallback keyword-based retrieval"""
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

    async def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding for text using OpenAI API with caching and batching"""
        if self.use_mock_embeddings:
            return self._generate_mock_embedding(text)

        if not self.openai_client:
            return None

        # Check cache first
        text_hash = hash(text)
        if text_hash in self.embeddings_cache:
            return self.embeddings_cache[text_hash]

        # Add to batch queue if batch processing is enabled
        if len(self.embedding_queue) < self.embedding_batch_size:
            self.embedding_queue.append((text, text_hash))

            # Process batch when queue is full
            if len(self.embedding_queue) >= self.embedding_batch_size:
                await self._process_embedding_batch()

            # Return cached result if available
            if text_hash in self.embeddings_cache:
                return self.embeddings_cache[text_hash]

        try:
            response = await asyncio.to_thread(
                self.openai_client.embeddings.create,
                model="text-embedding-3-small",
                input=text
            )
            embedding = np.array(response.data[0].embedding)

            # Cache the embedding with LRU management
            self._cache_embedding(text_hash, embedding)

            return embedding
        except Exception as e:
            print(f"⚠️ Failed to get embedding: {e}")
            return None

    async def _process_embedding_batch(self):
        """Process embeddings in batch for better performance"""
        if not self.embedding_queue:
            return

        try:
            texts = [item[0] for item in self.embedding_queue]
            text_hashes = [item[1] for item in self.embedding_queue]

            response = await asyncio.to_thread(
                self.openai_client.embeddings.create,
                model="text-embedding-3-small",
                input=texts
            )

            # Cache all embeddings from batch
            for i, embedding_data in enumerate(response.data):
                embedding = np.array(embedding_data.embedding)
                self._cache_embedding(text_hashes[i], embedding)

            print(f"✅ Processed batch of {len(texts)} embeddings")

        except Exception as e:
            print(f"⚠️ Batch embedding processing failed: {e}")

        # Clear queue
        self.embedding_queue.clear()

    def _cache_embedding(self, text_hash: int, embedding: np.ndarray):
        """Cache embedding with LRU management"""
        # Simple LRU: remove oldest if cache is full
        if len(self.embeddings_cache) >= self.cache_max_size:
            # Remove 10% of oldest entries
            items_to_remove = int(self.cache_max_size * 0.1)
            oldest_keys = list(self.embeddings_cache.keys())[:items_to_remove]
            for key in oldest_keys:
                del self.embeddings_cache[key]

        self.embeddings_cache[text_hash] = embedding

    def _generate_mock_embedding(self, text: str) -> np.ndarray:
        """Generate deterministic mock embedding for testing when OpenAI is not available"""
        # Create a deterministic hash-based embedding
        import hashlib

        # Use text hash to generate consistent embeddings
        text_hash = hashlib.md5(text.encode()).hexdigest()

        # Convert hex to numbers and normalize
        numbers = [int(text_hash[i:i+2], 16) for i in range(0, len(text_hash), 2)]

        # Pad or truncate to get the right dimension
        while len(numbers) < self.embedding_dim:
            numbers.extend(numbers[:min(len(numbers), self.embedding_dim - len(numbers))])
        numbers = numbers[:self.embedding_dim]

        # Normalize to unit vector
        embedding = np.array(numbers, dtype=np.float32)
        embedding = embedding / np.linalg.norm(embedding)

        # Cache it
        text_hash_int = hash(text)
        self._cache_embedding(text_hash_int, embedding)

        return embedding

    async def _get_document_embedding(self, doc: Dict[str, Any]) -> Optional[np.ndarray]:
        """Get embedding for a document"""
        doc_id = doc.get('title', '')

        # Check if already computed
        if doc_id in self.document_embeddings:
            return self.document_embeddings[doc_id]

        # Combine title and content for embedding
        text = f"{doc.get('title', '')} {doc.get('content', '')}"
        embedding = await self._get_embedding(text)

        if embedding is not None:
            self.document_embeddings[doc_id] = embedding

        return embedding

    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            # Normalize embeddings for cosine similarity
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            # Calculate cosine similarity
            similarity = float(np.dot(embedding1, embedding2) / (norm1 * norm2))

            # Convert from [-1, 1] to [0, 1] range for consistency
            similarity = (similarity + 1.0) / 2.0

            return max(0.0, min(1.0, similarity))
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0

    def _calculate_similarities_batch(self, query_embedding: np.ndarray, doc_embeddings: List[np.ndarray]) -> List[float]:
        """Calculate similarities in batch for better performance"""
        try:
            if not doc_embeddings:
                return []

            # Stack embeddings into matrix for vectorized computation
            doc_matrix = np.stack(doc_embeddings)

            # Normalize embeddings
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            doc_norms = doc_matrix / np.linalg.norm(doc_matrix, axis=1, keepdims=True)

            # Compute all similarities at once
            similarities = np.dot(doc_norms, query_norm)

            # Clamp values and convert to list
            return np.clip(similarities, 0.0, 1.0).tolist()
        except Exception as e:
            print(f"⚠️ Batch similarity calculation failed: {e}")
            return [0.0] * len(doc_embeddings)

    async def _precompute_embeddings(self):
        """Pre-compute embeddings for all documents in knowledge base"""
        if not self.openai_client and not self.use_mock_embeddings:
            return

        print("🔄 Pre-computing document embeddings...")
        for doc in self.knowledge_base:
            await self._get_document_embedding(doc)

        # Save embeddings to disk
        self._save_embeddings_cache()
        print("✅ Document embeddings computed and cached")

    def _load_embeddings_cache(self):
        """Load embeddings cache from disk"""
        embeddings_file = self.knowledge_base_path / "embeddings_cache.pkl"
        document_embeddings_file = self.knowledge_base_path / "document_embeddings.pkl"

        if embeddings_file.exists():
            try:
                with open(embeddings_file, 'rb') as f:
                    self.embeddings_cache = pickle.load(f)
                print(f"📚 Loaded {len(self.embeddings_cache)} cached embeddings")
            except Exception as e:
                print(f"⚠️ Failed to load embeddings cache: {e}")
                self.embeddings_cache = {}

        if document_embeddings_file.exists():
            try:
                with open(document_embeddings_file, 'rb') as f:
                    self.document_embeddings = pickle.load(f)
                print(f"📄 Loaded {len(self.document_embeddings)} document embeddings")
            except Exception as e:
                print(f"⚠️ Failed to load document embeddings: {e}")
                self.document_embeddings = {}

    def _save_embeddings_cache(self):
        """Save embeddings cache to disk"""
        try:
            with open(self.knowledge_base_path / "embeddings_cache.pkl", 'wb') as f:
                pickle.dump(self.embeddings_cache, f)

            with open(self.knowledge_base_path / "document_embeddings.pkl", 'wb') as f:
                pickle.dump(self.document_embeddings, f)
        except Exception as e:
            print(f"⚠️ Failed to save embeddings cache: {e}")

    def _enhance_with_conversation_context(self, business_context: str, user_id: str) -> str:
        """Enhance query with conversation context"""
        if not user_id or user_id not in self.conversation_memory:
            return business_context

        memory = self.conversation_memory[user_id]
        recent_context = memory.get('recent_topics', [])[-3:]  # Last 3 topics

        if recent_context:
            context_str = " ".join(recent_context)
            return f"Previous context: {context_str}\n\nCurrent query: {business_context}"

        return business_context

    def _update_conversation_memory(self, user_id: str, query: str, industry: str, documents: List[Dict]):
        """Update conversation memory for a user"""
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = {
                'recent_topics': [],
                'industries': [],
                'timestamp': datetime.now()
            }

        memory = self.conversation_memory[user_id]
        memory['recent_topics'].append(f"{industry}: {query[:100]}")
        memory['industries'].append(industry)
        memory['timestamp'] = datetime.now()

        # Keep only last 10 topics
        if len(memory['recent_topics']) > 10:
            memory['recent_topics'] = memory['recent_topics'][-10:]

        if len(memory['industries']) > 10:
            memory['industries'] = memory['industries'][-10:]

    async def ingest_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingest new documents into the knowledge base"""
        ingested = 0
        errors = []

        for doc in documents:
            try:
                # Validate document structure
                if not all(key in doc for key in ['title', 'content', 'domain']):
                    errors.append(f"Invalid document structure: {doc.get('title', 'Unknown')}")
                    continue

                # Add to knowledge base
                self.knowledge_base.append(doc)

                # Pre-compute embedding
                await self._get_document_embedding(doc)

                ingested += 1

            except Exception as e:
                errors.append(f"Failed to ingest {doc.get('title', 'Unknown')}: {str(e)}")

        # Save updated knowledge base and embeddings
        self._save_knowledge_base()
        self._save_embeddings_cache()

        return {
            "ingested": ingested,
            "errors": errors,
            "total_documents": len(self.knowledge_base)
        }

    def _save_knowledge_base(self):
        """Save knowledge base to disk"""
        try:
            with open(self.knowledge_base_path / "knowledge_base.json", 'w') as f:
                json.dump(self.knowledge_base, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Failed to save knowledge base: {e}")

    async def get_conversation_insights(self, user_id: str) -> Dict[str, Any]:
        """Get insights from user's conversation history"""
        if user_id not in self.conversation_memory:
            return {"insights": "No conversation history found"}

        memory = self.conversation_memory[user_id]

        # Analyze conversation patterns
        industries = memory.get('industries', [])
        industry_counts = {}
        for industry in industries:
            industry_counts[industry] = industry_counts.get(industry, 0) + 1

        primary_industry = max(industry_counts.keys(), key=industry_counts.get) if industry_counts else "Unknown"

        return {
            "primary_industry": primary_industry,
            "industry_distribution": industry_counts,
            "total_queries": len(memory.get('recent_topics', [])),
            "last_activity": memory.get('timestamp'),
            "insights": f"User primarily works with {primary_industry} systems"
        }

    def update_conversation_memory(self, user_id: str, message: str, context: Dict[str, Any] = None):
        """Public method to update conversation memory"""
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = {
                'messages': [],
                'recent_topics': [],
                'industries': [],
                'timestamp': datetime.now(),
                'context_data': {}
            }

        memory = self.conversation_memory[user_id]
        memory['messages'].append({
            'content': message,
            'timestamp': datetime.now(),
            'context': context or {}
        })

        # Keep only last 50 messages for memory efficiency
        if len(memory['messages']) > 50:
            memory['messages'] = memory['messages'][-50:]

        # Update recent topics from message content
        words = message.lower().split()
        topics = [word for word in words if len(word) > 4]
        memory['recent_topics'].extend(topics[:5])  # Add up to 5 topics
        memory['recent_topics'] = memory['recent_topics'][-20:]  # Keep last 20 topics

        memory['timestamp'] = datetime.now()
        if context:
            memory['context_data'].update(context)

    def get_conversation_memory(self, user_id: str) -> List[Dict[str, Any]]:
        """Public method to get conversation memory"""
        if user_id not in self.conversation_memory:
            return []

        return self.conversation_memory[user_id].get('messages', [])

    def clear_conversation_memory(self, user_id: str) -> bool:
        """Clear conversation memory for a user"""
        if user_id in self.conversation_memory:
            del self.conversation_memory[user_id]
            return True
        return False

    def get_conversation_context(self, user_id: str) -> Dict[str, Any]:
        """Get conversation context and metadata for a user"""
        if user_id not in self.conversation_memory:
            return {}

        memory = self.conversation_memory[user_id]
        return {
            'total_messages': len(memory.get('messages', [])),
            'recent_topics': memory.get('recent_topics', [])[-10:],  # Last 10 topics
            'last_activity': memory.get('timestamp'),
            'context_data': memory.get('context_data', {}),
            'summary': f"User has {len(memory.get('messages', []))} messages with focus on {', '.join(memory.get('recent_topics', [])[-3:])}"
        }

    def _get_embedding_sync(self, text: str) -> Optional[np.ndarray]:
        """Synchronous version of _get_embedding for testing"""
        if self.use_mock_embeddings:
            return self._generate_mock_embedding(text)

        if not self.openai_client:
            return None

        # For sync operation, just use mock embeddings
        return self._generate_mock_embedding(text)

    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None):
        """Add a document to the knowledge base for testing"""
        document = {
            'id': doc_id,
            'title': doc_id,
            'content': content,
            'keywords': [],
            'industry': 'general',
            'metadata': metadata or {}
        }

        # Add to knowledge base
        self.knowledge_base.append(document)

        # Generate and cache embedding
        embedding = self._get_embedding_sync(content)
        if embedding is not None:
            self.embeddings_cache[hash(content)] = embedding

    def get_similar_documents(self, query: str, top_k: int = 5) -> List[tuple]:
        """Get similar documents for testing purposes"""
        try:
            # Get query embedding
            query_embedding = self._get_embedding_sync(query)
            if query_embedding is None:
                return []

            # Calculate similarities for all documents
            similarities = []
            for doc in self.knowledge_base:
                doc_id = doc.get('id', doc.get('title', 'unknown'))
                content = doc['content']
                content_hash = hash(content)

                # Get or generate document embedding
                if content_hash in self.embeddings_cache:
                    doc_embedding = self.embeddings_cache[content_hash]
                else:
                    doc_embedding = self._get_embedding_sync(content)
                    if doc_embedding is not None:
                        self.embeddings_cache[content_hash] = doc_embedding

                if doc_embedding is not None:
                    similarity = self._calculate_similarity(query_embedding, doc_embedding)
                    similarities.append((doc_id, doc['content'], similarity))

            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x[2], reverse=True)
            return similarities[:top_k]

        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []


# Backward compatibility
class RAGKnowledgeSystem(EnhancedRAGKnowledgeSystem):
    """Backward compatibility wrapper"""
    def __init__(self):
        super().__init__()