import logging
import pandas as pd
import re
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class CbarScraper(BaseScraper):
    """
    CBAR job scraper
    """
    
    @scraper_error_handler
    async def parse_cbar(self, session):
        logger.info("Started scraping CBAR")
        url = "https://www.cbar.az/hr/f?p=100:106"
        response = await self.fetch_url_async(url, session, verify_ssl=False)
        if response:
            soup = BeautifulSoup(response, "html.parser")
            logger.info("Page fetched successfully")

            all_job_numbers = []
            all_job_titles = []
            all_job_start_dates = []
            all_job_end_dates = []
            all_job_links = []

            # Locate the blocks containing the job listings
            table = soup.find("table", class_="a-IRR-table")
            if table:
                rows = table.find_all("tr")[1:]  # Skip header row
                for row in rows:
                    cols = row.find_all("td")
                    job_number = cols[0].text.strip() if cols[0] else None
                    job_title = cols[1].text.strip() if cols[1] else None
                    job_start_date = cols[2].text.strip() if cols[2] else None
                    job_end_date = cols[3].text.strip() if cols[3] else None
                    job_link_tag = cols[1].find("a", href=True)
                    job_link = job_link_tag["href"] if job_link_tag else None

                    if job_link and 'javascript:' in job_link:
                        match = re.search(r"P50_VACANCY_ID,P50_POSITION_ID:([^,]+),([^&]+)", job_link)
                        if match:
                            job_vacancy_id = match.group(1)
                            job_position_id = match.group(2)
                            job_link = f"https://www.cbar.az/hr/f?p=100:50::::50:P50_VACANCY_ID,P50_POSITION_ID:{job_vacancy_id},{job_position_id}"

                    if None in [job_number, job_title, job_start_date, job_end_date, job_link]:
                        logger.warning(f"Missing elements in row: number={job_number}, title={job_title}, start_date={job_start_date}, end_date={job_end_date}, link={job_link}")
                        continue

                    all_job_numbers.append(job_number)
                    all_job_titles.append(job_title)
                    all_job_start_dates.append(job_start_date)
                    all_job_end_dates.append(job_end_date)
                    all_job_links.append(job_link)
            else:
                logger.warning("Job listings table not found on the page.")

            df = pd.DataFrame({
                'company': 'CBAR',
                'vacancy': all_job_titles,
                'apply_link': 'https://www.cbar.az/hr/f?p=100:106'
            })
            logger.info("Scraping completed for CBAR")
            return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
        else:
            logger.error("Failed to fetch the page.")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])