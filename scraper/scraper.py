import asyncio
import pandas as pd
import logging
import sys
import time
from datetime import datetime
from scraper_manager import ScraperManager
from base_scraper import BaseScraper

# Configure logging - more detailed for GitHub Actions
import os
is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'

if is_github_actions:
    # More verbose logging for GitHub Actions
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%H:%M:%S'
    )
else:
    # Standard logging for local development
    logging.basicConfig(
        level=logging.ERROR,
        format='%(levelname)s:%(name)s:%(message)s'
    )
logger = logging.getLogger(__name__)


class JobScraper(BaseScraper):
    """
    Modularized Job Scraper that uses individual scraper modules
    """
    
    def __init__(self):
        super().__init__()
        self.scraper_manager = ScraperManager()
        self.data = None
    
    async def get_data_async(self, max_concurrent: int = 10) -> pd.DataFrame:
        """
        Main async method to gather data from all scrapers
        """
        logger.info("Starting modularized job scraping...")
        
        try:
            # Use the scraper manager to run all scrapers
            combined_df = await self.scraper_manager.run_all_scrapers(max_concurrent)
            
            if not combined_df.empty:
                # Add scrape date
                combined_df['scrape_date'] = datetime.now()
                
                # Clean data
                combined_df = combined_df.dropna(subset=['company', 'vacancy'])
                combined_df = combined_df.drop_duplicates()
                
                logger.info(f"Successfully scraped {len(combined_df)} jobs from {len(self.scraper_manager.scrapers)} sources")
                self.data = combined_df
                return combined_df
            else:
                logger.warning("No data collected from any scrapers")
                self.data = pd.DataFrame()
                return self.data
                
        except Exception as e:
            logger.error(f"Error in get_data_async: {str(e)}")
            self.data = pd.DataFrame()
            return self.data
    
    def get_scraper_info(self):
        """Get information about loaded scrapers"""
        return self.scraper_manager.get_scraper_info()
    
    def get_available_scrapers(self):
        """Get list of available scrapers"""
        return self.scraper_manager.get_available_scrapers()


async def main():
    """Main execution function"""
    start_time = time.time()
    
    job_scraper = JobScraper()
    scraper_info = job_scraper.get_scraper_info()
    
    if is_github_actions:
        print(f"::notice title=Initialization::Loaded {len(scraper_info)} scrapers")
    else:
        logger.info(f"Loaded {len(scraper_info)} scrapers")
    
    # Run the scrapers
    await job_scraper.get_data_async()
    
    # Save to database if data was collected
    if job_scraper.data is not None and not job_scraper.data.empty:
        job_count = len(job_scraper.data)
        if is_github_actions:
            print(f"::notice title=Database::Saving {job_count} jobs to database")
        else:
            logger.info(f"Saving {job_count} jobs to database...")
        
        try:
            job_scraper.save_to_db(job_scraper.data)
            total_time = time.time() - start_time
            
            if is_github_actions:
                print(f"::notice title=Complete::Saved {job_count} jobs in {total_time:.1f}s")
            else:
                logger.info(f"✓ Saved {job_count} jobs in {total_time:.1f}s")
                
        except Exception as e:
            error_msg = f"Database error: {str(e)}"
            if is_github_actions:
                print(f"::error title=Database::{error_msg}")
            else:
                logger.error(f"✗ {error_msg}")
            raise
    else:
        if is_github_actions:
            print(f"::warning title=No Data::All scrapers failed or returned empty results")
        else:
            logger.warning(f"⚠ No data collected from any scrapers")


if __name__ == "__main__":
    asyncio.run(main())