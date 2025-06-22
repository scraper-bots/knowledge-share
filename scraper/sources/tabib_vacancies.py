import logging
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class TabibVacanciesScraper(BaseScraper):
    """
    TABIB vacancies scraper
    """
    
    @scraper_error_handler
    async def parse_tabib_vacancies(self, session):
        logger.info("Started scraping TABIB vacancies")
        url = "https://tabib.gov.az/vetendashlar-ucun/vakansiyalar"  # Updated URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html'
        }
        
        try:
            response = await self.fetch_url_async(url, session, headers=headers)
            if response:
                soup = BeautifulSoup(response, 'html.parser')
                jobs = []
                
                # Find vacancy containers
                vacancy_items = soup.find_all('div', class_='vacancy-item')
                for item in vacancy_items:
                    title = item.find('h2', class_='vacancy-title')
                    link = item.find('a', class_='apply-link')
                    
                    if title and link:
                        jobs.append({
                            'company': 'TABIB',
                            'vacancy': title.text.strip(),
                            'apply_link': urljoin(url, link['href'])
                        })
                
                return pd.DataFrame(jobs)
        except Exception as e:
            logger.error(f"Error scraping TABIB: {e}")
        return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])