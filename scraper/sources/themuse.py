import logging
import pandas as pd
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class TheMuseScraper(BaseScraper):
    """
    TheMuse.com API job scraper for remote and location-based jobs
    """
    
    @scraper_error_handler
    async def scrape_themuse_api(self, session):
        """
        Scrape job listings from TheMuse.com API
        """
        api_url = "https://www.themuse.com/api/search-renderer/jobs"
        params = {
            'ctsEnabled': 'false',
            'latlng': '40.37767028808594,49.89200973510742',
            'preference': 'bf2kq0pm0q8',
            'limit': 100,
            'query': '',
            'timeout': 5000
        }

        async with session.get(api_url, params=params) as response:
            if response.status != 200:
                logger.error(f"Failed to fetch data. Status code: {response.status}")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

            data = await response.json()

            jobs = []
            for hit in data.get('hits', []):
                job_data = hit.get('hit', {})
                company_name = job_data.get('company', {}).get('name', '')
                vacancy_title = job_data.get('title', '')
                company_short_name = job_data.get('company', {}).get('short_name', '')
                short_title = job_data.get('short_title', '')
                apply_link = f"https://www.themuse.com/jobs/{company_short_name}/{short_title}"

                job = {
                    'company': company_name,
                    'vacancy': vacancy_title,
                    'apply_link': apply_link
                }
                jobs.append(job)

        return pd.DataFrame(jobs, columns=['company', 'vacancy', 'apply_link'])