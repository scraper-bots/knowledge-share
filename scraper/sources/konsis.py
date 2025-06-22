import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class KonsisScraper(BaseScraper):
    """
    Konsis job scraper
    """
    
    @scraper_error_handler
    async def parse_konsis(self, session):
        logger.info("Started scraping Konsis")
        url = "https://konsis.az/karyera-vakansiya/"
        response = await self.fetch_url_async(url, session, verify_ssl=False)  # Handling SSL issues with verify_ssl=False

        if response:
            soup = BeautifulSoup(response, "html.parser")
            logger.info("Page fetched successfully")

            # Locate the articles containing the job listings
            articles = soup.find_all("div", class_="grid-item")
            if articles:
                logger.info("Vacancies section found")
                job_titles = []
                job_companies = []
                job_locations = []
                job_types = []
                job_descriptions = []
                job_links = []

                for article in articles:
                    meta = article.find("div", class_="item--meta")
                    if meta:
                        job_title = meta.find("h3", class_="item--title").text.strip()
                        features = meta.find_all("li")
                        job_company = features[0].text.strip() if len(features) > 0 else "N/A"
                        job_location = features[1].text.strip() if len(features) > 1 else "N/A"
                        job_type = features[2].text.strip() if len(features) > 2 else "N/A"
                        job_description = article.find("div", class_="item-desc").text.strip()
                        job_link = article.find("a", class_="btn btn-secondary", href=True)["href"]

                        job_titles.append(job_title)
                        job_companies.append(job_company)
                        job_locations.append(job_location)
                        job_types.append(job_type)
                        job_descriptions.append(job_description)
                        job_links.append("https://konsis.az" + job_link)

                df = pd.DataFrame({
                    'company': job_companies,
                    'vacancy': job_titles,
                    'apply_link': job_links
                })
                logger.info("Scraping completed for Konsis")
                return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            else:
                logger.warning("Vacancies section not found on the Konsis page.")
        else:
            logger.error("Failed to fetch the Konsis page.")

        return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])