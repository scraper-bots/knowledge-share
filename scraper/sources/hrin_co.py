import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class HrinCoScraper(BaseScraper):
    """
    Hrin.co job scraper
    """
    
    @scraper_error_handler
    async def scrape_hrin_co(self, session):
        base_url = 'https://hrin.co/?page={}'
        job_listings = []

        for page in range(1, 6):  # Scraping pages 1 to 5
            url = base_url.format(page)
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    job_cards = soup.find_all('div', class_='vacancy-list-item')
                    
                    for job in job_cards:
                        company_tag = job.find('a', class_='company')
                        vacancy_tag = job.find('a', class_='title')
                        
                        company = company_tag.get_text(strip=True) if company_tag else 'N/A'
                        vacancy = vacancy_tag.get_text(strip=True) if vacancy_tag else 'N/A'
                        apply_link = vacancy_tag['href'] if vacancy_tag else 'N/A'
                        
                        job_listings.append({
                            'company': company,
                            'vacancy': vacancy,
                            'apply_link': apply_link
                        })
                else:
                    logger.error(f"Failed to retrieve the webpage for page {page}. Status code: {response.status}")

        df = pd.DataFrame(job_listings)
        return df