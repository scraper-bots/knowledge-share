import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class OfferAzScraper(BaseScraper):
    """
    Offer.az job scraper
    """
    
    @scraper_error_handler
    async def parse_offer_az(self, session):
        logger.info("Started scraping offer.az")
        base_url = "https://www.offer.az/is-elanlari/page/"
        all_jobs = []

        for page_number in range(1, 8):
            url = f"{base_url}{page_number}/"
            response = await self.fetch_url_async(url, session)

            if response:
                soup = BeautifulSoup(response, 'html.parser')
                job_cards = soup.find_all('div', class_='job-card')

                for job_card in job_cards:
                    title_tag = job_card.find('a', class_='job-card__title')
                    title = title_tag.text.strip() if title_tag else "N/A"
                    link = title_tag['href'] if title_tag else "N/A"
                    company_tag = job_card.find('p', class_='job-card__meta')
                    company = company_tag.text.strip() if company_tag else "N/A"

                    all_jobs.append({
                        'vacancy': title,
                        'company': company,
                        'apply_link': link
                    })
            else:
                logger.warning(f"Failed to retrieve page {page_number}. Retrying...")
                # Retry mechanism
                retry_response = await self.fetch_url_async(url, session)
                if retry_response:
                    soup = BeautifulSoup(retry_response, 'html.parser')
                    job_cards = soup.find_all('div', class_='job-card')

                    for job_card in job_cards:
                        title_tag = job_card.find('a', class_='job-card__title')
                        title = title_tag.text.strip() if title_tag else "N/A"
                        link = title_tag['href'] if title_tag else "N/A"
                        company_tag = job_card.find('p', class_='job-card__meta')
                        company = company_tag.text.strip() if company_tag else "N/A"

                        all_jobs.append({
                            'vacancy': title,
                            'company': company,
                            'apply_link': link
                        })
                else:
                    logger.error(f"Failed to retrieve page {page_number} after retrying.")

        logger.info("Scraping completed for offer.az")
        return pd.DataFrame(all_jobs) if all_jobs else pd.DataFrame(columns=['vacancy', 'company', 'apply_link'])