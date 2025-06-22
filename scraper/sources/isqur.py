import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class IsqurScraper(BaseScraper):
    """
    Isqur.com job scraper
    """
    
    @scraper_error_handler
    async def parse_isqur(self, session):
        start_page = 1
        end_page = 5
        logger.info("Started scraping isqur.com")
        job_vacancies = []
        base_url = "https://isqur.com/is-elanlari/sehife-"

        for page_num in range(start_page, end_page + 1):
            logger.info(f"Scraping page {page_num} for isqur.com")
            url = f"{base_url}{page_num}"
            response = await self.fetch_url_async(url, session)
            if response:
                soup = BeautifulSoup(response, 'html.parser')
                job_cards = soup.find_all('div', class_='kart')
                for job in job_cards:
                    title = job.find('div', class_='basliq').text.strip()
                    company = "Unknown"  # The provided HTML does not include a company name
                    link = "https://isqur.com/" + job.find('a')['href']
                    job_vacancies.append({'company': company, 'vacancy': title, 'apply_link': link})
            else:
                logger.error(f"Failed to retrieve page {page_num} for isqur.com")

        logger.info("Scraping completed for isqur.com")
        return pd.DataFrame(job_vacancies) if job_vacancies else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])