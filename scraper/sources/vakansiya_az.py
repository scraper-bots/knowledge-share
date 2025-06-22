import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class VakansiyaAzScraper(BaseScraper):
    """
    Vakansiya.az job scraper
    """
    
    @scraper_error_handler
    async def parse_vakansiya_az(self, session):
        logger.info("Scraping started for vakansiya.az")
        url = 'https://www.vakansiya.az/az/'
        response = await self.fetch_url_async(url, session)
        
        if response:
            soup = BeautifulSoup(response, 'html.parser')
            jobs = []
            job_divs = soup.find_all('div', id='js-jobs-wrapper')

            for job_div in job_divs:
                company = job_div.find_all('div', class_='js-fields')[1].find('a')
                title = job_div.find('a', class_='jobtitle')
                apply_link = title['href'] if title else None

                jobs.append({
                    'company': company.get_text(strip=True) if company else 'N/A',
                    'vacancy': title.get_text(strip=True) if title else 'N/A',
                    'apply_link': f'https://www.vakansiya.az{apply_link}' if apply_link else 'N/A'
                })

            logger.info("Scraping completed for vakansiya.az")
            return pd.DataFrame(jobs) if jobs else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
        else:
            logger.error("Failed to retrieve the page.")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])