import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class AscoScraper(BaseScraper):
    """
    ASCO job scraper
    """
    
    @scraper_error_handler
    async def parse_asco(self, session):
        logger.info("Started scraping ASCO")
        base_url = "https://www.asco.az/az/pages/6/65?page="
        all_job_numbers = []
        all_job_titles = []
        all_job_deadlines = []
        all_job_links = []

        for page in range(1, 4):
            url = f"{base_url}{page}"
            response = await self.fetch_url_async(url, session, verify_ssl=False)
            if response:
                soup = BeautifulSoup(response, "html.parser")
                logger.info(f"Page {page} fetched successfully")

                # Locate the blocks containing the job listings
                table = soup.find("table", class_="default")
                if table:
                    rows = table.find_all("tr")[1:]  # Skip header row
                    for row in rows:
                        cols = row.find_all("td")
                        job_number = cols[0].text.strip() if cols[0] else None
                        job_title = cols[1].text.strip() if cols[1] else None
                        job_deadline = cols[2].text.strip() if cols[2] else None
                        job_link_tag = cols[3].find("a", href=True)
                        job_link = job_link_tag["href"] if job_link_tag else None

                        if None in [job_number, job_title, job_deadline, job_link]:
                            logger.warning(f"Missing elements in row: number={job_number}, title={job_title}, deadline={job_deadline}, link={job_link}")
                            continue

                        all_job_numbers.append(job_number)
                        all_job_titles.append(job_title)
                        all_job_deadlines.append(job_deadline)
                        all_job_links.append(job_link)
                else:
                    logger.warning(f"Job listings table not found on page {page}.")
            else:
                logger.warning(f"Failed to fetch page {page}.")

        df = pd.DataFrame({
            'company': 'ASCO',
            'vacancy': all_job_titles,
            'apply_link': all_job_links
        })
        logger.info("Scraping completed for ASCO")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])