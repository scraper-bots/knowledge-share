import asyncio
import random
import logging
import pandas as pd
import aiohttp
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class SmartjobAzScraper(BaseScraper):
    """
    SmartJob.az job scraper
    """
    
    @scraper_error_handler
    async def parse_smartjob_az(self, session):
        logger.info("Started scraping SmartJob.az")
        jobs = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://smartjob.az/',
            'Connection': 'keep-alive',
            'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        }

        for page in range(1, 5):
            url = f"https://smartjob.az/vacancies?page={page}"
            try:
                # Add delay between requests
                await asyncio.sleep(random.uniform(2, 4))
                
                response = await self.fetch_url_async(
                    url, 
                    session, 
                    headers=headers,
                    # ssl=False  # Disable SSL verification if needed
                )

                if response:
                    soup = BeautifulSoup(response, "html.parser")
                    job_listings = soup.find_all('div', class_='item-click')

                    if not job_listings:
                        logger.info(f"No job listings found on page {page}.")
                        continue

                    for listing in job_listings:
                        try:
                            title_elem = listing.find('div', class_='brows-job-position')
                            if title_elem and title_elem.h3 and title_elem.h3.a:
                                title = title_elem.h3.a.text.strip()
                                apply_link = title_elem.h3.a['href']
                                company_elem = listing.find('span', class_='company-title')
                                company = company_elem.a.text.strip() if company_elem and company_elem.a else "Unknown"
                                
                                jobs.append({
                                    'company': company,
                                    'vacancy': title,
                                    'apply_link': apply_link
                                })
                        except AttributeError as e:
                            logger.warning(f"Error parsing job listing: {e}")
                            continue
                else:
                    logger.warning(f"Failed to retrieve page {page}.")
                    # Add exponential backoff
                    await asyncio.sleep(2 ** page)
                    
            except aiohttp.ClientConnectorError as e:
                logger.error(f"Connection error on page {page}: {e}")
                await asyncio.sleep(5)  # Longer delay on connection error
                continue  # Try next page instead of breaking
                
            except Exception as e:
                logger.error(f"An error occurred on page {page}: {e}")
                await asyncio.sleep(3)
                continue

        logger.info("Scraping completed for SmartJob.az")
        return pd.DataFrame(jobs) if jobs else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])