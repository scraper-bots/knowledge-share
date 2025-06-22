import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class BossAzScraper(BaseScraper):
    """
    Boss.az job scraper
    """
    
    @scraper_error_handler
    async def parse_boss_az(self, session):
        logger.info("Starting to scrape Boss.az...")
        job_vacancies = []
        base_url = "https://boss.az"
        
        for page_num in range(1, 10):
            url = f"{base_url}/vacancies?page={page_num}"
            response = await self.fetch_url_async(url, session)
            if response:
                soup = BeautifulSoup(response, 'html.parser')
                job_listings = soup.find_all('div', class_='results-i')
                for job in job_listings:
                    title = job.find('h3', class_='results-i-title').get_text(strip=True)
                    company = job.find('a', class_='results-i-company').get_text(strip=True)
                    link = f"{base_url}{job.find('a', class_='results-i-link')['href']}"
                    job_vacancies.append({"company": company, "vacancy": title, "apply_link": link})
                logger.info(f"Scraped {len(job_listings)} jobs from page {page_num}")
            else:
                logger.warning(f"Failed to retrieve page {page_num}.")
        
        logger.info("Scraping completed for Boss.az")
        return pd.DataFrame(job_vacancies) if job_vacancies else pd.DataFrame(
            columns=['company', 'vacancy', 'apply_link'])