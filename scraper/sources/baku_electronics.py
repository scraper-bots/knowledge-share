import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class BakuElectronicsScraper(BaseScraper):
    """
    Baku Electronics job scraper
    """
    
    @scraper_error_handler
    async def parse_baku_electronics(self, session):
        logger.info("Started scraping Baku Electronics")
        base_url = "https://careers.bakuelectronics.az/az/vacancies/?p="
        all_job_titles = []
        all_job_categories = []
        all_job_locations = []
        all_job_deadlines = []
        all_job_links = []

        for page in range(1, 3):
            url = f"{base_url}{page}"
            response = await self.fetch_url_async(url, session, verify_ssl=False)
            if response:
                soup = BeautifulSoup(response, "html.parser")
                logger.info(f"Page {page} fetched successfully")

                # Locate the blocks containing the job listings
                vacancy_blocks = soup.find_all("div", class_="vacancy-list-block")
                if vacancy_blocks:
                    logger.info("Vacancies section found")
                    for block in vacancy_blocks:
                        header = block.find("div", class_="vacancy-list-block-header")
                        info = block.find("div", class_="vacancy-list-block-info")
                        deadline = block.find("div", class_="vacancy-list-block-note")
                        link_tag = block.find_parent("a", href=True)
                        link = link_tag["href"] if link_tag else None

                        job_title = header.text.strip() if header else None
                        category_location = info.find_all("label") if info else []
                        job_category = category_location[0].text.strip() if len(category_location) > 0 else None
                        job_location = category_location[1].text.strip() if len(category_location) > 1 else None
                        job_deadline = deadline.text.strip() if deadline else None
                        job_link = "https://careers.bakuelectronics.az" + link if link else None

                        if None in [job_title, job_category, job_location, job_deadline, job_link]:
                            logger.warning(f"Missing elements in block: title={job_title}, category={job_category}, location={job_location}, deadline={job_deadline}, link={job_link}")
                            continue

                        all_job_titles.append(job_title)
                        all_job_categories.append(job_category)
                        all_job_locations.append(job_location)
                        all_job_deadlines.append(job_deadline)
                        all_job_links.append(job_link)
                else:
                    logger.warning(f"Vacancies section not found on page {page}.")
            else:
                logger.warning(f"Failed to fetch page {page}.")

        df = pd.DataFrame({
            'company': 'Baku Electronics',
            'vacancy': all_job_titles,
            'apply_link': all_job_links
        })
        logger.info("Scraping completed for Baku Electronics")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])