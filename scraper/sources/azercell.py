import asyncio
import logging
import pandas as pd
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class AzercellScraper(BaseScraper):
    """
    Azercell job scraper for career page
    """
    
    @scraper_error_handler
    async def parse_azercell(self, session):
        """
        Scrape job listings from Azercell career page
        """
        logger.info("Started scraping Azercell")
        url = "https://www.azercell.com/az/about-us/career.html"
        response_text = await self.fetch_url_async(url, session)
        if not response_text:
            logger.warning("Failed to retrieve Azercell page.")
            return pd.DataFrame()

        soup = BeautifulSoup(response_text, "html.parser")
        vacancies_section = soup.find("section", class_="section_vacancies")
        if not vacancies_section:
            logger.warning("Vacancies section not found on Azercell page.")
            return pd.DataFrame()

        job_listings = vacancies_section.find_all("a", class_="vacancies__link")
        tasks = [self.fetch_url_async(urljoin(url, link["href"]), session) for link in job_listings]
        job_pages = await asyncio.gather(*tasks)

        jobs_data = []
        for i, job_page in enumerate(job_pages):
            if job_page:
                job_soup = BeautifulSoup(job_page, "html.parser")
                jobs_data.append({
                    'company': 'azercell',
                    "vacancy": job_listings[i].find("h4", class_="vacancies__name").text,
                    "location": job_listings[i].find("span", class_="vacancies__location").text.strip(),
                    "apply_link": job_listings[i]["href"],
                    "function": job_soup.find("span", class_="function").text if job_soup.find("span", class_="function") else None,
                    "schedule": job_soup.find("span", class_="schedule").text if job_soup.find("span", class_="schedule") else None,
                    "deadline": job_soup.find("span", class_="deadline").text if job_soup.find("span", class_="deadline") else None,
                    "responsibilities": job_soup.find("div", class_="responsibilities").text.strip() if job_soup.find("div", class_="responsibilities") else None,
                    "requirements": job_soup.find("div", class_="requirements").text.strip() if job_soup.find("div", class_="requirements") else None
                })

        logger.info("Completed scraping Azercell")
        return pd.DataFrame(jobs_data)