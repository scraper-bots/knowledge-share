#!/usr/bin/env python3
"""
Comprehensive test script for modular scraper
Tests all aspects: data insertion, deletion, compatibility, etc.
"""

import asyncio
import pandas as pd
import psycopg2
import logging
import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import JobScraper
from scraper_manager import ScraperManager
from base_scraper import BaseScraper

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestModularScraper:
    def __init__(self):
        self.test_results = {}
        self.job_scraper = JobScraper()
        
    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test results"""
        self.test_results[test_name] = {"passed": passed, "details": details}
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{status}: {test_name} - {details}")
    
    def test_scraper_loading(self):
        """Test 1: Check if all scrapers are loaded correctly"""
        try:
            manager = ScraperManager()
            loaded_count = len(manager.scrapers)
            scraper_info = manager.get_scraper_info()
            
            expected_minimum = 50  # We should have at least 50 scrapers
            passed = loaded_count >= expected_minimum
            
            details = f"Loaded {loaded_count} scrapers. Expected minimum: {expected_minimum}"
            if loaded_count > 0:
                details += f". Sample scrapers: {list(scraper_info.keys())[:5]}"
            
            self.log_test_result("Scraper Loading", passed, details)
            return passed
            
        except Exception as e:
            self.log_test_result("Scraper Loading", False, f"Exception: {str(e)}")
            return False
    
    def test_database_connection(self):
        """Test 2: Check database connectivity"""
        try:
            base_scraper = BaseScraper()
            with psycopg2.connect(**base_scraper.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    
            passed = result[0] == 1
            self.log_test_result("Database Connection", passed, "Successfully connected to database")
            return passed
            
        except Exception as e:
            self.log_test_result("Database Connection", False, f"Connection failed: {str(e)}")
            return False
    
    def test_table_exists(self):
        """Test 3: Check if target table exists"""
        try:
            base_scraper = BaseScraper()
            with psycopg2.connect(**base_scraper.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'scraper' 
                            AND table_name = 'jobs_jobpost'
                        )
                    """)
                    table_exists = cur.fetchone()[0]
                    
            self.log_test_result("Table Exists", table_exists, 
                               "scraper.jobs_jobpost table found" if table_exists else "Table not found")
            return table_exists
            
        except Exception as e:
            self.log_test_result("Table Exists", False, f"Error checking table: {str(e)}")
            return False
    
    def test_data_deletion_truncate(self):
        """Test 4: Verify TRUNCATE behavior (deletes all old data)"""
        try:
            base_scraper = BaseScraper()
            
            # First, insert some test data
            test_data = pd.DataFrame([
                {'company': 'Test Company 1', 'vacancy': 'Test Job 1', 'apply_link': 'http://test1.com'},
                {'company': 'Test Company 2', 'vacancy': 'Test Job 2', 'apply_link': 'http://test2.com'}
            ])
            
            # Save test data
            base_scraper.save_to_db(test_data)
            
            # Check if data was inserted
            with psycopg2.connect(**base_scraper.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM scraper.jobs_jobpost")
                    count_after_insert = cur.fetchone()[0]
            
            # Now save different data (should truncate and replace)
            new_test_data = pd.DataFrame([
                {'company': 'New Company', 'vacancy': 'New Job', 'apply_link': 'http://newtest.com'}
            ])
            
            base_scraper.save_to_db(new_test_data)
            
            # Check final count
            with psycopg2.connect(**base_scraper.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM scraper.jobs_jobpost")
                    final_count = cur.fetchone()[0]
                    
                    # Check if we have exactly the new data (truncate + insert)
                    cur.execute("SELECT company FROM scraper.jobs_jobpost WHERE company = 'New Company'")
                    new_data_exists = cur.fetchone() is not None
                    
                    cur.execute("SELECT company FROM scraper.jobs_jobpost WHERE company = 'Test Company 1'")
                    old_data_exists = cur.fetchone() is not None
            
            # Test passes if:
            # 1. Final count equals new data count (1)
            # 2. New data exists
            # 3. Old data doesn't exist (was truncated)
            passed = (final_count == 1 and new_data_exists and not old_data_exists)
            
            details = f"Final count: {final_count}, New data exists: {new_data_exists}, Old data removed: {not old_data_exists}"
            self.log_test_result("Data Deletion (TRUNCATE)", passed, details)
            return passed
            
        except Exception as e:
            self.log_test_result("Data Deletion (TRUNCATE)", False, f"Exception: {str(e)}")
            return False
    
    def test_column_mapping(self):
        """Test 5: Verify correct column mapping (vacancy->title, etc.)"""
        try:
            base_scraper = BaseScraper()
            
            # Insert test data with specific values
            test_data = pd.DataFrame([
                {
                    'company': 'Mapping Test Company',
                    'vacancy': 'Mapping Test Position',
                    'apply_link': 'http://glorri.az/test-mapping'
                }
            ])
            
            base_scraper.save_to_db(test_data)
            
            # Check if data was mapped correctly
            with psycopg2.connect(**base_scraper.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT title, company, apply_link, source 
                        FROM scraper.jobs_jobpost 
                        WHERE company = 'Mapping Test Company'
                    """)
                    result = cur.fetchone()
            
            if result:
                title, company, apply_link, source = result
                passed = (
                    title == 'Mapping Test Position' and  # vacancy -> title
                    company == 'Mapping Test Company' and  # company -> company
                    apply_link == 'http://glorri.az/test-mapping' and  # apply_link -> apply_link
                    source == 'Glorri'  # source determined from URL
                )
                details = f"Mapped correctly: title='{title}', company='{company}', source='{source}'"
            else:
                passed = False
                details = "No data found after insertion"
            
            self.log_test_result("Column Mapping", passed, details)
            return passed
            
        except Exception as e:
            self.log_test_result("Column Mapping", False, f"Exception: {str(e)}")
            return False
    
    def test_source_determination(self):
        """Test 6: Test source determination from URLs"""
        try:
            base_scraper = BaseScraper()
            
            test_cases = [
                ('http://glorri.az/job/123', 'Glorri'),
                ('https://careers.azercell.com/vacancy', 'Azercell'),
                ('http://djinni.co/jobs/456', 'Djinni'),
                ('http://unknown-site.com/job', 'Other'),
                ('', 'Unknown')
            ]
            
            all_passed = True
            details_list = []
            
            for url, expected_source in test_cases:
                actual_source = base_scraper.determine_source(url)
                case_passed = actual_source == expected_source
                all_passed = all_passed and case_passed
                details_list.append(f"{url} -> {actual_source} (expected: {expected_source}) {'✓' if case_passed else '✗'}")
            
            details = "; ".join(details_list)
            self.log_test_result("Source Determination", all_passed, details)
            return all_passed
            
        except Exception as e:
            self.log_test_result("Source Determination", False, f"Exception: {str(e)}")
            return False
    
    async def test_single_scraper_run(self):
        """Test 7: Test running a single scraper"""
        try:
            manager = ScraperManager()
            if not manager.scrapers:
                self.log_test_result("Single Scraper Run", False, "No scrapers loaded")
                return False
            
            # Get first available scraper
            scraper_name = list(manager.scrapers.keys())[0]
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                result = await manager.run_single_scraper(scraper_name, session)
            
            passed = isinstance(result, pd.DataFrame)
            details = f"Scraper '{scraper_name}' returned DataFrame with {len(result)} rows" if passed else f"Scraper '{scraper_name}' failed"
            
            self.log_test_result("Single Scraper Run", passed, details)
            return passed
            
        except Exception as e:
            self.log_test_result("Single Scraper Run", False, f"Exception: {str(e)}")
            return False
    
    def test_github_actions_compatibility(self):
        """Test 8: Test GitHub Actions compatibility"""
        try:
            # Check if the main entry point works
            import subprocess
            import sys
            
            # Test the main scraper file syntax
            result = subprocess.run([sys.executable, '-m', 'py_compile', 'scraper.py'], 
                                  capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
            
            syntax_ok = result.returncode == 0
            
            # Check if required environment variables are expected
            required_env_vars = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'EMAIL', 'PASSWORD']
            env_vars_ok = all(var in os.environ for var in required_env_vars)
            
            passed = syntax_ok and env_vars_ok
            details = f"Syntax OK: {syntax_ok}, Env vars present: {env_vars_ok}"
            if not env_vars_ok:
                missing = [var for var in required_env_vars if var not in os.environ]
                details += f", Missing: {missing}"
            
            self.log_test_result("GitHub Actions Compatibility", passed, details)
            return passed
            
        except Exception as e:
            self.log_test_result("GitHub Actions Compatibility", False, f"Exception: {str(e)}")
            return False
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['passed'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n{'='*60}")
        print("DETAILED RESULTS")
        print(f"{'='*60}")
        
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            print(f"{status}: {test_name}")
            if result['details']:
                print(f"   Details: {result['details']}")
        
        print(f"\n{'='*60}")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Modular scraper is fully compatible.")
        else:
            print("⚠️  Some tests failed. Please review the issues above.")
        
        print(f"{'='*60}")

async def main():
    """Run all tests"""
    print("Starting Modular Scraper Test Suite...")
    print("="*60)
    
    tester = TestModularScraper()
    
    # Run all tests
    tester.test_scraper_loading()
    tester.test_database_connection()
    tester.test_table_exists()
    tester.test_data_deletion_truncate()
    tester.test_column_mapping()
    tester.test_source_determination()
    await tester.test_single_scraper_run()
    tester.test_github_actions_compatibility()
    
    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())