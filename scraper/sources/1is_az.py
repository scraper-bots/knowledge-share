import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class OneIsAzScraper(BaseScraper):
    """
    1is.az job scraper
    """
    
    @scraper_error_handler
    async def scrape_1is_az(self, session):
        logger.info('Scraping started for 1is.az')
        pages = 3
        base_url = "https://1is.az/vsearch?expired=on&sort_by=1&page="
        job_listings = []

        for page in range(1, pages + 1):
            url = base_url + str(page)
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch page {page}. Status code: {response.status}")
                    continue

                html_content = await response.text()
                soup = BeautifulSoup(html_content, "html.parser")

                all_vacancies = soup.find_all('div', class_='vac-card')
                for vac in all_vacancies:
                    job = {}

                    vac_inner1 = vac.find('div', class_='vac-inner1')
                    if vac_inner1:
                        category = vac_inner1.find('a', class_='vac-inner1-a')
                        if category:
                            job['category'] = category.text.strip()
                        
                        views = vac_inner1.find('span', class_='look-numb')
                        if views:
                            job['views'] = views.text.strip()

                    vac_inner2 = vac.find('div', class_='vac-inner2')
                    if vac_inner2:
                        job_title = vac_inner2.find('a', class_='vac-name')
                        if job_title:
                            job['vacancy'] = job_title.text.strip()
                            job['apply_link'] = job_title['href']

                    vac_inner3 = vac.find('div', class_='vac-inner3')
                    if vac_inner3:
                        company_info = vac_inner3.find('div', class_='vac-inn1')
                        if company_info:
                            company = company_info.find('a', class_='comp-link')
                            if company:
                                job['company'] = company.text.strip()
                                job['company_link'] = company['href']

                    if 'company' in job and 'vacancy' in job and 'apply_link' in job:
                        job_listings.append(job)
        
        logger.info("Scraping completed for 1is.az")
        
        return pd.DataFrame(job_listings, columns=['company', 'vacancy', 'apply_link'])