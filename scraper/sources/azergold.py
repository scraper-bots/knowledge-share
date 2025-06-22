import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class AzergoldScraper(BaseScraper):
    """
    AzerGold job scraper
    """
    
    @scraper_error_handler
    async def parse_azergold(self, session):
        logger.info("Started scraping AzerGold")
        url = "https://careers.azergold.az/"
        response = await self.fetch_url_async(url, session, verify_ssl=False)  # Handling SSL issues with verify_ssl=False

        if response:
            soup = BeautifulSoup(response, "html.parser")
            logger.info("Page fetched successfully")

            # Locate the table containing the job listings
            table = soup.find("table", class_="table-vacancy")
            if table:
                logger.info("Vacancies section found")
                job_rows = table.find("tbody").find_all("tr")

                job_titles = []
                job_links = []

                for row in job_rows:
                    title_cell = row.find("td")
                    if title_cell:
                        title_link = title_cell.find("a")
                        if title_link:
                            job_titles.append(title_link.text.strip())
                            job_links.append(title_link["href"])

                df = pd.DataFrame({'company': 'AzerGold', "vacancy": job_titles, "apply_link": job_links})
                logger.info("Scraping completed for AzerGold")
                return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            else:
                logger.warning("Vacancies section not found on the AzerGold page.")
        else:
            logger.error("Failed to fetch the AzerGold page.")

        return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])