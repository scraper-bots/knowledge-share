import asyncio
import pandas as pd
import logging
from datetime import datetime
from scraper_manager import ScraperManager
from base_scraper import BaseScraper

# Configure logging
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
    job_scraper = JobScraper()
    
    # Print loaded scrapers info
    scraper_info = job_scraper.get_scraper_info()
    logger.info(f"Loaded {len(scraper_info)} scrapers: {list(scraper_info.keys())}")
    
    # Run the scrapers
    await job_scraper.get_data_async()
    
    # Save to database if data was collected
    if job_scraper.data is not None and not job_scraper.data.empty:
        logger.info(f"Saving {len(job_scraper.data)} jobs to database...")
        job_scraper.save_to_db(job_scraper.data)
        logger.info("Data successfully saved to database")
    else:
        logger.warning("No data to save to database")


if __name__ == "__main__":
    asyncio.run(main())