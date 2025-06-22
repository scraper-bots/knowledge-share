import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class AdaScraper(BaseScraper):
    """
    ADA University job scraper
    """
    
    @scraper_error_handler
    async def parse_ada(self, session):
        logger.info("Started scraping ADA University")

        url = "https://ada.edu.az/jobs"
        response = await self.fetch_url_async(url, session, verify_ssl=False)  # SSL disabled for this connection

        if response:
            soup = BeautifulSoup(response, 'html.parser')

            # Find the table containing the job listings
            table = soup.find('table', class_='table-job')
            jobs = []

            if table:
                # Loop through each row in the table body
                for row in table.find('tbody').find_all('tr'):
                    title_tag = row.find('td', class_='name').find('a')
                    view_link_tag = row.find('td', class_='view').find('a')

                    # Safely get the title and apply link
                    title = title_tag.text.strip() if title_tag else "N/A"
                    apply_link = view_link_tag['href'] if view_link_tag else "N/A"

                    job = {
                        'company': 'ADA University',
                        'vacancy': title,
                        'apply_link': apply_link
                    }
                    jobs.append(job)

                df = pd.DataFrame(jobs)
                logger.info("Scraping completed for ADA University")
                logger.info(f"Scraped jobs: {len(jobs)}")
                return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            else:
                logger.warning("No job listings found on the ADA University page.")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
        else:
            logger.error("Failed to fetch the page.")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])