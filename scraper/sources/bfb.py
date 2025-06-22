import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class BfbScraper(BaseScraper):
    """
    Baku Stock Exchange (BFB) job scraper
    """
    
    @scraper_error_handler
    async def scrape_bfb(self, session):
        url = "https://www.bfb.az/en/careers"
        async with session.get(url) as response:
            soup = BeautifulSoup(await response.text(), "html.parser")

            titles = []
            job_listings = soup.select("ul.page-list > li")

            for listing in job_listings:
                title_tag = listing.find("h3", class_="accordion-title")
                title = title_tag.get_text(strip=True) if title_tag else "N/A"
                titles.append(title)

            return pd.DataFrame({
                'company': 'Baku Stock Exchange',
                "vacancy": titles,
                "apply_link" : 'https://www.bfb.az/en/careers',
            })