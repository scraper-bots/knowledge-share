import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class BravosupermarketScraper(BaseScraper):
    """
    Bravo Supermarket job scraper
    """
    
    @scraper_error_handler
    async def scrape_bravosupermarket(self, session):
        base_url = "https://www.bravosupermarket.az/career/all-vacancies/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        job_data = []

        response = await self.fetch_url_async(base_url, session, headers=headers, verify_ssl=True)
        if not response:
            logger.error("Failed to fetch the Bravo Supermarket careers page.")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

        soup = BeautifulSoup(response, 'html.parser')
        job_list = soup.find('div', {'class': 'vacancies_grid'}).find_all('article')

        for job in job_list:
            job_title = job.find('h3').text.strip()
            location = job.find('footer').find('p').text.strip()
            apply_link = "https://www.bravosupermarket.az" + job.find('a')['href']

            job_data.append({
                'company': 'Azerbaijan Supermarket',
                'vacancy': job_title,
                'apply_link': apply_link
            })

        df = pd.DataFrame(job_data)
        logger.info("Scraping completed for Bravo Supermarket")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])