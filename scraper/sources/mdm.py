import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class MdmScraper(BaseScraper):
    """
    Milli Depozit Mərkəzi job scraper
    """
    
    @scraper_error_handler
    async def scrape_mdm(self, session):
        base_url = "https://www.mdm.gov.az/karyera"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        job_data = []
        response = await self.fetch_url_async(base_url, session, headers=headers, verify_ssl=False)
        if not response:
            logger.error("Failed to fetch the Milli Depozit Mərkəzi careers page.")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

        soup = BeautifulSoup(response, 'html.parser')
        content = soup.find('div', {'class': 'content'})
        paragraphs = content.find_all('p')

        job_title = None
        job_description = ""

        for p in paragraphs:
            text = p.get_text().strip()
            if text.startswith("Vəzifə :") or text.startswith("Vəzifə:"):
                if job_title:
                    job_data.append({
                        'company': 'Milli Depozit Mərkəzi',
                        'vacancy': job_title.strip(),
                        'apply_link': base_url
                    })
                job_title = text.replace("Vəzifə :", "").replace("Vəzifə:", "").strip()
                job_description = ""
            elif text.startswith("Əsas tələblər:") or text.startswith("Vəzifə və öhdəliklər:"):
                job_description += " " + text
            else:
                job_description += " " + text

        if job_title:
            job_data.append({
                'company': 'Milli Depozit Mərkəzi',
                'vacancy': job_title.strip(),
                'apply_link': base_url
            })

        df = pd.DataFrame(job_data)
        logger.info("Scraping completed for Milli Depozit Mərkəzi")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])