#!/usr/bin/env python3
"""
Vector Embeddings Performance Test
Tests the optimized RAG knowledge system performance with real data
"""

import asyncio
import time
import json
import statistics
from typing import List, Dict
from backend.src.rag_knowledge_system import EnhancedRAGKnowledgeSystem

class VectorPerformanceTester:
    def __init__(self):
        self.rag_system = EnhancedRAGKnowledgeSystem()
        self.test_queries = [
            "healthcare security compliance requirements",
            "financial services payment card security",
            "API security authentication and authorization",
            "zero trust architecture implementation",
            "cryptocurrency wallet security best practices",
            "cloud infrastructure security monitoring",
            "DevSecOps pipeline security automation",
            "GDPR privacy data protection compliance",
            "blockchain smart contract vulnerabilities",
            "incident response security procedures"
        ]

    async def test_single_query_performance(self, query: str) -> Dict:
        """Test performance of a single query"""
        start_time = time.time()

        try:
            # Test semantic retrieval
            results = await self.rag_system._semantic_retrieval(query, top_k=5)
            processing_time = time.time() - start_time

            return {
                "query": query,
                "results_count": len(results),
                "processing_time": processing_time,
                "success": True,
                "cache_size": len(self.rag_system.embeddings_cache),
                "doc_embeddings_count": len(self.rag_system.document_embeddings)
            }
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "query": query,
                "results_count": 0,
                "processing_time": processing_time,
                "success": False,
                "error": str(e)
            }

    async def test_batch_performance(self, concurrent_queries: int = 5) -> Dict:
        """Test performance with concurrent queries"""
        start_time = time.time()

        # Run concurrent queries
        tasks = []
        for i in range(concurrent_queries):
            query = self.test_queries[i % len(self.test_queries)]
            tasks.append(self.test_single_query_performance(query))

        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Calculate metrics
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]

        if successful_results:
            processing_times = [r["processing_time"] for r in successful_results]
            avg_processing_time = statistics.mean(processing_times)
            median_processing_time = statistics.median(processing_times)
            min_processing_time = min(processing_times)
            max_processing_time = max(processing_times)
            queries_per_second = len(successful_results) / total_time
        else:
            avg_processing_time = median_processing_time = min_processing_time = max_processing_time = 0
            queries_per_second = 0

        return {
            "total_queries": concurrent_queries,
            "successful_queries": len(successful_results),
            "failed_queries": len(failed_results),
            "success_rate": len(successful_results) / concurrent_queries * 100,
            "total_time": total_time,
            "queries_per_second": queries_per_second,
            "avg_processing_time": avg_processing_time,
            "median_processing_time": median_processing_time,
            "min_processing_time": min_processing_time,
            "max_processing_time": max_processing_time,
            "cache_efficiency": len(self.rag_system.embeddings_cache),
            "results": results
        }

    async def test_cache_performance(self) -> Dict:
        """Test embedding cache performance"""
        print("🧪 Testing cache performance...")

        # First run - cache miss
        cache_miss_times = []
        for query in self.test_queries[:3]:
            start_time = time.time()
            await self.rag_system._get_embedding(query)
            cache_miss_times.append(time.time() - start_time)

        # Second run - cache hit
        cache_hit_times = []
        for query in self.test_queries[:3]:
            start_time = time.time()
            await self.rag_system._get_embedding(query)
            cache_hit_times.append(time.time() - start_time)

        cache_hit_avg = statistics.mean(cache_hit_times)
        cache_miss_avg = statistics.mean(cache_miss_times)

        return {
            "cache_miss_avg": cache_miss_avg,
            "cache_hit_avg": cache_hit_avg,
            "cache_speedup": cache_miss_avg / cache_hit_avg if cache_hit_avg > 0 else float('inf'),
            "cache_size": len(self.rag_system.embeddings_cache)
        }

    async def run_comprehensive_performance_test(self) -> Dict:
        """Run comprehensive performance test suite"""
        print("🚀 VECTOR EMBEDDINGS PERFORMANCE TEST")
        print("=" * 60)

        results = {}

        # Test 1: Single query performance
        print("\n1. Testing single query performance...")
        single_query_result = await self.test_single_query_performance(self.test_queries[0])
        results["single_query"] = single_query_result
        print(f"   ✅ Single query: {single_query_result['processing_time']:.3f}s")

        # Test 2: Batch performance with different concurrency levels
        print("\n2. Testing batch performance...")
        batch_results = {}
        for concurrency in [1, 5, 10, 20]:
            print(f"   Testing {concurrency} concurrent queries...")
            batch_result = await self.test_batch_performance(concurrency)
            batch_results[f"concurrency_{concurrency}"] = batch_result
            print(f"   ✅ {concurrency} queries: {batch_result['queries_per_second']:.1f} q/s")

        results["batch_performance"] = batch_results

        # Test 3: Cache performance
        print("\n3. Testing cache performance...")
        cache_result = await self.test_cache_performance()
        results["cache_performance"] = cache_result
        print(f"   ✅ Cache speedup: {cache_result['cache_speedup']:.1f}x")

        # Test 4: Memory usage
        print("\n4. Checking memory usage...")
        memory_info = {
            "embeddings_cache_size": len(self.rag_system.embeddings_cache),
            "document_embeddings_count": len(self.rag_system.document_embeddings),
            "knowledge_base_size": len(self.rag_system.knowledge_base)
        }
        results["memory_usage"] = memory_info
        print(f"   ✅ Cache entries: {memory_info['embeddings_cache_size']}")

        return results

async def main():
    print("🎯 VECTOR EMBEDDINGS PERFORMANCE TESTING")
    print("This test evaluates the optimized RAG system performance")
    print("-" * 50)

    tester = VectorPerformanceTester()
    results = await tester.run_comprehensive_performance_test()

    # Display comprehensive results
    print("\n" + "=" * 60)
    print("📈 VECTOR PERFORMANCE TEST RESULTS")
    print("=" * 60)

    # Single query results
    single = results["single_query"]
    print(f"🔍 Single Query Performance:")
    print(f"   Processing Time: {single['processing_time']:.3f}s")
    print(f"   Results Found: {single['results_count']}")
    print(f"   Cache Size: {single.get('cache_size', 0)}")

    # Batch performance results
    print(f"\n⚡ Batch Performance:")
    best_qps = 0
    best_concurrency = 0

    for key, batch in results["batch_performance"].items():
        concurrency = key.split("_")[1]
        qps = batch["queries_per_second"]
        print(f"   {concurrency} concurrent: {qps:.1f} queries/sec ({batch['success_rate']:.1f}% success)")

        if qps > best_qps:
            best_qps = qps
            best_concurrency = concurrency

    # Cache performance
    cache = results["cache_performance"]
    print(f"\n💾 Cache Performance:")
    print(f"   Cache Miss: {cache['cache_miss_avg']:.3f}s avg")
    print(f"   Cache Hit: {cache['cache_hit_avg']:.3f}s avg")
    print(f"   Cache Speedup: {cache['cache_speedup']:.1f}x faster")

    # Memory usage
    memory = results["memory_usage"]
    print(f"\n🧠 Memory Usage:")
    print(f"   Embeddings Cache: {memory['embeddings_cache_size']} entries")
    print(f"   Document Embeddings: {memory['document_embeddings_count']} cached")
    print(f"   Knowledge Base: {memory['knowledge_base_size']} documents")

    # Performance classification
    if best_qps > 50:
        classification = "🚀 EXCELLENT (High-performance RAG)"
    elif best_qps > 20:
        classification = "✅ VERY GOOD (Production-ready)"
    elif best_qps > 10:
        classification = "👍 GOOD (Suitable for most use cases)"
    elif best_qps > 5:
        classification = "⚠️  MODERATE (Optimization recommended)"
    else:
        classification = "❌ NEEDS IMPROVEMENT"

    print(f"\n🏆 Performance Classification: {classification}")
    print(f"🏁 Best Performance: {best_qps:.1f} queries/sec at {best_concurrency} concurrent queries")

    # Save detailed results
    print(f"\n💾 Full results saved to vector_performance_results.json")
    with open("vector_performance_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        exit(1)