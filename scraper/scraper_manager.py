import asyncio
import aiohttp
import pandas as pd
import logging
import random
from typing import List, Dict
import importlib
import os
from pathlib import Path

from base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ScraperManager:
    """Manages and orchestrates all individual scrapers"""
    
    def __init__(self):
        self.scrapers = {}
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
    
    async def run_single_scraper(self, scraper_name: str, session: aiohttp.ClientSession) -> pd.DataFrame:
        """Run a single scraper and return its results"""
        try:
            if scraper_name not in self.scrapers:
                logger.error(f"Scraper {scraper_name} not found")
                return pd.DataFrame()
                
            # Create scraper instance
            scraper_class = self.scrapers[scraper_name]
            scraper_instance = scraper_class()
            
            # Get the scraper method
            scraper_methods = self.get_scraper_methods(scraper_instance)
            
            if not scraper_methods:
                logger.error(f"No scraper methods found in {scraper_name}")
                return pd.DataFrame()
            
            # Run the first (and usually only) scraper method
            result = await scraper_methods[0](session)
            
            if isinstance(result, pd.DataFrame):
                logger.info(f"Scraper {scraper_name} completed successfully with {len(result)} jobs")
                return result
            else:
                logger.warning(f"Scraper {scraper_name} returned non-DataFrame result")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error running scraper {scraper_name}: {str(e)}")
            return pd.DataFrame()
    
    async def run_all_scrapers(self, max_concurrent: int = 10) -> pd.DataFrame:
        """Run all scrapers concurrently and return combined results"""
        # Detect GitHub Actions environment and adjust concurrency
        is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        if is_github_actions:
            max_concurrent = min(max_concurrent, 3)  # Reduce concurrency in CI
            logger.info(f"GitHub Actions detected - reducing concurrency to {max_concurrent}")
        
        logger.info(f"Starting {len(self.scrapers)} scrapers with max_concurrent={max_concurrent}")
        
        # Enhanced connector settings for CI environments
        connector_kwargs = {
            'limit': 50,
            'limit_per_host': 10,
            'ttl_dns_cache': 300,
            'use_dns_cache': True,
        }
        
        if is_github_actions:
            connector_kwargs.update({
                'limit': 20,
                'limit_per_host': 5,
                'keepalive_timeout': 30,
                'enable_cleanup_closed': True
            })
        
        connector = aiohttp.TCPConnector(**connector_kwargs)
        timeout = aiohttp.ClientTimeout(total=300 if is_github_actions else 180)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Create semaphore to limit concurrent scrapers
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def run_with_semaphore(scraper_name):
                async with semaphore:
                    if is_github_actions:
                        # Add delay between scraper starts in CI
                        await asyncio.sleep(random.uniform(0.5, 2))
                    return await self.run_single_scraper(scraper_name, session)
            
            # Run all scrapers concurrently
            tasks = [run_with_semaphore(scraper_name) for scraper_name in self.scrapers.keys()]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine all results
            all_dataframes = []
            successful_scrapers = 0
            
            for i, result in enumerate(results):
                scraper_name = list(self.scrapers.keys())[i]
                
                if isinstance(result, Exception):
                    logger.error(f"Scraper {scraper_name} failed with exception: {str(result)}")
                elif isinstance(result, pd.DataFrame) and not result.empty:
                    all_dataframes.append(result)
                    successful_scrapers += 1
                    logger.info(f"Scraper {scraper_name} added {len(result)} jobs")
            
            # Combine all DataFrames
            if all_dataframes:
                combined_df = pd.concat(all_dataframes, ignore_index=True)
                logger.info(f"Total jobs collected: {len(combined_df)} from {successful_scrapers}/{len(self.scrapers)} scrapers")
                return combined_df
            else:
                logger.warning("No data collected from any scrapers")
                return pd.DataFrame()
    
    def get_available_scrapers(self) -> List[str]:
        """Get list of available scraper names"""
        return list(self.scrapers.keys())
    
    def get_scraper_info(self) -> Dict[str, str]:
        """Get information about all loaded scrapers"""
        return {name: cls.__name__ for name, cls in self.scrapers.items()}


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