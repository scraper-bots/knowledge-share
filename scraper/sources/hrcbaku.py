import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class HrcbakuScraper(BaseScraper):
    """
    HRC Baku job scraper
    """
    
    @scraper_error_handler
    async def scrape_hrcbaku(self, session):
        url = "https://hrcbaku.com/jobs-1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                logger.error(f"Failed to retrieve the page. Status code: {response.status}")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

            soup = BeautifulSoup(await response.text(), "html.parser")
            
            jobs = []
            job_containers = soup.find_all("div", class_="tn-elem")

            for job_container in job_containers:
                title_elem = job_container.find("a", href=True)
                if title_elem and "vacancy" in title_elem['href']:
                    title = title_elem.get_text(strip=True)
                    apply_link = "https://hrcbaku.com" + title_elem['href']
                    description = title_elem.get_text(strip=True)
                    location = "Baku, Azerbaijan"

                    # Finding the company and any adjacent information if available
                    company = "Not specified"
                    company_elem = job_container.find_previous_sibling("div", class_="tn-elem")
                    if company_elem:
                        company_text = company_elem.get_text(strip=True)
                        if company_text and "Apply" not in company_text:
                            company = company_text

                    if "Apply" not in title:
                        jobs.append({
                            "company": company,
                            "vacancy": title,
                            "apply_link": apply_link
                        })
            
            return pd.DataFrame(jobs)