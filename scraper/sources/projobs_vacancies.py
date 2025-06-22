import logging
import pandas as pd
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class ProjobsVacanciesScraper(BaseScraper):
    """
    Projobs vacancies scraper
    """
    
    @scraper_error_handler
    async def parse_projobs_vacancies(self, session):
        """Fetch and parse job vacancies from Projobs API."""
        data = []
        base_url = "https://core.projobs.az/v1/vacancies"
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6',
            'Connection': 'keep-alive',
            'Dnt': '1',
            'Host': 'core.projobs.az',
            'Origin': 'https://projobs.az',
            'Referer': 'https://projobs.az/',
            'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        }
        max_pages = 10
        for page in range(1, max_pages + 1):
            url = f"{base_url}?page={page}"
            try:
                response = await self.fetch_url_async(url, session, headers=headers)
                if response:
                    vacancies = response.get("data", [])
                    for vacancy in vacancies:
                        vacancy_info = {
                            "company": vacancy["companyName"],
                            "vacancy": vacancy["name"],
                            "apply_link": f"https://projobs.az/jobdetails/{vacancy['id']}"
                        }
                        data.append(vacancy_info)
                    logger.info(f"Scraped page {page} successfully.")
                else:
                    logger.error(f"Failed to retrieve data from {url}")
                    continue
            except Exception as e:
                logger.error(f"Request to {url} failed: {e}")
                continue

        if data:
            df = pd.DataFrame(data)
            logger.info("Scraping completed for Projobs")
            return df if not df.empty else pd.DataFrame(columns=["company", "vacancy", "apply_link"])
        else:
            logger.warning("No vacancies found in the API response.")
            return pd.DataFrame(columns=["company", "vacancy", "apply_link"])