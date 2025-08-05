import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class JobboxAzScraper(BaseScraper):
    """
    Jobbox.az job scraper
    """
    
    @scraper_error_handler
    async def parse_jobbox_az(self, session):
        # Domain appears to be permanently down - skip scraper
        logger.warning("jobbox.az domain is no longer accessible (DNS not found), skipping scraper")
        return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            
        start_page = 1
        end_page = 5
        logger.info(f"Scraping started for jobbox.az from page {start_page} to page {end_page}")
        job_vacancies = []
        
        for page_num in range(start_page, end_page + 1):
            logger.info(f"Scraping page {page_num}")
            url = f'https://jobbox.az/az/vacancies?page={page_num}'
            response = await self.fetch_url_async(url, session)

            if response:
                soup = BeautifulSoup(response, 'html.parser')
                job_items = soup.find_all('li', class_='item')

                for item in job_items:
                    job = {}

                    link_tag = item.find('a')
                    if link_tag:
                        job['apply_link'] = link_tag['href']
                    else:
                        continue  # Skip if no link found

                    title_ul = item.find('ul', class_='title')
                    if title_ul:
                        title_div = title_ul.find_all('li')
                        job['vacancy'] = title_div[0].text.strip() if len(title_div) > 0 else None
                    else:
                        continue  # Skip if title information is missing

                    address_ul = item.find('ul', class_='address')
                    if address_ul:
                        address_div = address_ul.find_all('li')
                        job['company'] = address_div[0].text.strip() if len(address_div) > 0 else None
                    else:
                        continue  # Skip if address information is missing

                    job_vacancies.append(job)
            else:
                logger.error(f"Failed to retrieve page {page_num}.")

        df = pd.DataFrame(job_vacancies, columns=['company', 'vacancy', 'apply_link'])
        logger.info("Scraping completed for jobbox.az")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])