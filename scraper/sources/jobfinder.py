import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class JobfinderScraper(BaseScraper):
    """
    JobFinder.az job scraper
    """
    
    @scraper_error_handler
    async def parse_jobfinder(self, session):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        all_job_data = []

        start_page = 1
        end_page = 10

        for page_number in range(start_page, end_page + 1):
            url = f"https://jobfinder.az/job?page={page_number}"
            response = await self.fetch_url_async(url, session, headers=headers)

            if not response:
                logger.error(f"Failed to retrieve page {page_number}")
                continue

            soup = BeautifulSoup(response, 'html.parser')
            job_listings = soup.find_all('div', class_='content_list_item job_list_item clearfix')

            for job in job_listings:
                # Extract job title
                title_tag = job.find('h3', class_='value').find('a') if job.find('h3', class_='value') else None
                
                # Try multiple methods to extract company name
                company_name = 'N/A'
                company_tag = job.find('div', class_='jobListCompany')
                
                if company_tag:
                    # Method 1: Try image alt attribute
                    img_tag = company_tag.find('img')
                    if img_tag and img_tag.get('alt'):
                        company_name = img_tag['alt']
                    else:
                        # Method 2: Try direct text content
                        company_text = company_tag.get_text(strip=True)
                        if company_text:
                            company_name = company_text
                
                # Method 3: Look for company in job card headings
                if company_name == 'N/A':
                    company_heading = job.find('h4')
                    if company_heading:
                        company_link = company_heading.find('a')
                        if company_link:
                            company_name = company_link.get_text(strip=True)
                
                # Method 4: Try other common containers
                if company_name == 'N/A':
                    for selector in ['.company', '.org', '.jobAuthor a', '.employer']:
                        company_elem = job.select_one(selector)
                        if company_elem:
                            company_name = company_elem.get_text(strip=True)
                            break
                
                all_job_data.append({
                    'company': company_name,
                    'vacancy': title_tag.text.strip() if title_tag else 'N/A',
                    'apply_link': 'https://jobfinder.az' + title_tag['href'] if title_tag and 'href' in title_tag.attrs else 'N/A'
                })

        if all_job_data:
            df = pd.DataFrame(all_job_data)
            logger.info(f"Scraping completed for JobFinder. Found {len(all_job_data)} jobs.")
            return df
        else:
            logger.warning("No job listings found on JobFinder.")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])