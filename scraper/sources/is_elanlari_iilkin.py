import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class IsElanlariIilkinScraper(BaseScraper):
    """
    Is-elanlari.iilkin.com job scraper
    """
    
    @scraper_error_handler
    async def parse_is_elanlari_iilkin(self, session):
        logger.info("Started scraping is-elanlari.iilkin.com")
        base_url = 'http://is-elanlari.iilkin.com/vakansiyalar/'
        job_listings = []

        async def scrape_page(content):
            soup = BeautifulSoup(content, 'html.parser')
            main_content = soup.find('main', id='main', class_='site-main')
            if main_content:
                articles = main_content.find_all('article')
                for job in articles:
                    title_element = job.find('a', class_='home-title-links')
                    company_element = job.find('p', class_='vacan-company-name')
                    link_element = job.find('a', class_='home-title-links')

                    job_listings.append({
                        "vacancy": title_element.text.strip().lower() if title_element else 'n/a',
                        "company": company_element.text.strip().lower() if company_element else 'n/a',
                        "apply_link": link_element['href'] if link_element else 'n/a'
                    })
            else:
                logger.warning("Main content not found")

        for page_num in range(1, 4):
            url = base_url if page_num == 1 else f'{base_url}{page_num}'
            logger.info(f'Scraping page {page_num}...')
            response = await self.fetch_url_async(url, session)
            if response:
                await scrape_page(response)
            else:
                logger.warning(f"Failed to retrieve page {page_num} for is-elanlari.iilkin.com")

        if job_listings:
            df = pd.DataFrame(job_listings)
            logger.info("Scraping completed for is-elanlari.iilkin.com")
            return df
        else:
            logger.warning("No job listings found")
            return pd.DataFrame(columns=['vacancy', 'company', 'apply_link'])