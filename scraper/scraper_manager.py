import asyncio
import aiohttp
import pandas as pd
import logging
import random
import traceback
import time
from typing import List, Dict, Tuple
import importlib
import os
from pathlib import Path

from base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ScraperManager:
    """Manages and orchestrates all individual scrapers"""
    
    def __init__(self):
        self.scrapers = {}
        self.scraper_results = {}  # Track detailed results for each scraper
        self.failed_scrapers = {}  # Track failed scrapers with reasons
        self.is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        self.load_scrapers()
    
    def load_scrapers(self):
        """Dynamically load all scraper classes from sources directory"""
        sources_dir = Path(__file__).parent / 'sources'
        
        # Get all .py files in sources directory
        scraper_files = [f.stem for f in sources_dir.glob('*.py') if f.stem != '__init__']
        
        for scraper_file in scraper_files:
            try:
                # Import the module
                module = importlib.import_module(f'sources.{scraper_file}')
                
                # Find the scraper class (should end with 'Scraper')
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BaseScraper) and 
                        attr != BaseScraper):
                        
                        self.scrapers[scraper_file] = attr
                        logger.info(f"Loaded scraper: {scraper_file} -> {attr.__name__}")
                        break
                
            except Exception as e:
                logger.error(f"Failed to load scraper {scraper_file}: {str(e)}")
    
    def get_scraper_methods(self, scraper_instance):
        """Get all scraper methods (parse_* or scrape_*) from an instance"""
        methods = []
        for method_name in dir(scraper_instance):
            if (method_name.startswith('parse_') or method_name.startswith('scrape_')) and callable(getattr(scraper_instance, method_name)):
                methods.append(getattr(scraper_instance, method_name))
        return methods
    
    async def run_single_scraper(self, scraper_name: str, session: aiohttp.ClientSession) -> Tuple[pd.DataFrame, dict]:
        """Run a single scraper and return its results with detailed status info"""
        start_time = time.time()
        scraper_info = {
            'name': scraper_name,
            'start_time': start_time,
            'status': 'unknown',
            'error': None,
            'job_count': 0,
            'duration': 0,
            'method_name': None
        }
        
        try:
            if scraper_name not in self.scrapers:
                error_msg = f"Scraper {scraper_name} not found in loaded scrapers"
                scraper_info.update({'status': 'not_found', 'error': error_msg})
                if self.is_github_actions:
                    print(f"::error title=Scraper Not Found::{error_msg}")
                logger.error(error_msg)
                return pd.DataFrame(), scraper_info
                
            # Create scraper instance
            scraper_class = self.scrapers[scraper_name]
            scraper_instance = scraper_class()
            
            # Get the scraper method
            scraper_methods = self.get_scraper_methods(scraper_instance)
            
            if not scraper_methods:
                error_msg = f"No scraper methods found in {scraper_name} (expected parse_* or scrape_* methods)"
                scraper_info.update({'status': 'no_methods', 'error': error_msg})
                if self.is_github_actions:
                    print(f"::error title=No Scraper Methods::{error_msg}")
                logger.error(error_msg)
                return pd.DataFrame(), scraper_info
            
            # Record the method name being used
            method = scraper_methods[0]
            scraper_info['method_name'] = method.__name__
            
            if self.is_github_actions:
                print(f"::group::Running {scraper_name} ({method.__name__})")
            
            # Run the first (and usually only) scraper method
            result = await method(session)
            
            scraper_info['duration'] = time.time() - start_time
            
            if isinstance(result, pd.DataFrame):
                job_count = len(result)
                scraper_info.update({
                    'status': 'success' if job_count > 0 else 'no_jobs',
                    'job_count': job_count
                })
                
                if job_count > 0:
                    success_msg = f"SUCCESS {scraper_name}: {job_count} jobs in {scraper_info['duration']:.1f}s"
                    logger.info(success_msg)
                    if self.is_github_actions:
                        print(f"::notice title=Scraper Success::{success_msg}")
                else:
                    warning_msg = f"WARNING {scraper_name}: 0 jobs found (method ran but returned empty DataFrame)"
                    logger.warning(warning_msg)
                    if self.is_github_actions:
                        print(f"::warning title=No Jobs Found::{warning_msg}")
                
                return result, scraper_info
            else:
                error_msg = f"Scraper {scraper_name} returned {type(result).__name__} instead of DataFrame"
                scraper_info.update({'status': 'invalid_return', 'error': error_msg})
                logger.warning(error_msg)
                if self.is_github_actions:
                    print(f"::warning title=Invalid Return Type::{error_msg}")
                return pd.DataFrame(), scraper_info
                
        except asyncio.TimeoutError as e:
            scraper_info['duration'] = time.time() - start_time
            error_msg = f"Timeout after {scraper_info['duration']:.1f}s: {str(e)}"
            scraper_info.update({'status': 'timeout', 'error': error_msg})
            logger.error(f"ERROR {scraper_name}: {error_msg}")
            if self.is_github_actions:
                print(f"::error title=Scraper Timeout::{scraper_name} - {error_msg}")
            return pd.DataFrame(), scraper_info
            
        except aiohttp.ClientError as e:
            scraper_info['duration'] = time.time() - start_time
            error_msg = f"HTTP/Network error: {str(e)}"
            scraper_info.update({'status': 'network_error', 'error': error_msg})
            logger.error(f"ERROR {scraper_name}: {error_msg}")
            if self.is_github_actions:
                print(f"::error title=Network Error::{scraper_name} - {error_msg}")
            return pd.DataFrame(), scraper_info
            
        except Exception as e:
            scraper_info['duration'] = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"
            scraper_info.update({'status': 'exception', 'error': error_msg})
            
            # Get full traceback for debugging
            if self.is_github_actions:
                full_traceback = traceback.format_exc()
                print(f"::error title=Scraper Exception::{scraper_name} failed - {error_msg}")
                print(f"::group::Full traceback for {scraper_name}")
                print(full_traceback)
                print("::endgroup::")
            
            logger.error(f"ERROR {scraper_name}: {error_msg}")
            return pd.DataFrame(), scraper_info
            
        finally:
            if self.is_github_actions:
                print("::endgroup::")
    
    async def run_all_scrapers(self, max_concurrent: int = 10) -> pd.DataFrame:
        """Run all scrapers concurrently and return combined results with detailed logging"""
        # Clear previous results
        self.scraper_results = {}
        self.failed_scrapers = {}
        
        if self.is_github_actions:
            max_concurrent = min(max_concurrent, 3)  # Reduce concurrency in CI
            print(f"::notice title=GitHub Actions Mode::Reducing concurrency to {max_concurrent} for better stability")
        
        total_scrapers = len(self.scrapers)
        logger.info(f"Starting {total_scrapers} scrapers with max_concurrent={max_concurrent}")
        
        if self.is_github_actions:
            print(f"::group::Scraper Execution Summary")
            print(f"Total scrapers to run: {total_scrapers}")
            print(f"Concurrency limit: {max_concurrent}")
            print(f"Environment: GitHub Actions")
            print("::endgroup::")
        
        # Enhanced connector settings for CI environments
        connector_kwargs = {
            'limit': 50,
            'limit_per_host': 10,
            'ttl_dns_cache': 300,
            'use_dns_cache': True,
        }
        
        if self.is_github_actions:
            connector_kwargs.update({
                'limit': 20,
                'limit_per_host': 5,
                'keepalive_timeout': 30,
                'enable_cleanup_closed': True
            })
        
        connector = aiohttp.TCPConnector(**connector_kwargs)
        timeout = aiohttp.ClientTimeout(total=300 if self.is_github_actions else 180)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Create semaphore to limit concurrent scrapers
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def run_with_semaphore(scraper_name):
                async with semaphore:
                    if self.is_github_actions:
                        # Add delay between scraper starts in CI
                        await asyncio.sleep(random.uniform(0.5, 2))
                    return await self.run_single_scraper(scraper_name, session)
            
            # Run all scrapers concurrently
            start_time = time.time()
            tasks = [run_with_semaphore(scraper_name) for scraper_name in self.scrapers.keys()]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_duration = time.time() - start_time
            
            # Process and categorize all results
            all_dataframes = []
            successful_scrapers = 0
            failed_count = 0
            no_jobs_count = 0
            
            for i, result in enumerate(results):
                scraper_name = list(self.scrapers.keys())[i]
                
                if isinstance(result, Exception):
                    # Handle exceptions that weren't caught by run_single_scraper
                    error_info = {
                        'name': scraper_name,
                        'status': 'unhandled_exception',
                        'error': str(result),
                        'duration': 0
                    }
                    self.failed_scrapers[scraper_name] = error_info
                    failed_count += 1
                    
                    logger.error(f"❌ {scraper_name}: Unhandled exception - {str(result)}")
                    if self.is_github_actions:
                        print(f"::error title=Unhandled Exception::{scraper_name} - {str(result)}")
                        
                elif isinstance(result, tuple) and len(result) == 2:
                    # Normal result from run_single_scraper
                    dataframe, scraper_info = result
                    self.scraper_results[scraper_name] = scraper_info
                    
                    if scraper_info['status'] == 'success':
                        all_dataframes.append(dataframe)
                        successful_scrapers += 1
                    elif scraper_info['status'] == 'no_jobs':
                        no_jobs_count += 1
                    else:
                        self.failed_scrapers[scraper_name] = scraper_info
                        failed_count += 1
                else:
                    # Unexpected result format
                    error_info = {
                        'name': scraper_name,
                        'status': 'unexpected_result',
                        'error': f"Unexpected result type: {type(result)}",
                        'duration': 0
                    }
                    self.failed_scrapers[scraper_name] = error_info
                    failed_count += 1
            
            # Generate comprehensive summary
            self._log_execution_summary(total_scrapers, successful_scrapers, no_jobs_count, failed_count, total_duration)
            
            # Combine all DataFrames
            if all_dataframes:
                combined_df = pd.concat(all_dataframes, ignore_index=True)
                total_jobs = len(combined_df)
                logger.info(f"FINAL RESULT: {total_jobs} jobs from {successful_scrapers} successful scrapers")
                return combined_df
            else:
                logger.warning("WARNING: No data collected from any scrapers")
                if self.is_github_actions:
                    print("::warning title=No Data Collected::All scrapers failed or returned empty results")
                return pd.DataFrame()
    
    def get_available_scrapers(self) -> List[str]:
        """Get list of available scraper names"""
        return list(self.scrapers.keys())
    
    def get_scraper_info(self) -> Dict[str, str]:
        """Get information about all loaded scrapers"""
        return {name: cls.__name__ for name, cls in self.scrapers.items()}
    
    def _log_execution_summary(self, total_scrapers: int, successful: int, no_jobs: int, failed: int, duration: float):
        """Log comprehensive execution summary"""
        
        if self.is_github_actions:
            print(f"::group::Execution Summary - {successful}/{total_scrapers} successful")
        
        logger.info(f"\n" + "="*60)
        logger.info(f"SCRAPER EXECUTION SUMMARY")
        logger.info(f"="*60)
        logger.info(f"Successful (with jobs): {successful}")
        logger.info(f"Successful (no jobs): {no_jobs}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total duration: {duration:.1f}s")
        logger.info(f"="*60)
        
        if self.is_github_actions:
            print(f"Successful scrapers: {successful}")
            print(f"Empty results: {no_jobs}")
            print(f"Failed scrapers: {failed}")
            print(f"Total time: {duration:.1f}s")
        
        # Log failed scrapers with details
        if self.failed_scrapers:
            logger.error(f"\\nFAILED SCRAPERS DETAILS:")
            if self.is_github_actions:
                print(f"\\nFailed Scrapers Details:")
            
            # Group failures by type
            failure_types = {}
            for name, info in self.failed_scrapers.items():
                status = info['status']
                if status not in failure_types:
                    failure_types[status] = []
                failure_types[status].append((name, info))
            
            for failure_type, scrapers in failure_types.items():
                type_label = failure_type.replace('_', ' ').title()
                logger.error(f"\\n  {type_label} ({len(scrapers)} scrapers):")
                
                if self.is_github_actions:
                    print(f"\\n  {type_label}:")
                
                for name, info in scrapers:
                    duration_str = f" ({info['duration']:.1f}s)" if info['duration'] > 0 else ""
                    error_msg = info.get('error', 'Unknown error')
                    
                    logger.error(f"    • {name}{duration_str}: {error_msg}")
                    if self.is_github_actions:
                        print(f"    • {name}{duration_str}: {error_msg}")
        
        # Log successful scrapers summary
        if successful > 0:
            logger.info(f"\\nSUCCESSFUL SCRAPERS:")
            if self.is_github_actions:
                print(f"\\nSuccessful Scrapers:")
            
            success_list = []
            for name, info in self.scraper_results.items():
                if info['status'] == 'success':
                    success_list.append((name, info['job_count'], info['duration']))
            
            # Sort by job count (descending)
            success_list.sort(key=lambda x: x[1], reverse=True)
            
            for name, job_count, duration in success_list:
                logger.info(f"  • {name}: {job_count} jobs ({duration:.1f}s)")
                if self.is_github_actions:
                    print(f"  • {name}: {job_count} jobs ({duration:.1f}s)")
        
        if self.is_github_actions:
            print("::endgroup::")
        
        logger.info("="*60)


# Backwards compatibility - main execution function
async def get_data_async() -> pd.DataFrame:
    """Main function to run all scrapers - maintains compatibility with original scraper.py"""
    manager = ScraperManager()
    return await manager.run_all_scrapers()


if __name__ == "__main__":
    # Test the scraper manager
    async def test_scrapers():
        manager = ScraperManager()
        print(f"Loaded scrapers: {manager.get_scraper_info()}")
        
        # Run all scrapers
        results = await manager.run_all_scrapers(max_concurrent=5)
        print(f"Total results: {len(results)} jobs")
        
        if not results.empty:
            print("\nSample results:")
            print(results.head())
    
    asyncio.run(test_scrapers())