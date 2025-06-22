import logging
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class AzercosmosScraper(BaseScraper):
    """
    Azercosmos job scraper
    """
    
    @scraper_error_handler
    async def parse_azercosmos(self, session):
        """
        Scrape job vacancies from Azercosmos careers page with enhanced parsing
        """
        logger.info("Started scraping Azercosmos")
        url = "https://azercosmos.az/en/about-us/careers"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
            response = await self.fetch_url_async(url, session, headers=headers)
            
            if not response:
                logger.error("Failed to retrieve the Azercosmos careers page")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            
            soup = BeautifulSoup(response, 'html.parser')
            job_listings = []
            
            # First, find the section containing careers
            careers_section = soup.find('section', class_='careers')
            if not careers_section:
                logger.warning("Careers section not found")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            
            # Find the positions container
            positions_div = careers_section.find('div', class_='positions')
            if not positions_div:
                logger.warning("Positions container not found")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            
            # Find all collapsible job divs within the positions container
            collapsibles = positions_div.find_all('div', class_='collapsible')
            base_url = "https://azercosmos.az"
            
            for collapsible in collapsibles:
                try:
                    # Find the label containing the job title
                    label = collapsible.find('label')
                    if not label:
                        continue
                        
                    # Find the title span within the flex container
                    flex_container = label.find('div', class_='flex')
                    if not flex_container:
                        continue
                        
                    title_span = flex_container.find('span')
                    title = title_span.text.strip() if title_span else None
                    
                    # Find the collapser div which contains the apply link
                    collapser = collapsible.find('div', class_='collapser')
                    if not collapser:
                        continue
                        
                    # Find the apply link
                    apply_link_elem = collapser.find('a', href=True)
                    apply_link = urljoin(base_url, apply_link_elem['href']) if apply_link_elem else None
                    
                    if title and apply_link:
                        job_listings.append({
                            'company': 'Azercosmos',
                            'vacancy': title,
                            'apply_link': apply_link
                        })
                except Exception as e:
                    logger.warning(f"Error parsing job listing: {str(e)}")
                    continue
            
            logger.info(f"Successfully scraped {len(job_listings)} jobs from Azercosmos")
            return pd.DataFrame(job_listings)
        
        except Exception as e:
            logger.error(f"Error scraping Azercosmos: {str(e)}")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])