import asyncio
import random
import logging
import pandas as pd
import aiohttp
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class AzerconnectScraper(BaseScraper):
    """
    Enhanced Azerconnect scraper with increased timeouts and better connection handling
    """
    
    @scraper_error_handler
    async def parse_azerconnect(self, session):
        """
        Enhanced Azerconnect scraper with increased timeouts and better connection handling
        """
        logger.info("Started scraping Azerconnect")
        
        base_url = "https://www.azerconnect.az"
        url = f"{base_url}/vacancies"

        # Rotating User-Agent pool
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
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

        max_retries = 3
        base_delay = 5

        for attempt in range(max_retries):
            try:
                # Increased timeouts
                timeout = aiohttp.ClientTimeout(
                    total=60,          # Increased total timeout
                    connect=20,        # Increased connection timeout
                    sock_connect=20,   # Socket connection timeout
                    sock_read=30       # Socket read timeout
                )
                
                connector = aiohttp.TCPConnector(
                    ssl=False,
                    limit=1,
                    force_close=True,
                    enable_cleanup_closed=True
                )

                async with aiohttp.ClientSession(
                    timeout=timeout,
                    connector=connector,
                    headers=headers
                ) as client:
                    # First try accessing the homepage
                    try:
                        async with client.get(base_url) as init_response:
                            if init_response.status != 200:
                                logger.error(f"Failed to access homepage (attempt {attempt + 1}): {init_response.status}")
                                delay = base_delay * (2 ** attempt)
                                await asyncio.sleep(delay)
                                continue

                            # Add delay between requests
                            await asyncio.sleep(random.uniform(2, 4))

                            # Update headers for main request
                            headers.update({
                                'Referer': base_url,
                                'Origin': base_url
                            })

                            # Fetch vacancies page
                            async with client.get(url, headers=headers) as response:
                                if response.status != 200:
                                    logger.error(f"Failed to fetch vacancies (attempt {attempt + 1}): {response.status}")
                                    delay = base_delay * (2 ** attempt)
                                    await asyncio.sleep(delay)
                                    continue

                                content = await response.text()
                                
                                if not content or len(content) < 1000:
                                    logger.error(f"Invalid content received (attempt {attempt + 1})")
                                    delay = base_delay * (2 ** attempt)
                                    await asyncio.sleep(delay)
                                    continue

                                soup = BeautifulSoup(content, 'html.parser')
                                job_listings = soup.find_all('div', class_='CollapsibleItem_item__CB3bC')

                                if not job_listings:
                                    logger.error(f"No job listings found (attempt {attempt + 1})")
                                    delay = base_delay * (2 ** attempt)
                                    await asyncio.sleep(delay)
                                    continue

                                jobs_data = []
                                for job in job_listings:
                                    try:
                                        title_block = job.find('div', class_='CollapsibleItem_toggle__XNu5y')
                                        title = title_block.find('span').text.strip() if title_block and title_block.find('span') else None
                                        
                                        if not title:
                                            continue

                                        apply_btn = job.find('a', class_='Button_button-blue__0wZ4l')
                                        apply_link = apply_btn['href'] if apply_btn and 'href' in apply_btn.attrs else None
                                        
                                        if not apply_link:
                                            continue

                                        content_block = job.find('div', class_='CollapsibleItem_contentInner__vVcvk')
                                        if not content_block:
                                            continue

                                        jobs_data.append({
                                            'company': 'Azerconnect',
                                            'vacancy': title,
                                            'apply_link': apply_link
                                        })

                                    except Exception as e:
                                        logger.error(f"Error parsing individual job: {str(e)}")
                                        continue

                                if jobs_data:
                                    logger.info(f"Successfully scraped {len(jobs_data)} jobs from Azerconnect")
                                    return pd.DataFrame(jobs_data)

                    except aiohttp.ClientError as e:
                        logger.error(f"Client error (attempt {attempt + 1}): {str(e)}")
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            await asyncio.sleep(delay)
                            continue
                        return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

                    except asyncio.TimeoutError:
                        logger.error(f"Timeout error (attempt {attempt + 1})")
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            await asyncio.sleep(delay)
                            continue
                        return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

            except Exception as e:
                logger.error(f"Unexpected error (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

        logger.error("All attempts failed for Azerconnect scraper")
        return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])