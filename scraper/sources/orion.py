import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class OrionScraper(BaseScraper):
    """
    Orion Jobs scraper
    """
    
    @scraper_error_handler
    async def scrape_orion(self, session):
        async def get_orion_jobs(page):
            url = f"https://www.orionjobs.com/jobs/azerbaijan-office?page={page}"
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to retrieve page {page}")
                    return []

                soup = BeautifulSoup(await response.text(), "html.parser")
                job_list = []

                for job in soup.select("ul.results-list li.job-result-item"):
                    title = job.select_one(".job-title a").get_text(strip=True)
                    apply_url = job.select_one(".job-apply-now-link a")["href"]

                    job_list.append({
                        "company": "Unknown",
                        "vacancy": title,
                        "apply_link": f"https://www.orionjobs.com{apply_url}"
                    })

                return job_list

        all_jobs = []
        for page in range(1, 6):  # Scrape pages 1 to 5
            jobs = await get_orion_jobs(page)
            if jobs:
                all_jobs.extend(jobs)
            else:
                logger.info(f"No jobs found on page {page}")

        if all_jobs:
            return pd.DataFrame(all_jobs)
        else:
            logger.info("No jobs data to save")
            return pd.DataFrame()