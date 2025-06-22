import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class ArtiScraper(BaseScraper):
    """
    ARTI job scraper
    """
    
    @scraper_error_handler
    async def scrape_arti(self, session):
        logger.info("Scraping started for ARTI")
        base_url = "https://arti.edu.az/media/vakansiyalar"
        pages = 5
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        job_data = []

        for page in range(1, pages + 1):
            url = f"{base_url}/page/{page}/"
            response = await self.fetch_url_async(url, session, headers=headers)
            if not response:
                logger.error(f"Failed to fetch page {page} for ARTI.")
                continue

            soup = BeautifulSoup(response, 'html.parser')
            cards = soup.find_all('a', {'class': 'card card-bordered card-transition h-100'})

            for card in cards:
                job_title = card.find('h4', {'class': 'card-title'}).get_text(strip=True)
                job_link = card['href']
                job_description = card.find('p', {'class': 'card-text text-body'}).get_text(strip=True)
                job_data.append({
                    'company':'Azərbaycan Respublikasının Təhsil İnstitutu',
                    'vacancy': job_title,
                    'apply_link': job_link
                })

        logger.info("Scraping completed for ARTI")
        return pd.DataFrame(job_data) if job_data else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])