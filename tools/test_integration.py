"""
Treasury Service Integration Test

Tests key API endpoints and functionality without making expensive LLM calls.
"""

import requests
import time
import json
from datetime import datetime


class TreasuryServiceTester:
    """Test suite for treasury service integration."""
    
    def __init__(self, base_url="http://localhost:8003"):
        self.base_url = base_url
        self.results = []
    
    def test_endpoint(self, endpoint, method="GET", data=None, expected_status=200):
        """Test a specific endpoint and return results."""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=5)
            else:
                return {"endpoint": endpoint, "status": "error", "error": f"Unsupported method: {method}"}
            
            success = response.status_code == expected_status
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "status": "success" if success else "failed", 
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "content_type": response.headers.get("content-type", ""),
                "response_size": len(response.content)
            }
            
            # Try to parse JSON response
            try:
                result["response_data"] = response.json()
            except:
                result["response_data"] = response.text[:200]
            
            return result
            
        except Exception as e:
            return {
                "endpoint": endpoint,
                "status": "error",
                "error": str(e)
            }
    
    def run_basic_tests(self):
        """Run basic API tests without LLM calls."""
        print("🧪 Treasury Service Integration Tests")
        print("=" * 50)
        
        # Test basic endpoints
        tests = [
            ("/health", "GET"),
            ("/", "GET"),
        ]
        
        for endpoint, method in tests:
            print(f"\n📋 Testing {method} {endpoint}...")
            result = self.test_endpoint(endpoint, method)
            self.results.append(result)
            
            if result["status"] == "success":
                print(f"   ✅ Status: {result['status_code']}")
                print(f"   ⏱️  Response Time: {result['response_time']:.3f}s")
                if "response_data" in result:
                    print(f"   📄 Response: {json.dumps(result['response_data'], indent=2)}")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        
        self.print_summary()
    
    def test_mock_api_integration(self):
        """Test MockBankAPI integration (non-LLM)."""
        print("\n🏦 Testing MockBankAPI Integration...")
        
        # This tests the MockBankAPI without LLM calls
        result = self.test_endpoint("/test/mock-api", "GET")
        self.results.append(result)
        
        if result["status"] == "success":
            print("   ✅ MockBankAPI integration working")
            response = result.get("response_data", {})
            if isinstance(response, dict):
                print(f"   📊 Balance count: {response.get('sample_balances_count', 'N/A')}")
                print(f"   💳 Payments count: {response.get('sample_payments_count', 'N/A')}")
        else:
            print(f"   ❌ MockBankAPI test failed: {result.get('error', 'Unknown error')}")
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r["status"] == "success"])
        failed_tests = total_tests - successful_tests
        
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Successful: {successful_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        
        avg_response_time = sum(r.get("response_time", 0) for r in self.results if "response_time" in r) / max(1, len([r for r in self.results if "response_time" in r]))
        print(f"   ⏱️  Avg Response Time: {avg_response_time:.3f}s")
        
        if failed_tests == 0:
            print("\n🎉 All tests passed! Treasury service is running correctly.")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed. Check the details above.")
        
        return failed_tests == 0


if __name__ == "__main__":
    tester = TreasuryServiceTester()
    
    print("Starting Treasury Service Integration Tests...")
    print(f"Target URL: {tester.base_url}")
    print(f"Test Time: {datetime.now().isoformat()}")
    
    # Run basic API tests
    tester.run_basic_tests()
    
    # Test MockBankAPI integration (non-LLM)
    tester.test_mock_api_integration()
    
    # Save results for reference
    with open("logs/integration_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "test_results": tester.results,
            "summary": {
                "total_tests": len(tester.results),
                "successful": len([r for r in tester.results if r["status"] == "success"]),
                "failed": len([r for r in tester.results if r["status"] != "success"])
            }
        }, f, indent=2)
    
    print("\n📝 Test results saved to logs/integration_test_results.json")