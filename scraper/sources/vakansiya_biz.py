import logging
import pandas as pd
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class VakansiyaBizScraper(BaseScraper):
    """
    Vakansiya.biz job scraper
    """
    
    @scraper_error_handler
    async def parse_vakansiya_biz(self, session):
        logger.info("Started scraping Vakansiya.biz")
        base_url = "https://api.vakansiya.biz/api/v1/vacancies/search"
        headers = {'Content-Type': 'application/json'}
        page = 1
        all_jobs = []

        while True:
            response = await self.fetch_url_async(
                f"{base_url}?page={page}&country_id=108&city_id=0&industry_id=0&job_type_id=0&work_type_id=0&gender=-1&education_id=0&experience_id=0&min_salary=0&max_salary=0&title=",
                session,
                headers=headers
            )

            if not response:
                logger.error(f"Failed to fetch page {page}")
                break

            data = response.get('data', [])
            all_jobs.extend(data)

            if not response.get('next_page_url'):
                break

            page += 1

        job_listings = [{
            'company': job['company_name'].strip().lower(),
            'vacancy': job['title'].strip().lower(),
            'apply_link': f"https://vakansiya.biz/az/vakansiyalar/{job['id']}/{job['slug']}"
        } for job in all_jobs]

        df = pd.DataFrame(job_listings)
        logger.info("Scraping completed for Vakansiya.biz")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])