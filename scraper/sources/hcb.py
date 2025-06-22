import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class HcbScraper(BaseScraper):
    """
    HCB (Human Capital Bureau) job scraper
    """
    
    @scraper_error_handler
    async def scrape_hcb(self, session):
        url = 'https://hcb.az/'
        async with session.get(url) as response:
            response.raise_for_status()
            soup = BeautifulSoup(await response.text(), 'html.parser')
            
            jobs = []
            table_rows = soup.select('.table-bg table tbody tr')
            for row in table_rows:
                columns = row.find_all('td')
                if len(columns) >= 6:
                    apply_link = columns[0].find('a')['href']
                    vacancy = columns[2].get_text(strip=True)
                    company = columns[3].get_text(strip=True)

                    jobs.append({
                        'company': company,
                        'vacancy': vacancy,
                        'apply_link': apply_link
                    })

            return pd.DataFrame(jobs)