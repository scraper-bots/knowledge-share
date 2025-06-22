import logging
import pandas as pd
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class UnJobsScraper(BaseScraper):
    """
    UN Azerbaijan job scraper for career listings
    """
    
    @scraper_error_handler
    async def scrape_un_jobs(self, session):
        """
        Scrape job listings from UN Azerbaijan website
        """
        logger.info("Scraping started for UN")
        url = 'https://azerbaijan.un.org/az/jobs'
        base_url = 'https://azerbaijan.un.org'

        async with session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                job_listings = []

                # Find all job article elements
                job_cards = soup.find_all('article', class_='node--view-mode-teaser')

                for job in job_cards:
                    # Extract the title and link
                    title_tag = job.find('a', attrs={'data-once': 'submenu-reveal'})
                    title = title_tag.get_text(strip=True) if title_tag else 'N/A'  # Fall back to get_text() if title attribute is missing
                    href = title_tag['href'] if title_tag else ''
                    
                    # Ensure the full apply link is constructed correctly
                    if href.startswith('http'):
                        apply_link = href
                    else:
                        apply_link = urljoin(base_url, href)

                    # Extract the organization name
                    organization_tag = job.find('div', class_='text-un-gray-dark text-lg')
                    organization = organization_tag.get_text(strip=True) if organization_tag else 'N/A'

                    job_listings.append({
                        'company': organization,
                        'vacancy': title,
                        'apply_link': apply_link
                    })

                df = pd.DataFrame(job_listings)
                logger.info("Scraping completed for UN")
                logger.info(f"\n{df}")
                return df
            else:
                logger.error(f"Failed to retrieve the webpage. Status code: {response.status}")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])