import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class OilfundJobsScraper(BaseScraper):
    """
    Azerbaijan State Oil Fund job scraper
    """
    
    @scraper_error_handler
    async def scrape_oilfund_jobs(self, session):
        url = 'https://oilfund.az/fund/career-opportunities/vacancy'
        async with session.get(url, verify_ssl=False) as response:
            if response.status == 200:
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                job_listings = []
                
                job_cards = soup.find_all('div', class_='oil-q-box')
                
                for job in job_cards:
                    title_tag = job.find('a', class_='font-gotham-book')
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        apply_link = title_tag['href']
                        job_listings.append({
                            'company':'Azərbaycan Respublikasının Dövlət Neft Fondu',
                            'vacancy': title,
                            'apply_link': apply_link
                        })
                
                df = pd.DataFrame(job_listings)
                return df
            else:
                logger.error(f"Failed to retrieve the webpage. Status code: {response.status}")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])