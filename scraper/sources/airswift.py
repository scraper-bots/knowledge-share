import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class AirswiftScraper(BaseScraper):
    """
    Airswift job scraper
    """
    
    @scraper_error_handler
    async def scrape_airswift(self, session):
        url = "https://www.airswift.com/jobs?search=&location=Baku&verticals_discipline=*&sector=*&employment_type=*&date_published=*"
        async with session.get(url) as response:
            soup = BeautifulSoup(await response.text(), "html.parser")

            titles = []
            apply_links = []

            job_cards = soup.select("div.jobs__card")

            for card in job_cards:
                title_tag = card.select_one("div.title")
                title = title_tag.get_text(strip=True) if title_tag else "N/A"
                titles.append(title)

                apply_link_tag = card.select_one("a.c-button.candidate-conversion-apply")
                apply_link = apply_link_tag["href"] if apply_link_tag else "N/A"
                apply_links.append(apply_link)

            return pd.DataFrame({
                'company': 'Unknown',
                'vacancy': titles,
                "apply_link": apply_links
            })