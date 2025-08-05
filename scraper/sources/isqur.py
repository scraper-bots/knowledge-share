import logging
import pandas as pd
import asyncio
import random
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class IsqurScraper(BaseScraper):
    """
    Isqur.com job scraper with enhanced anti-bot protection
    """
    
    @scraper_error_handler
    async def parse_isqur(self, session):
        start_page = 1
        end_page = 5
        logger.info("Started scraping isqur.com")
        job_vacancies = []
        base_url = "https://isqur.com/is-elanlari/sehife-"

        # Enhanced headers to avoid 403 blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'az,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }

        for page_num in range(start_page, end_page + 1):
            logger.info(f"Scraping page {page_num} for isqur.com")
            url = f"{base_url}{page_num}"
            
            # Add random delay between requests
            if page_num > 1:
                await asyncio.sleep(random.uniform(2, 4))
            
            response = await self.fetch_url_async(url, session, headers=headers)
            if response:
                soup = BeautifulSoup(response, 'html.parser')
                job_cards = soup.find_all('div', class_='kart')
                for job in job_cards:
                    try:
                        title_element = job.find('div', class_='basliq')
                        if title_element:
                            title = title_element.text.strip()
                            company = "Unknown"  # The provided HTML does not include a company name
                            link_element = job.find('a')
                            if link_element and link_element.get('href'):
                                link = "https://isqur.com/" + link_element['href']
                                job_vacancies.append({'company': company, 'vacancy': title, 'apply_link': link})
                    except Exception as e:
                        logger.warning(f"Error parsing job card: {str(e)}")
                        continue
            else:
                logger.error(f"Failed to retrieve page {page_num} for isqur.com")

        logger.info(f"Scraping completed for isqur.com - found {len(job_vacancies)} jobs")
        return pd.DataFrame(job_vacancies) if job_vacancies else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])