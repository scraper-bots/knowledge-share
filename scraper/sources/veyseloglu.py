import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class VeyselogluScraper(BaseScraper):
    """
    Veyseloglu job scraper for job listings from karyera.veyseloglu.az
    """
    
    @scraper_error_handler
    async def scrape_veyseloglu(self, session):
        """
        Scrape job listings from karyera.veyseloglu.az across multiple pages
        """
        page_limit = 10
        base_url = "https://karyera.veyseloglu.az/home/allvacancies"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        job_data = []

        for page in range(1, page_limit + 1):
            params = {
                'pageIndex': page,
                'pageSize': 10
            }
            
            response = await self.fetch_url_async(base_url, session, params=params, headers=headers, verify_ssl=False)

            if not response:
                logger.error(f"Failed to fetch page {page} from veyseloglu.az")
                continue

            soup = BeautifulSoup(response, 'html.parser')
            
            # Find the vacancy body container
            vacancy_body = soup.find('div', {'class': 'vacancy-body'})
            if not vacancy_body:
                logger.warning(f"No vacancy body found on page {page}")
                continue
                
            # Find all job listings
            job_listings = vacancy_body.find_all('div', {'class': 'vacancies-option hot-content'})

            if not job_listings:
                logger.info(f"No more job listings found on page {page}, stopping")
                break

            for job in job_listings:
                try:
                    # Extract job title
                    title_element = job.find('h3', {'class': 'vacancies-option__title'})
                    job_title = title_element.text.strip() if title_element else 'n/a'
                    
                    # Extract company name (Veyseloglu for all listings)
                    company = 'Veyseloglu MMC'
                    
                    # Extract location
                    location_element = job.find('div', {'class': 'hot-vacancies__office'})
                    location = location_element.find('span').text.strip() if location_element and location_element.find('span') else 'n/a'
                    
                    # Extract application deadline
                    date_element = job.find('div', {'class': 'hot-vacancies__date'})
                    deadline = date_element.find('span').text.strip() if date_element and date_element.find('span') else 'n/a'
                    
                    # Extract vacancy ID from hidden input
                    vacancy_id_input = job.find('input', {'type': 'hidden'})
                    vacancy_id = vacancy_id_input.get('value') if vacancy_id_input else None
                    
                    # Construct apply link
                    if vacancy_id:
                        apply_link = f"https://karyera.veyseloglu.az/vac/detail?vacancyId={vacancy_id}"
                    else:
                        # Fallback - try to find the detail link
                        detail_link = job.find('a', {'class': 'vacancies-option__light'})
                        if detail_link and detail_link.get('href'):
                            apply_link = f"https://karyera.veyseloglu.az{detail_link.get('href')}"
                        else:
                            apply_link = base_url
                    
                    # Combine title with location for more detailed vacancy name
                    if location != 'n/a':
                        full_title = f"{job_title} - {location}"
                    else:
                        full_title = job_title
                        
                    if deadline != 'n/a' and 'Son müraciət tarixi' in deadline:
                        deadline_date = deadline.replace('Son müraciət tarixi: ', '')
                        full_title = f"{full_title} (Son tarix: {deadline_date})"

                    job_data.append({
                        'company': company,
                        'vacancy': full_title,
                        'apply_link': apply_link
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing job listing: {str(e)}")
                    continue

            logger.info(f"Scraped page {page} for veyseloglu.az - found {len(job_listings)} listings")

        df = pd.DataFrame(job_data)
        logger.info(f"Scraping completed for veyseloglu.az - total jobs: {len(job_data)}")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])