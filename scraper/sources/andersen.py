import logging
import pandas as pd
import re
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class AndersenScraper(BaseScraper):
    """
    Andersen job scraper - scrapes actual jobs from Andersen careers page
    """
    
    @scraper_error_handler
    async def parse_andersen(self, session):
        logger.info("Started scraping Andersen careers")
        
        url = "https://people.andersenlab.com/vacancies"
        jobs_data = []
        
        try:
            # Fetch the careers page
            response = await self.fetch_url_async(url, session)
            
            if not response:
                logger.warning("Failed to fetch Andersen careers page")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            
            soup = BeautifulSoup(response, 'html.parser')
            
            # Look for job listings (you may need to adjust selectors based on actual page structure)
            job_elements = soup.find_all('div', class_='vacancy-item') or soup.find_all('a', href=lambda x: x and '/vacancy/' in x)
            
            if not job_elements:
                # Try alternative selectors
                job_elements = soup.find_all('a', href=re.compile(r'/vacancy/\d+'))
            
            for job_element in job_elements:
                try:
                    # Extract job title
                    title_elem = job_element.find('h3') or job_element.find('h2') or job_element.find('.title')
                    if not title_elem:
                        title_elem = job_element
                    
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown Position"
                    
                    # Extract apply link
                    if job_element.name == 'a':
                        apply_link = job_element.get('href')
                    else:
                        link_elem = job_element.find('a')
                        apply_link = link_elem.get('href') if link_elem else None
                    
                    if apply_link and not apply_link.startswith('http'):
                        apply_link = f"https://people.andersenlab.com{apply_link}"
                    
                    if title and apply_link:
                        jobs_data.append({
                            'company': 'Andersen',
                            'vacancy': title,
                            'apply_link': apply_link
                        })
                
                except Exception as e:
                    logger.warning(f"Error parsing job element: {e}")
                    continue
            
            if not jobs_data:
                logger.warning("No jobs found on Andersen careers page")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            
            logger.info(f"Successfully scraped {len(jobs_data)} jobs from Andersen")
            return pd.DataFrame(jobs_data)
            
        except Exception as e:
            logger.error(f"Error scraping Andersen: {e}")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
