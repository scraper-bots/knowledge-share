import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class ItsGovScraper(BaseScraper):
    """
    Its.gov.az job scraper
    """
    
    @scraper_error_handler
    async def parse_its_gov(self, session):
        start_page = 1
        end_page = 20
        logger.info(f"Scraping its.gov.az from page {start_page} to page {end_page}")
        base_url = "https://its.gov.az/page/vakansiyalar?page="
        all_vacancies = []

        for page in range(start_page, end_page + 1):
            url = f"{base_url}{page}"
            logger.info(f"Fetching page {page}")
            response = await self.fetch_url_async(url, session)
            
            if response:
                soup = BeautifulSoup(response, "html.parser")
                events = soup.find_all('div', class_='event')
                if not events:
                    logger.info(f"No job listings found on page {page}")
                    break

                for event in events:
                    title_tag = event.find('a', class_='event__link')
                    if title_tag:
                        title = title_tag.get_text(strip=True).lower()
                        link = title_tag['href']
                        deadline_tag = event.find('span', class_='event__time')
                        deadline = deadline_tag.get_text(strip=True) if deadline_tag else 'N/A'
                        all_vacancies.append({
                            'company': 'icbari tibbi sigorta',  # Normalized company name
                            'vacancy': title,
                            'apply_link': link
                        })
            else:
                logger.warning(f"Failed to retrieve page {page}")

        logger.info("Scraping completed for its.gov.az")
        return pd.DataFrame(all_vacancies) if all_vacancies else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])