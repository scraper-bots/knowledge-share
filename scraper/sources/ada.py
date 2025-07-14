import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class AdaScraper(BaseScraper):
    """
    ADA University job scraper
    """
    
    @scraper_error_handler
    async def parse_ada(self, session):
        logger.info("Started scraping ADA University")

        # Try both English and main career pages
        urls = ["https://ada.edu.az/en/jobs", "https://ada.edu.az/jobs"]
        jobs = []
        
        for url in urls:
            response = await self.fetch_url_async(url, session, verify_ssl=False)
            
            if response:
                soup = BeautifulSoup(response, 'html.parser')

                # Look for various job listing structures
                # Try original table structure
                table = soup.find('table', class_='table-job')
                if table and table.find('tbody'):
                    for row in table.find('tbody').find_all('tr'):
                        title_tag = row.find('td', class_='name').find('a') if row.find('td', class_='name') else None
                        view_link_tag = row.find('td', class_='view').find('a') if row.find('td', class_='view') else None

                        # Safely get the title and apply link
                        title = title_tag.text.strip() if title_tag else "N/A"
                        apply_link = view_link_tag['href'] if view_link_tag else "N/A"

                        if title != "N/A":
                            job = {
                                'company': 'ADA University',
                                'vacancy': title,
                                'apply_link': f"https://ada.edu.az{apply_link}" if apply_link.startswith('/') else apply_link
                            }
                            jobs.append(job)
                    
                    if jobs:
                        break  # Found jobs, no need to try other URLs
                
                # Try alternative structures if no table found
                elif not jobs:
                    # Look for job cards or other structures
                    job_cards = soup.find_all(['div', 'li'], class_=lambda x: x and ('job' in str(x).lower() or 'vacancy' in str(x).lower() or 'career' in str(x).lower()))
                    
                    for card in job_cards:
                        title_elem = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a'])
                        if title_elem and title_elem.get_text(strip=True):
                            title = title_elem.get_text(strip=True)
                            link = card.find('a')
                            apply_link = link['href'] if link and 'href' in link.attrs else url
                            
                            job = {
                                'company': 'ADA University',
                                'vacancy': title,
                                'apply_link': f"https://ada.edu.az{apply_link}" if apply_link.startswith('/') else apply_link
                            }
                            jobs.append(job)
                    
                    if jobs:
                        break  # Found jobs, no need to try other URLs

        # Return results
        if jobs:
            df = pd.DataFrame(jobs)
            logger.info(f"Scraping completed for ADA University - found {len(jobs)} jobs")
            return df
        else:
            logger.warning("No job listings found on ADA University pages")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])