import logging
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class FintechFarmScraper(BaseScraper):
    """
    Fintech Farm job scraper
    """
    
    @scraper_error_handler
    async def scrape_fintech_farm(self, session):
        """
        Scraper for Fintech Farm careers page
        """
        logger.info("Started scraping Fintech Farm careers")
        
        base_url = "https://www.fintech-farm.com"
        careers_url = f"{base_url}/careers"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }
        
        job_listings = []
        
        try:
            response = await self.fetch_url_async(careers_url, session, headers=headers)
            
            if not response:
                logger.error("Failed to retrieve Fintech Farm careers page")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            
            soup = BeautifulSoup(response, 'html.parser')
            
            # Find all job links - looking for anchor tags with href starting with "/careers/"
            job_links = soup.select('a[href^="/careers/"]')
            
            for job_link in job_links:
                try:
                    # Extract job title from the div with specific class
                    title_element = job_link.select_one('div.root__Root-sc-4rskl8-0.JdHxC')
                    job_title = title_element.text.strip() if title_element else "Unknown Position"
                    
                    # Extract the relative link and construct full URL
                    relative_link = job_link.get('href', '')
                    apply_link = urljoin(base_url, relative_link) if relative_link else careers_url
                    
                    job_listings.append({
                        'company': 'Fintech Farm',
                        'vacancy': job_title,
                        'apply_link': apply_link
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing job listing: {str(e)}")
                    continue
            
            logger.info(f"Successfully scraped {len(job_listings)} jobs from Fintech Farm")
            return pd.DataFrame(job_listings)
            
        except Exception as e:
            logger.error(f"Error scraping Fintech Farm: {str(e)}")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])