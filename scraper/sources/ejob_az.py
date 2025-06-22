import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class EjobAzScraper(BaseScraper):
    """
    Ejob.az job scraper
    """
    
    @scraper_error_handler
    async def parse_ejob_az(self, session):
        start_page = 1
        end_page = 20
        logger.info("Scraping started for ejob.az")
        base_url = "https://ejob.az/is-elanlari"
        all_jobs = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        for page in range(start_page, end_page + 1):
            url = f"{base_url}/page-{page}/"
            try:
                response = await self.fetch_url_async(url, session, headers=headers, verify_ssl=False)
                if response:
                    soup = BeautifulSoup(response, 'html.parser')
                    job_tables = soup.find_all('table', class_='background')
                    for job in job_tables:
                        title_link = job.find('a', href=True)
                        company = job.find('div', class_='company')
                        if title_link and company:
                            all_jobs.append({
                                'company': company.text.strip(),
                                'vacancy': title_link.text.strip(),
                                'apply_link': f"https://ejob.az{title_link['href']}"
                            })
                else:
                    logger.warning(f"Failed to retrieve page {page}.")
            except Exception as e:
                logger.error(f"Error on page {page}: {e}")
                continue

        logger.info("Scraping completed for ejob.az")
        return pd.DataFrame(all_jobs) if all_jobs else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])