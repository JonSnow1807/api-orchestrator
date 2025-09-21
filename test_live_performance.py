#!/usr/bin/env python3
"""
LIVE PERFORMANCE TESTING SUITE
Tests the API Orchestrator with a running server to validate real performance metrics
"""

import asyncio
import aiohttp
import time
import statistics
import json
import sys
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor

class LivePerformanceTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_server_health(self) -> bool:
        """Check if the API server is running and responsive"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    print("✅ Server is running and healthy")
                    return True
                else:
                    print(f"⚠️  Server responded with status {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Server health check failed: {e}")
            print("💡 Make sure to start the server first:")
            print("   cd backend && python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000")
            return False

    async def discover_endpoints(self) -> List[str]:
        """Discover available API endpoints"""
        try:
            # Try to get OpenAPI docs
            async with self.session.get(f"{self.base_url}/docs/openapi.json") as response:
                if response.status == 200:
                    openapi_spec = await response.json()
                    endpoints = []
                    for path, methods in openapi_spec.get("paths", {}).items():
                        for method in methods.keys():
                            if method.upper() in ["GET", "POST", "PUT", "DELETE"]:
                                endpoints.append(f"{method.upper()} {path}")
                    print(f"📋 Discovered {len(endpoints)} endpoints from OpenAPI spec")
                    return endpoints[:50]  # Limit to first 50 for testing
        except Exception as e:
            print(f"⚠️  OpenAPI discovery failed: {e}")

        # Fallback to common endpoints
        common_endpoints = [
            "GET /",
            "GET /health",
            "GET /docs",
            "GET /api/status",
            "GET /api/endpoints",
            "POST /api/test",
            "GET /api/metrics",
        ]
        print(f"📋 Using {len(common_endpoints)} common endpoints for testing")
        return common_endpoints

    async def test_endpoint_performance(self, method: str, path: str, concurrent_requests: int = 10) -> Dict:
        """Test performance of a single endpoint"""
        start_time = time.time()
        results = []

        async def make_request():
            request_start = time.time()
            try:
                if method == "GET":
                    async with self.session.get(f"{self.base_url}{path}") as response:
                        status = response.status
                        await response.text()  # Consume response
                elif method == "POST":
                    async with self.session.post(f"{self.base_url}{path}", json={"test": "data"}) as response:
                        status = response.status
                        await response.text()
                else:
                    # For other methods, try as GET
                    async with self.session.get(f"{self.base_url}{path}") as response:
                        status = response.status
                        await response.text()

                request_time = time.time() - request_start
                return {"status": status, "time": request_time, "success": True}
            except Exception as e:
                request_time = time.time() - request_start
                return {"status": 0, "time": request_time, "success": False, "error": str(e)}

        # Execute concurrent requests
        tasks = [make_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Calculate metrics
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]

        if successful_requests:
            response_times = [r["time"] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            requests_per_second = len(successful_requests) / total_time
        else:
            avg_response_time = median_response_time = min_response_time = max_response_time = 0
            requests_per_second = 0

        return {
            "endpoint": f"{method} {path}",
            "total_requests": concurrent_requests,
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": len(successful_requests) / concurrent_requests * 100,
            "total_time": total_time,
            "requests_per_second": requests_per_second,
            "avg_response_time": avg_response_time,
            "median_response_time": median_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
        }

    async def run_performance_suite(self) -> Dict:
        """Run comprehensive performance test suite"""
        print("🚀 LIVE API PERFORMANCE TESTING SUITE")
        print("=" * 60)

        # Check server health
        if not await self.check_server_health():
            return {"error": "Server not available"}

        # Discover endpoints
        endpoints = await self.discover_endpoints()

        print(f"\n📊 Testing {len(endpoints)} endpoints...")

        # Test each endpoint
        endpoint_results = []
        total_requests = 0
        total_successful = 0

        for i, endpoint in enumerate(endpoints):
            parts = endpoint.split(" ", 1)
            method = parts[0] if len(parts) > 1 else "GET"
            path = parts[1] if len(parts) > 1 else endpoint

            print(f"\n{i+1:2d}. Testing {endpoint}...")

            try:
                result = await self.test_endpoint_performance(method, path, concurrent_requests=20)
                endpoint_results.append(result)

                total_requests += result["total_requests"]
                total_successful += result["successful_requests"]

                print(f"    ✅ {result['requests_per_second']:.1f} req/s | "
                      f"{result['success_rate']:.1f}% success | "
                      f"avg: {result['avg_response_time']*1000:.1f}ms")

            except Exception as e:
                print(f"    ❌ Failed: {e}")

        # Calculate overall metrics
        if endpoint_results:
            overall_rps = sum(r["requests_per_second"] for r in endpoint_results)
            overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0
            avg_response_times = [r["avg_response_time"] for r in endpoint_results if r["avg_response_time"] > 0]
            overall_avg_response = statistics.mean(avg_response_times) if avg_response_times else 0

            return {
                "total_endpoints_tested": len(endpoint_results),
                "total_requests": total_requests,
                "total_successful": total_successful,
                "overall_success_rate": overall_success_rate,
                "overall_requests_per_second": overall_rps,
                "overall_avg_response_time": overall_avg_response,
                "endpoint_results": endpoint_results
            }
        else:
            return {"error": "No endpoints could be tested"}

async def main():
    print("🎯 API ORCHESTRATOR LIVE PERFORMANCE TEST")
    print("This test requires the FastAPI server to be running")
    print("-" * 50)

    async with LivePerformanceTester() as tester:
        results = await tester.run_performance_suite()

        if "error" in results:
            print(f"\n❌ TEST FAILED: {results['error']}")
            return 1

        # Display comprehensive results
        print("\n" + "=" * 60)
        print("📈 PERFORMANCE TEST RESULTS")
        print("=" * 60)

        print(f"📊 Total Endpoints Tested: {results['total_endpoints_tested']}")
        print(f"🎯 Total Requests: {results['total_requests']:,}")
        print(f"✅ Successful Requests: {results['total_successful']:,}")
        print(f"📈 Overall Success Rate: {results['overall_success_rate']:.1f}%")
        print(f"⚡ Overall Requests/Second: {results['overall_requests_per_second']:.1f}")
        print(f"⏱️  Average Response Time: {results['overall_avg_response_time']*1000:.1f}ms")

        # Performance classification
        rps = results['overall_requests_per_second']
        if rps > 1000:
            classification = "🚀 EXCELLENT (Enterprise-grade)"
        elif rps > 500:
            classification = "✅ VERY GOOD (Production-ready)"
        elif rps > 100:
            classification = "👍 GOOD (Suitable for most use cases)"
        elif rps > 50:
            classification = "⚠️  MODERATE (Optimization recommended)"
        else:
            classification = "❌ NEEDS IMPROVEMENT"

        print(f"🏆 Performance Classification: {classification}")

        # Top performing endpoints
        sorted_endpoints = sorted(results['endpoint_results'],
                                 key=lambda x: x['requests_per_second'], reverse=True)

        print(f"\n🏆 TOP 5 PERFORMING ENDPOINTS:")
        for i, endpoint in enumerate(sorted_endpoints[:5]):
            print(f"  {i+1}. {endpoint['endpoint']:<25} | "
                  f"{endpoint['requests_per_second']:6.1f} req/s | "
                  f"{endpoint['avg_response_time']*1000:5.1f}ms avg")

        print(f"\n💾 Full results saved to performance_results.json")
        with open("performance_results.json", "w") as f:
            json.dump(results, f, indent=2)

        return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)