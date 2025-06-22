import logging
import pandas as pd
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class KapitalbankScraper(BaseScraper):
    """
    Kapital Bank job scraper
    """
    
    @scraper_error_handler
    async def parse_kapitalbank(self, session):
        logger.info("Fetching jobs from Kapital Bank API")
        url = "https://apihr.kapitalbank.az/api/Vacancy/vacancies?Skip=0&Take=150&SortField=id&OrderBy=true"
        response = await self.fetch_url_async(url, session)

        if response:
            data = response.get('data', [])
            if not data:
                logger.warning("No job data found in the API response.")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

            jobs_data = []
            for job in data:
                jobs_data.append({
                    'company': 'Kapital Bank',
                    'vacancy': job['header'],
                    'apply_link': f"https://hr.kapitalbank.az/vacancy/{job['id']}"
                })

            logger.info("Job data fetched and parsed successfully from Kapital Bank API")
            return pd.DataFrame(jobs_data)
        else:
            logger.error("Failed to fetch data from Kapital Bank API.")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])