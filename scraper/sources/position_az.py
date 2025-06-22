import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class PositionAzScraper(BaseScraper):
    """
    Position.az job scraper
    """
    
    @scraper_error_handler
    async def scrape_position_az(self, session):
        url = 'https://position.az'

        async with session.get(url) as response:
            if response.status == 200:
                # Parse the HTML content using BeautifulSoup
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find the job listings
                job_listings = soup.find_all('tr', {'class': lambda x: x and x.startswith('category-')})
                
                # Initialize lists to store the job data
                vacancies = []
                companies = []
                apply_links = []
                
                # Loop through each job listing and extract the data
                for job in job_listings:
                    vacancy = job.find('td', {'title': True}).get_text(strip=True)
                    company = job.find_all('td')[1].get_text(strip=True)
                    apply_link = job.find('a')['href']
                    
                    vacancies.append(vacancy)
                    companies.append(company)
                    # Fix the apply link if it does not start with 'https://position.az'
                    if not apply_link.startswith('https://position.az'):
                        apply_link = url + apply_link
                    apply_links.append(apply_link)
                
                # Create a DataFrame from the lists
                data = {
                    'vacancy': vacancies,
                    'company': companies,
                    'apply_link': apply_links
                }
                df = pd.DataFrame(data)
                
                return df
            else:
                logger.error(f"Failed to retrieve the webpage. Status code: {response.status}")
                return pd.DataFrame(columns=['vacancy', 'company', 'apply_link'])