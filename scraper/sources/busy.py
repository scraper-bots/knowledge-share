import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class BusyScraper(BaseScraper):
    """
    Busy.az job scraper for job listings
    """
    
    @scraper_error_handler
    async def parse_busy_az(self, session):
        """
        Scrape job listings from Busy.az across multiple pages
        """
        logger.info("Scraping started for busy.az")
        job_vacancies = []
        for page_num in range(1, 7):
            logger.info(f"Scraping page {page_num}")
            url = f'https://busy.az/vacancies?page={page_num}'
            response = await self.fetch_url_async(url, session)

            if response:
                soup = BeautifulSoup(response, 'html.parser')
                job_listings = soup.find_all('a', class_='job-listing')

                for job in job_listings:
                    job_details = job.find('div', class_='job-listing-details')
                    job_title = job_details.find('h3', class_='job-listing-title').text.strip()
                    company_element = job_details.find('i', class_='icon-material-outline-business')
                    company_name = company_element.find_parent('li').text.strip() if company_element else 'N/A'
                    apply_link = job.get('href')
                    job_vacancies.append({"company": company_name, "vacancy": job_title, "apply_link": apply_link})
            else:
                logger.error(f"Failed to retrieve page {page_num}.")
        df = pd.DataFrame(job_vacancies)
        logger.info("Scraping completed for busy.az")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])