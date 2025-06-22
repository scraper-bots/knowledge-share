import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class EkaryeraScraper(BaseScraper):
    """
    Ekaryera.az job scraper for job listings
    """
    
    @scraper_error_handler
    async def scrape_ekaryera(self, session):
        """
        Scrape job listings from ekaryera.az across multiple pages
        """
        page_limit = 5
        base_url = "https://www.ekaryera.az/vakansiyalar?page="
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        job_data = []

        for page in range(1, page_limit + 1):
            url = base_url + str(page)
            response = await self.fetch_url_async(url, session, headers=headers, verify_ssl=False)

            if not response:
                logger.error(f"Failed to fetch page {page} from ekaryera.az")
                continue

            soup = BeautifulSoup(response, 'html.parser')
            job_list = soup.find('div', {'class': 'job-listings-sec'}).find_all('div', {'class': 'job-listing'})

            for job in job_list:
                job_title = job.find('h3').find('a').text.strip()
                company = job.find('span', text=True).text.strip() if job.find('span', text=True) else 'CompanyName'
                location = job.find('div', {'class': 'job-lctn'}).text.strip()
                employment_type = job.find('span', {'class': 'job-is'}).text.strip()
                experience = job.find('i').text.strip()
                apply_link = job.find('a')['href']

                job_data.append({
                    'company': company,
                    'vacancy': job_title,
                    'apply_link': apply_link
                })
            logger.info(f"Scraped page {page} for ekaryera.az")

        df = pd.DataFrame(job_data)
        logger.info("Scraping completed for ekaryera.az")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])