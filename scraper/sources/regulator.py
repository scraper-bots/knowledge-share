import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class RegulatorScraper(BaseScraper):
    """
    Azerbaijan Energy Regulatory Agency job scraper
    """
    
    @scraper_error_handler
    async def scrape_regulator(self, session):
        """
        Scrape job listings from regulator.gov.az
        """
        url = "https://regulator.gov.az/az/vakansiyalar/vakansiyalar_611"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = await self.fetch_url_async(url, session, headers=headers, verify_ssl=False)

        if not response:
            logger.error("Failed to fetch data from regulator.gov.az")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

        soup = BeautifulSoup(response, 'html.parser')
        table = soup.find('table', {'border': '1'})

        if not table:
            logger.warning("No table found on the regulator.gov.az page.")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

        rows = table.find_all('tr')[1:]  # Skip the header row
        job_data = []

        for row in rows:
            cols = row.find_all('td')
            title_tag = cols[0].find('a')
            title = title_tag.text.strip() if title_tag else 'N/A'
            location = cols[1].text.strip() if len(cols) > 1 else 'N/A'
            field = cols[2].text.strip() if len(cols) > 2 else 'N/A'
            deadline = cols[3].text.strip() if len(cols) > 3 else 'N/A'
            apply_link = title_tag['href'] if title_tag else 'N/A'

            job_data.append({
                'company': 'Azerbaijan Energy Regulatory Agency',
                'vacancy': title,
                'apply_link': apply_link
            })

        df = pd.DataFrame(job_data)
        logger.info("Scraping completed for regulator.gov.az")
        return df