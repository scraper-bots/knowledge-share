import logging
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class ZiraatScraper(BaseScraper):
    """
    Ziraat Bank job scraper
    """
    
    @scraper_error_handler
    async def scrape_ziraat(self, session):
        base_url = 'https://ziraatbank.az'
        url = 'https://ziraatbank.az/az/vacancies2'
        
        response = await self.fetch_url_async(url, session)
        if not response:
            logger.error(f"Failed to fetch the page for Ziraat Bank.")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

        soup = BeautifulSoup(response, 'html.parser')
        jobs = []

        # Find all job listings
        job_cards = soup.find_all('div', class_='landing-item-box')

        for card in job_cards:
            title_tag = card.find('h2')
            title = title_tag.get_text(strip=True) if title_tag else 'N/A'
            
            # Find apply link
            link_tag = card.find('a', href=True)
            apply_link = urljoin(base_url, link_tag['href']) if link_tag else base_url

            jobs.append({
                'company': 'Ziraat Bank',
                'vacancy': title,
                'apply_link': apply_link
            })

        logger.info("Scraping completed for Ziraat Bank")
        return pd.DataFrame(jobs) if jobs else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])