import asyncio
import logging
import pandas as pd
import aiohttp
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class IsverenAzScraper(BaseScraper):
    """
    Isveren.az job scraper
    """
    
    @scraper_error_handler
    async def parse_isveren_az(self, session):
        start_page = 1
        end_page = 15
        max_retries = 3
        backoff_factor = 1
        jobs = []

        for page_num in range(start_page, end_page + 1):
            retries = 0
            while retries < max_retries:
                try:
                    logger.info(f"Scraping started for isveren.az page {page_num}")
                    url = f"https://isveren.az/?page={page_num}"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
                    }

                    response = await self.fetch_url_async(url, session, headers=headers, verify_ssl=False)

                    if response:
                        soup = BeautifulSoup(response, 'html.parser')
                        job_cards = soup.find_all('div', class_='job-card')

                        for job_card in job_cards:
                            title_element = job_card.find('h5', class_='job-title')
                            company_element = job_card.find('p', class_='job-list')
                            link_element = job_card.find('a', href=True)

                            title = title_element.text.strip() if title_element else "No title provided"
                            company = company_element.text.strip() if company_element else "No company provided"
                            link = link_element['href'] if link_element else "No link provided"

                            jobs.append({
                                'company': company,
                                'vacancy': title,
                                'apply_link': link
                            })

                        break  # Exit the retry loop if the request was successful
                    else:
                        logger.error(f"Failed to retrieve page {page_num}.")
                        break

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    retries += 1
                    logger.warning(f"Attempt {retries} for page {page_num} failed: {e}")
                    if retries < max_retries:
                        sleep_time = backoff_factor * (2 ** (retries - 1))
                        logger.info(f"Retrying page {page_num} in {sleep_time} seconds...")
                        await asyncio.sleep(sleep_time)
                    else:
                        logger.error(f"Max retries exceeded for page {page_num}")

        df = pd.DataFrame(jobs)
        logger.info("Scraping completed for isveren.az")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])