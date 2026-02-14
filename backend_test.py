"""
Backend API Testing for Climate Credit Risk Intelligence Platform
Testing all endpoints with comprehensive coverage
"""
import requests
import sys
import json
from datetime import datetime

class ClimateRiskAPITester:
    def __init__(self, base_url="https://risk-analysis-7.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json() if response.content else {}
                except:
                    response_data = {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                response_data = {}

            # Store test result
            self.test_results.append({
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "response_size": len(response.content) if response.content else 0
            })

            return success, response_data

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout ({timeout}s)")
            self.test_results.append({
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": "TIMEOUT",
                "success": False,
                "error": "Request timeout"
            })
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": "ERROR",
                "success": False,
                "error": str(e)
            })
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        return self.run_test("Health Check", "GET", "/api/health", 200)

    def test_generate_sample_data(self):
        """Generate sample data for testing"""
        return self.run_test("Generate Sample Data", "POST", "/api/sample-data/generate", 200)

    def test_portfolio_operations(self):
        """Test portfolio CRUD operations"""
        results = []
        
        # Test get portfolios (empty or existing)
        success, data = self.run_test("Get Portfolios", "GET", "/api/portfolios", 200)
        results.append(success)
        existing_portfolios = data.get('portfolios', []) if success else []

        # Create a test portfolio
        test_portfolio_data = {
            "name": f"Test Portfolio {datetime.now().strftime('%H%M%S')}",
            "description": "Test portfolio for API validation"
        }
        success, portfolio_data = self.run_test(
            "Create Portfolio", "POST", "/api/portfolios", 200, test_portfolio_data
        )
        results.append(success)
        
        if success and 'id' in portfolio_data:
            portfolio_id = portfolio_data['id']
            
            # Get specific portfolio
            success, _ = self.run_test(
                "Get Portfolio by ID", "GET", f"/api/portfolios/{portfolio_id}", 200
            )
            results.append(success)
            
            # Update portfolio
            update_data = {
                "name": f"Updated Portfolio {datetime.now().strftime('%H%M%S')}",
                "description": "Updated description"
            }
            success, _ = self.run_test(
                "Update Portfolio", "PUT", f"/api/portfolios/{portfolio_id}", 200, update_data
            )
            results.append(success)
            
            # Test adding asset to portfolio
            test_asset = {
                "asset": {
                    "id": f"test_asset_{datetime.now().strftime('%H%M%S')}",
                    "asset_type": "Bond",
                    "company": {
                        "name": "Test Energy Corp",
                        "sector": "Power Generation",
                        "subsector": "Coal"
                    },
                    "exposure": 1000000.0,
                    "market_value": 950000.0,
                    "base_pd": 0.02,
                    "base_lgd": 0.45,
                    "rating": "BBB",
                    "maturity_years": 5
                }
            }
            success, _ = self.run_test(
                "Add Asset to Portfolio", "POST", f"/api/portfolios/{portfolio_id}/assets", 200, test_asset
            )
            results.append(success)
            
            # Get updated portfolio to verify asset was added
            success, updated_portfolio = self.run_test(
                "Verify Asset Added", "GET", f"/api/portfolios/{portfolio_id}", 200
            )
            results.append(success)
            
            if success and updated_portfolio.get('assets'):
                asset_id = updated_portfolio['assets'][0]['id']
                
                # Test removing asset from portfolio
                success, _ = self.run_test(
                    "Remove Asset from Portfolio", "DELETE", f"/api/portfolios/{portfolio_id}/assets/{asset_id}", 200
                )
                results.append(success)
            
            # Delete portfolio (cleanup)
            success, _ = self.run_test(
                "Delete Portfolio", "DELETE", f"/api/portfolios/{portfolio_id}", 200
            )
            results.append(success)
        
        return all(results)

    def test_scenario_data_operations(self):
        """Test scenario data operations"""
        results = []
        
        # Get scenario data overview
        success, scenario_data = self.run_test("Get Scenario Data Overview", "GET", "/api/scenario-data", 200)
        results.append(success)
        
        # If no data exists, refresh it
        if success and scenario_data.get('total_records', 0) == 0:
            print("   No scenario data found, refreshing...")
            success, _ = self.run_test("Refresh Scenario Data", "POST", "/api/scenario-data/refresh", 200, {"force": False}, timeout=60)
            results.append(success)
            
            # Get scenario data again after refresh
            success, _ = self.run_test("Get Scenario Data After Refresh", "GET", "/api/scenario-data", 200)
            results.append(success)
        
        return all(results)

    def test_analysis_operations(self):
        """Test analysis run operations"""
        results = []
        
        # First ensure we have sample data and scenario data
        sample_success, sample_data = self.test_generate_sample_data()
        if not sample_success:
            print("❌ Cannot test analysis without sample data")
            return False
        
        # Get portfolios to use for analysis
        success, portfolios_data = self.run_test("Get Portfolios for Analysis", "GET", "/api/portfolios", 200)
        results.append(success)
        
        if success and portfolios_data.get('portfolios'):
            portfolio = portfolios_data['portfolios'][0]
            portfolio_id = portfolio['id']
            
            # Run analysis
            analysis_request = {
                "portfolio_id": portfolio_id,
                "scenarios": ["Orderly", "Disorderly"],
                "horizons": [2030, 2040]
            }
            success, analysis_data = self.run_test(
                "Run Scenario Analysis", "POST", "/api/analysis/run", 200, analysis_request, timeout=120
            )
            results.append(success)
            
            if success and 'id' in analysis_data:
                run_id = analysis_data['id']
                
                # Get all analysis runs
                success, _ = self.run_test("Get Analysis Runs", "GET", "/api/analysis/runs", 200)
                results.append(success)
                
                # Get specific analysis run
                success, _ = self.run_test(
                    "Get Analysis Run by ID", "GET", f"/api/analysis/runs/{run_id}", 200
                )
                results.append(success)
                
                # Delete analysis run (cleanup)
                success, _ = self.run_test(
                    "Delete Analysis Run", "DELETE", f"/api/analysis/runs/{run_id}", 200
                )
                results.append(success)
        
        return all(results)

    def run_all_tests(self):
        """Run comprehensive API test suite"""
        print("🚀 Starting Climate Risk API Test Suite")
        print("=" * 60)
        
        # Test health check first
        health_ok, _ = self.test_health_check()
        if not health_ok:
            print("\n❌ Health check failed - aborting further tests")
            return False
        
        # Run test categories
        test_categories = [
            ("Portfolio Operations", self.test_portfolio_operations),
            ("Scenario Data Operations", self.test_scenario_data_operations),
            ("Analysis Operations", self.test_analysis_operations)
        ]
        
        category_results = []
        for category_name, test_func in test_categories:
            print(f"\n📊 Testing {category_name}")
            print("-" * 40)
            try:
                result = test_func()
                category_results.append(result)
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"\n{category_name}: {status}")
            except Exception as e:
                print(f"\n❌ {category_name} failed with exception: {str(e)}")
                category_results.append(False)
        
        # Final results
        print("\n" + "=" * 60)
        print(f"📊 Final Results: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"🎯 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Detailed results
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   - {test['name']}: {test.get('actual_status', 'ERROR')}")
        
        return all(category_results)

def main():
    """Main test execution"""
    tester = ClimateRiskAPITester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Test suite crashed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())