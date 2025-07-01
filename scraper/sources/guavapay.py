import logging
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class GuavapayScraper(BaseScraper):
    """
    Guavapay job scraper
    """
    
    @scraper_error_handler
    async def scrape_guavapay(self, session):
        """
        Scraper for Guavapay careers page
        """
        logger.info("Started scraping Guavapay careers")
        
        base_url = "https://guavalab.az"
        careers_url = f"{base_url}/en/careers"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }
        
        job_listings = []
        
        try:
            # Fetch the main careers page
            response = await self.fetch_url_async(careers_url, session, headers=headers)
            
            if not response:
                logger.error("Failed to retrieve Guavapay careers page")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            
            soup = BeautifulSoup(response, 'html.parser')
            
            # Find all job cards on the page
            job_cards = soup.select('div.flex.flex-col.gap-y-6.rounded-2xl.bg-\\[\\#F0F4F3\\].p-8')
            
            if not job_cards:
                # Try alternative selector if the first one doesn't match
                job_cards = soup.select('div.rounded-2xl.bg-[#F0F4F3]')
                
            if not job_cards:
                logger.warning("No job cards found on Guavapay careers page")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
                
            logger.info(f"Found {len(job_cards)} job cards on Guavapay careers page")
            
            for job_card in job_cards:
                try:
                    # Extract job title
                    title_element = job_card.select_one('h3')
                    job_title = title_element.text.strip() if title_element else "Unknown Position"
                    
                    # Extract application link - look for the "See details" button specifically
                    link_element = job_card.select_one('a[href*="/careers/"]')
                    if not link_element:
                        # Fallback to any link that contains "See details" text
                        link_element = job_card.find('a', string=lambda text: text and 'See details' in text)
                    relative_link = link_element['href'] if link_element and 'href' in link_element.attrs else None
                    
                    # Construct the full application link
                    apply_link = urljoin(base_url, relative_link) if relative_link else careers_url
                    
                    job_listings.append({
                        'company': 'Guavapay',
                        'vacancy': job_title,
                        'apply_link': apply_link
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing job card: {str(e)}")
                    continue
            
            logger.info(f"Successfully scraped {len(job_listings)} jobs from Guavapay")
            return pd.DataFrame(job_listings)
            
        except Exception as e:
            logger.error(f"Error scraping Guavapay: {str(e)}")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])