import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class DejobsScraper(BaseScraper):
    """
    Dejobs.org job scraper
    """
    
    @scraper_error_handler
    async def scrape_dejobs(self, session):
        url = "https://dejobs.org/aze/jobs/#1"
        async with session.get(url) as response:
            if response.status != 200:
                logger.error(f"Failed to fetch data. Status code: {response.status}")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

            soup = BeautifulSoup(await response.text(), 'html.parser')

            jobs = []
            job_listings = soup.find_all('li', class_='direct_joblisting')

            for job in job_listings:
                try:
                    vacancy = job.find('span', class_='resultHeader').text.strip()
                    apply_link = "https://dejobs.org" + job.find('a')['href'].strip()
                    company = job.find('b', class_='job-location-information').text.strip()

                    jobs.append({
                        'company': company,
                        'vacancy': vacancy,
                        'apply_link': apply_link
                    })
                except AttributeError as e:
                    logger.warning(f"Error parsing job: {e}")
                    continue

            return pd.DataFrame(jobs, columns=['company', 'vacancy', 'apply_link'])