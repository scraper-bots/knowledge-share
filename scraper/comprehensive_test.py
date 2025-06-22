#!/usr/bin/env python3
"""
Comprehensive end-to-end testing of modular scrapers
Tests actual scraping, database operations, and data quality
"""

import asyncio
import pandas as pd
import psycopg2
import logging
import sys
import os
import aiohttp
from datetime import datetime
import re
from urllib.parse import urlparse

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import JobScraper
from scraper_manager import ScraperManager
from base_scraper import BaseScraper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveScraperTest:
    def __init__(self):
        self.test_results = {}
        self.scraper_results = {}
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test results"""
        self.test_results[test_name] = {"passed": passed, "details": details}
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{status}: {test_name} - {details}")
        
    async def test_individual_scrapers(self, limit: int = 10):
        """Test individual scrapers one by one"""
        logger.info(f"Testing individual scrapers (limit: {limit})...")
        
        try:
            manager = ScraperManager()
            scrapers_to_test = list(manager.scrapers.keys())[:limit]
            
            working_scrapers = 0
            failed_scrapers = []
            total_jobs = 0
            
            async with aiohttp.ClientSession() as session:
                for scraper_name in scrapers_to_test:
                    try:
                        logger.info(f"Testing scraper: {scraper_name}")
                        result = await manager.run_single_scraper(scraper_name, session)
                        
                        if isinstance(result, pd.DataFrame) and not result.empty:
                            jobs_count = len(result)
                            total_jobs += jobs_count
                            working_scrapers += 1
                            self.scraper_results[scraper_name] = {
                                'status': 'success',
                                'jobs_count': jobs_count,
                                'sample_data': result.head(1).to_dict('records')[0] if jobs_count > 0 else None
                            }
                            logger.info(f"  ✅ {scraper_name}: {jobs_count} jobs")
                        else:
                            failed_scrapers.append(scraper_name)
                            self.scraper_results[scraper_name] = {
                                'status': 'failed',
                                'jobs_count': 0,
                                'sample_data': None
                            }
                            logger.warning(f"  ⚠️ {scraper_name}: No data returned")
                            
                    except Exception as e:
                        failed_scrapers.append(scraper_name)
                        self.scraper_results[scraper_name] = {
                            'status': 'error',
                            'jobs_count': 0,
                            'error': str(e)
                        }
                        logger.error(f"  ❌ {scraper_name}: {str(e)}")
            
            success_rate = (working_scrapers / len(scrapers_to_test)) * 100
            passed = success_rate >= 50  # At least 50% should work
            
            details = f"Tested {len(scrapers_to_test)} scrapers. Working: {working_scrapers}, Failed: {len(failed_scrapers)}, Total jobs: {total_jobs}, Success rate: {success_rate:.1f}%"
            
            self.log_test("Individual Scrapers Test", passed, details)
            return passed
            
        except Exception as e:
            self.log_test("Individual Scrapers Test", False, f"Exception: {str(e)}")
            return False
    
    async def test_full_scraping_cycle(self):
        """Test complete scraping cycle and database insertion"""
        logger.info("Testing full scraping cycle...")
        
        try:
            # Step 1: Record initial database state
            base_scraper = BaseScraper()
            
            with psycopg2.connect(**base_scraper.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM scraper.jobs_jobpost")
                    initial_count = cur.fetchone()[0]
            
            logger.info(f"Initial database count: {initial_count}")
            
            # Step 2: Run full scraping cycle with limited scrapers (for testing)
            job_scraper = JobScraper()
            
            # Override to test only first 5 scrapers for speed
            original_scrapers = job_scraper.scraper_manager.scrapers.copy()
            test_scrapers = dict(list(original_scrapers.items())[:5])
            job_scraper.scraper_manager.scrapers = test_scrapers
            
            logger.info(f"Running scraping cycle with {len(test_scrapers)} scrapers...")
            await job_scraper.get_data_async(max_concurrent=3)
            
            # Step 3: Check if data was collected
            scraped_jobs = len(job_scraper.data) if job_scraper.data is not None else 0
            logger.info(f"Scraped {scraped_jobs} jobs")
            
            # Step 4: Save to database
            if job_scraper.data is not None and not job_scraper.data.empty:
                job_scraper.save_to_db(job_scraper.data)
                logger.info("Data saved to database")
            
            # Step 5: Verify database state after scraping
            with psycopg2.connect(**base_scraper.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM scraper.jobs_jobpost")
                    final_count = cur.fetchone()[0]
                    
                    # Get sample data
                    cur.execute("SELECT title, company, apply_link, source FROM scraper.jobs_jobpost LIMIT 5")
                    sample_data = cur.fetchall()
            
            logger.info(f"Final database count: {final_count}")
            
            # Test passes if:
            # 1. We collected some data
            # 2. Database was updated (TRUNCATE behavior means count = scraped jobs)
            # 3. Final count matches scraped jobs (confirms TRUNCATE worked)
            
            passed = (scraped_jobs > 0 and final_count == scraped_jobs and len(sample_data) > 0)
            
            details = f"Scraped: {scraped_jobs} jobs, DB before: {initial_count}, DB after: {final_count}, TRUNCATE worked: {final_count == scraped_jobs}"
            
            self.log_test("Full Scraping Cycle", passed, details)
            
            # Store results for further analysis
            self.full_cycle_results = {
                'scraped_jobs': scraped_jobs,
                'initial_db_count': initial_count,
                'final_db_count': final_count,
                'sample_data': sample_data,
                'truncate_worked': final_count == scraped_jobs
            }
            
            return passed
            
        except Exception as e:
            self.log_test("Full Scraping Cycle", False, f"Exception: {str(e)}")
            return False
    
    def test_data_integrity(self):
        """Test data integrity in the database"""
        logger.info("Testing data integrity...")
        
        try:
            if not hasattr(self, 'full_cycle_results'):
                self.log_test("Data Integrity", False, "No scraping cycle data available")
                return False
            
            base_scraper = BaseScraper()
            
            with psycopg2.connect(**base_scraper.db_params) as conn:
                with conn.cursor() as cur:
                    # Test 1: Check for NULL values in required fields
                    cur.execute("""
                        SELECT COUNT(*) FROM scraper.jobs_jobpost 
                        WHERE title IS NULL OR title = '' OR 
                              company IS NULL OR company = '' OR 
                              apply_link IS NULL OR apply_link = ''
                    """)
                    null_count = cur.fetchone()[0]
                    
                    # Test 2: Check for duplicates
                    cur.execute("""
                        SELECT COUNT(*) - COUNT(DISTINCT (title, company, apply_link)) 
                        FROM scraper.jobs_jobpost
                    """)
                    duplicate_count = cur.fetchone()[0]
                    
                    # Test 3: Check data length constraints
                    cur.execute("""
                        SELECT COUNT(*) FROM scraper.jobs_jobpost 
                        WHERE LENGTH(title) > 500 OR 
                              LENGTH(company) > 500 OR 
                              LENGTH(apply_link) > 1000 OR 
                              LENGTH(source) > 100
                    """)
                    length_violations = cur.fetchone()[0]
                    
                    # Test 4: Check source field population
                    cur.execute("""
                        SELECT COUNT(*) FROM scraper.jobs_jobpost 
                        WHERE source IS NULL OR source = ''
                    """)
                    missing_source = cur.fetchone()[0]
                    
                    # Test 5: Get total count for percentages
                    cur.execute("SELECT COUNT(*) FROM scraper.jobs_jobpost")
                    total_count = cur.fetchone()[0]
            
            # Calculate integrity metrics
            integrity_issues = null_count + duplicate_count + length_violations + missing_source
            integrity_score = ((total_count - integrity_issues) / total_count * 100) if total_count > 0 else 0
            
            passed = integrity_score >= 95  # 95% or higher integrity score
            
            details = f"Total: {total_count}, Nulls: {null_count}, Duplicates: {duplicate_count}, Length violations: {length_violations}, Missing source: {missing_source}, Integrity: {integrity_score:.1f}%"
            
            self.log_test("Data Integrity", passed, details)
            return passed
            
        except Exception as e:
            self.log_test("Data Integrity", False, f"Exception: {str(e)}")
            return False
    
    def test_data_quality(self):
        """Test data quality - URLs, company names, job titles"""
        logger.info("Testing data quality...")
        
        try:
            base_scraper = BaseScraper()
            
            with psycopg2.connect(**base_scraper.db_params) as conn:
                with conn.cursor() as cur:
                    # Get sample of data for quality analysis
                    cur.execute("""
                        SELECT title, company, apply_link, source 
                        FROM scraper.jobs_jobpost 
                        LIMIT 100
                    """)
                    sample_data = cur.fetchall()
                    
                    # Get total count
                    cur.execute("SELECT COUNT(*) FROM scraper.jobs_jobpost")
                    total_count = cur.fetchone()[0]
            
            if not sample_data:
                self.log_test("Data Quality", False, "No data to analyze")
                return False
            
            quality_issues = []
            
            # Test URL validity
            valid_urls = 0
            for title, company, apply_link, source in sample_data:
                try:
                    parsed = urlparse(apply_link)
                    if parsed.scheme and parsed.netloc:
                        valid_urls += 1
                except:
                    pass
            
            url_quality = (valid_urls / len(sample_data)) * 100
            if url_quality < 80:
                quality_issues.append(f"URL quality low: {url_quality:.1f}%")
            
            # Test for meaningful job titles (not just 'n/a' or empty)
            meaningful_titles = sum(1 for title, _, _, _ in sample_data 
                                  if title and title.lower() not in ['n/a', 'na', 'null', 'none', ''])
            title_quality = (meaningful_titles / len(sample_data)) * 100
            if title_quality < 80:
                quality_issues.append(f"Title quality low: {title_quality:.1f}%")
            
            # Test for meaningful company names
            meaningful_companies = sum(1 for _, company, _, _ in sample_data 
                                     if company and company.lower() not in ['n/a', 'na', 'null', 'none', ''])
            company_quality = (meaningful_companies / len(sample_data)) * 100
            if company_quality < 80:
                quality_issues.append(f"Company quality low: {company_quality:.1f}%")
            
            # Test source determination
            known_sources = sum(1 for _, _, _, source in sample_data 
                              if source and source not in ['Other', 'Unknown'])
            source_quality = (known_sources / len(sample_data)) * 100
            if source_quality < 70:
                quality_issues.append(f"Source detection low: {source_quality:.1f}%")
            
            overall_quality = (url_quality + title_quality + company_quality + source_quality) / 4
            passed = len(quality_issues) == 0 and overall_quality >= 80
            
            details = f"URLs: {url_quality:.1f}%, Titles: {title_quality:.1f}%, Companies: {company_quality:.1f}%, Sources: {source_quality:.1f}%, Overall: {overall_quality:.1f}%"
            if quality_issues:
                details += f", Issues: {'; '.join(quality_issues)}"
            
            self.log_test("Data Quality", passed, details)
            return passed
            
        except Exception as e:
            self.log_test("Data Quality", False, f"Exception: {str(e)}")
            return False
    
    def test_truncate_behavior(self):
        """Specifically test TRUNCATE behavior"""
        logger.info("Testing TRUNCATE behavior...")
        
        try:
            base_scraper = BaseScraper()
            
            # Step 1: Insert test data
            test_data_1 = pd.DataFrame([
                {'company': 'TRUNCATE_TEST_1', 'vacancy': 'Test Job 1', 'apply_link': 'http://test1.com'},
                {'company': 'TRUNCATE_TEST_2', 'vacancy': 'Test Job 2', 'apply_link': 'http://test2.com'}
            ])
            
            base_scraper.save_to_db(test_data_1)
            
            # Verify first insertion
            with psycopg2.connect(**base_scraper.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM scraper.jobs_jobpost WHERE company LIKE 'TRUNCATE_TEST_%'")
                    count_after_first = cur.fetchone()[0]
            
            # Step 2: Insert different test data (should TRUNCATE first)
            test_data_2 = pd.DataFrame([
                {'company': 'TRUNCATE_TEST_3', 'vacancy': 'Test Job 3', 'apply_link': 'http://test3.com'}
            ])
            
            base_scraper.save_to_db(test_data_2)
            
            # Verify TRUNCATE behavior
            with psycopg2.connect(**base_scraper.db_params) as conn:
                with conn.cursor() as cur:
                    # Check total count (should be exactly 1)
                    cur.execute("SELECT COUNT(*) FROM scraper.jobs_jobpost")
                    total_count = cur.fetchone()[0]
                    
                    # Check if old data exists (should be 0)
                    cur.execute("SELECT COUNT(*) FROM scraper.jobs_jobpost WHERE company IN ('TRUNCATE_TEST_1', 'TRUNCATE_TEST_2')")
                    old_data_count = cur.fetchone()[0]
                    
                    # Check if new data exists (should be 1)
                    cur.execute("SELECT COUNT(*) FROM scraper.jobs_jobpost WHERE company = 'TRUNCATE_TEST_3'")
                    new_data_count = cur.fetchone()[0]
            
            # Test passes if:
            # 1. Total count equals new data count (1)
            # 2. Old data was completely removed (0)
            # 3. New data was inserted (1)
            
            truncate_worked = (total_count == 1 and old_data_count == 0 and new_data_count == 1)
            
            details = f"First insert: {count_after_first} rows, After TRUNCATE: Total={total_count}, Old data={old_data_count}, New data={new_data_count}, TRUNCATE worked: {truncate_worked}"
            
            self.log_test("TRUNCATE Behavior", truncate_worked, details)
            return truncate_worked
            
        except Exception as e:
            self.log_test("TRUNCATE Behavior", False, f"Exception: {str(e)}")
            return False
    
    def print_comprehensive_report(self):
        """Print comprehensive test report"""
        print(f"\n{'='*80}")
        print("COMPREHENSIVE SCRAPER TEST REPORT")
        print(f"{'='*80}")
        
        # Test Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['passed'])
        
        print(f"\n📊 TEST SUMMARY")
        print(f"{'='*40}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Individual Test Results
        print(f"\n📋 DETAILED TEST RESULTS")
        print(f"{'='*40}")
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            print(f"{status}: {test_name}")
            if result['details']:
                print(f"   📝 {result['details']}")
        
        # Scraper Analysis
        if hasattr(self, 'scraper_results') and self.scraper_results:
            print(f"\n🔍 INDIVIDUAL SCRAPER ANALYSIS")
            print(f"{'='*40}")
            
            successful_scrapers = [name for name, data in self.scraper_results.items() if data['status'] == 'success']
            failed_scrapers = [name for name, data in self.scraper_results.items() if data['status'] in ['failed', 'error']]
            
            print(f"✅ Working Scrapers ({len(successful_scrapers)}):")
            for scraper in successful_scrapers:
                jobs = self.scraper_results[scraper]['jobs_count']
                print(f"   • {scraper}: {jobs} jobs")
            
            if failed_scrapers:
                print(f"\n❌ Failed Scrapers ({len(failed_scrapers)}):")
                for scraper in failed_scrapers:
                    status = self.scraper_results[scraper]['status']
                    error = self.scraper_results[scraper].get('error', 'No data returned')
                    print(f"   • {scraper}: {status} - {error}")
        
        # Database Analysis
        if hasattr(self, 'full_cycle_results'):
            print(f"\n💾 DATABASE ANALYSIS")
            print(f"{'='*40}")
            results = self.full_cycle_results
            print(f"Jobs Scraped: {results['scraped_jobs']}")
            print(f"DB Before: {results['initial_db_count']}")
            print(f"DB After: {results['final_db_count']}")
            print(f"TRUNCATE Worked: {'✅' if results['truncate_worked'] else '❌'}")
            
            if results['sample_data']:
                print(f"\n📋 Sample Database Records:")
                for i, (title, company, apply_link, source) in enumerate(results['sample_data'], 1):
                    print(f"   {i}. {title[:50]}... | {company[:30]}... | {source}")
        
        # Final Assessment
        print(f"\n🎯 FINAL ASSESSMENT")
        print(f"{'='*40}")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Modular scraper is fully functional and ready for production.")
            print("✅ Data integrity and quality meet requirements.")
            print("✅ Database operations work correctly (TRUNCATE + INSERT).")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️  MOSTLY SUCCESSFUL with minor issues.")
            print("✅ Core functionality works well.")
            print("⚠️  Some scrapers may need attention.")
        else:
            print("❌ SIGNIFICANT ISSUES DETECTED")
            print("❌ Multiple critical tests failed.")
            print("❌ Requires investigation and fixes.")
        
        print(f"\n{'='*80}")

async def main():
    """Run comprehensive tests"""
    print("Starting Comprehensive Scraper Test Suite...")
    print("This will test actual scraping and database operations.")
    print("=" * 80)
    
    tester = ComprehensiveScraperTest()
    
    # Run all tests in sequence
    await tester.test_individual_scrapers(limit=10)  # Test first 10 scrapers
    await tester.test_full_scraping_cycle()
    tester.test_truncate_behavior()
    tester.test_data_integrity()
    tester.test_data_quality()
    
    # Print comprehensive report
    tester.print_comprehensive_report()

if __name__ == "__main__":
    asyncio.run(main())