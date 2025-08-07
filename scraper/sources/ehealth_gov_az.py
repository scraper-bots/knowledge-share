import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class EhealthGovAzScraper(BaseScraper):
    """
    e-health.gov.az job scraper for government healthcare positions
    """
    
    @scraper_error_handler
    async def scrape_ehealth_gov_az(self, session):
        """
        Scrape job listings from e-health.gov.az career pages
        """
        base_url = "https://e-health.gov.az/Career"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,az;q=0.8"
        }

        job_data = []
        page = 1
        max_pages = 5  # Limit to prevent infinite loops

        while page <= max_pages:
            # For first page, use base URL, for others add page parameter
            url = base_url if page == 1 else f"{base_url}?page={page}"
            
            response = await self.fetch_url_async(url, session, headers=headers, verify_ssl=True)

            if not response:
                logger.error(f"Failed to fetch page {page} from e-health.gov.az")
                break

            soup = BeautifulSoup(response, 'html.parser')
            
            # Find all job cards
            job_cards = soup.find_all('div', class_='col-md-4')
            
            if not job_cards:
                logger.info(f"No more job cards found on page {page}")
                break

            page_jobs_found = 0
            
            for card in job_cards:
                try:
                    # Check if this is a job card (has onclick attribute with Career/Details)
                    onclick_attr = card.get('onclick', '')
                    if 'Career/Details' not in onclick_attr:
                        continue
                    
                    # Extract job ID from onclick attribute
                    # Example: window.location= '/Career/Details/2146'
                    job_id = None
                    if onclick_attr:
                        try:
                            # Extract the ID from the onclick string
                            start_idx = onclick_attr.find('/Career/Details/') + len('/Career/Details/')
                            end_idx = onclick_attr.find("'", start_idx)
                            if end_idx > start_idx:
                                job_id = onclick_attr[start_idx:end_idx]
                        except:
                            pass
                    
                    # Find job title
                    title_element = card.find('h4', class_='card-title')
                    job_title = title_element.text.strip() if title_element else 'n/a'
                    
                    # Find date
                    date_element = card.find('small', class_='text-muted')
                    job_date = date_element.text.strip() if date_element else 'n/a'
                    
                    # Build comprehensive job title with date
                    full_title = job_title
                    if job_date != 'n/a':
                        full_title = f"{job_title} (Posted: {job_date})"
                    
                    # Build apply link
                    if job_id:
                        apply_link = f"https://e-health.gov.az/Career/Details/{job_id}"
                    else:
                        apply_link = base_url

                    job_data.append({
                        'company': 'e-health.gov.az (Ministry of Health)',
                        'vacancy': full_title,
                        'apply_link': apply_link
                    })
                    
                    page_jobs_found += 1
                    
                except Exception as e:
                    logger.error(f"Error parsing e-health.gov.az job card: {str(e)}")
                    continue

            if page_jobs_found == 0:
                logger.info(f"No valid job cards found on page {page}, stopping")
                break
                
            logger.info(f"Scraped {page_jobs_found} jobs from e-health.gov.az page {page}")
            
            # Check if there's a next page by looking for pagination
            pagination = soup.find('nav', {'aria-label': '...'})
            has_next = False
            if pagination:
                next_links = pagination.find_all('a', class_='page-link')
                for link in next_links:
                    if 'Növbəti' in link.text or 'Next' in link.text:
                        parent_li = link.find_parent('li')
                        if parent_li and 'disabled' not in parent_li.get('class', []):
                            has_next = True
                            break
            
            if not has_next:
                logger.info(f"No more pages available after page {page}")
                break
                
            page += 1

        df = pd.DataFrame(job_data)
        logger.info(f"e-health.gov.az scraping completed - total jobs: {len(job_data)}")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])