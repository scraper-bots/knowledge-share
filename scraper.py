#!/usr/bin/env python3
"""
Async startup details scraper for knowledge-share.eu with retry mechanisms
Scrapes all startup details without images or HTML content
"""

import aiohttp
import asyncio
import json
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StartupDetailsScraper:
    """Async scraper for startup details with retry mechanisms"""
    
    BASE_URL = "https://www.knowledge-share.eu"
    LISTINGS_API = f"{BASE_URL}/api/pages/"
    
    def __init__(self, max_concurrent: int = 10, request_delay: float = 0.5):
        self.max_concurrent = max_concurrent
        self.request_delay = request_delay
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Headers from working configuration
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'en',
            'dnt': '1',
            'priority': 'u=1, i',
            'referer': 'https://www.knowledge-share.eu/en/start-ups?currentPage=1',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'cookie': 'sessionid=xqwssxzsexmi4kxif427o2zqlmrzgmpb; _gcl_gs=2.1.k1$i1756913135$u143345135; _gcl_au=1.1.1194548550.1756913140; _clck=1ymtsdg%5E2%5Efz0%5E0%5E2072; _clsk=7ljvx4%5E1756914538231%5E5%5E1%5Ej.clarity.ms%2Fcollect; _gcl_aw=GCL.1756914642.Cj0KCQjwzt_FBhCEARIsAJGFWVnbhx7xpSLXBhvUKq7duSxG_87S4DNjtaWoy7xQ1hBQfeUM6KVh4E0aAl61EALw_wcB; _iub_cs-13261173=%7B%22timestamp%22%3A%222025-09-03T15%3A25%3A57.650Z%22%2C%22version%22%3A%221.85.0%22%2C%22purposes%22%3A%7B%221%22%3Atrue%2C%222%22%3Afalse%2C%223%22%3Afalse%2C%224%22%3Afalse%2C%225%22%3Afalse%7D%2C%22id%22%3A%2213261173%22%2C%22cons%22%3A%7B%22rand%22%3A%227026c2%22%7D%7D; _iub_previous_preference_id=%7B%2213261173%22%3A%222025%2F09%2F03%2F15%2F25%2F57%2F650%2F7026c2%22%7D'
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True
    )
    async def fetch_json(self, session: aiohttp.ClientSession, url: str, params: Dict = None) -> Dict[str, Any]:
        """Fetch JSON data with retry mechanism"""
        async with self.semaphore:
            try:
                timeout = aiohttp.ClientTimeout(total=30)
                async with session.get(url, params=params, headers=self.headers, timeout=timeout) as response:
                    if response.status == 429:  # Rate limited
                        await asyncio.sleep(5)
                        raise aiohttp.ClientError("Rate limited")
                    
                    response.raise_for_status()
                    data = await response.json()
                    await asyncio.sleep(self.request_delay)  # Rate limiting
                    return data
                    
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                raise
    
    async def get_startup_page(self, session: aiohttp.ClientSession, limit: int, offset: int) -> Dict[str, Any]:
        """Get a single page of startups"""
        params = {
            'limit': str(limit),
            'offset': str(offset),
            'site': 'www.knowledge-share.eu',
            'order': '-first_published_at',
            'fields': 'abstract,categories,funding_stage,initiative,looking_for,options,preview_image,title,trl',
            'locale': 'en',
            'type': 'startups.StartUpPage'
        }
        
        return await self.fetch_json(session, self.LISTINGS_API, params)
    
    async def get_all_startup_urls(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """Get all startup detail URLs from listings API"""
        detail_urls = []
        offset = 0
        limit = 20  # API maximum
        
        logger.info("Getting startup URLs...")
        
        while True:
            try:
                data = await self.get_startup_page(session, limit, offset)
                items = data.get('items', [])
                
                if not items:
                    break
                
                for item in items:
                    detail_urls.append({
                        'id': item['id'],
                        'title': item['title'],
                        'detail_url': item['meta']['detailUrl']
                    })
                
                logger.info(f"Found {len(items)} URLs (total: {len(detail_urls)})")
                
                total_count = data.get('meta', {}).get('totalCount', 0)
                if len(detail_urls) >= total_count:
                    break
                
                offset += limit
                
            except Exception as e:
                logger.error(f"Error getting URLs at offset {offset}: {e}")
                break
        
        logger.info(f"Total startup URLs found: {len(detail_urls)}")
        return detail_urls
    
    async def get_startup_details(self, session: aiohttp.ClientSession, startup_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get detailed startup information with retry"""
        try:
            data = await self.fetch_json(session, startup_info['detail_url'])
            cleaned_data = self.clean_data(data)
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Failed to get details for {startup_info['title']}: {e}")
            return None
    
    def clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove image, HTML and unnecessary fields"""
        # Fields to exclude (images, HTML, meta info)
        exclude_fields = {
            'previewImage', 'coverImage', 'logo', 'meta', 'options',
            'htmlUrl', 'pagePath', 'detailUrl'
        }
        
        cleaned = {}
        for key, value in data.items():
            if key in exclude_fields:
                continue
            
            if isinstance(value, dict):
                # Recursively clean nested dictionaries
                if any(img_key in value for img_key in ['url', 'renditions', 'alt']):
                    continue  # Skip image objects
                cleaned_nested = self.clean_data(value)
                if cleaned_nested:  # Only add non-empty items
                    cleaned[key] = cleaned_nested
            elif isinstance(value, list):
                # Clean lists
                cleaned_list = []
                for item in value:
                    if isinstance(item, dict):
                        cleaned_item = self.clean_data(item)
                        if cleaned_item:  # Only add non-empty items
                            cleaned_list.append(cleaned_item)
                    else:
                        cleaned_list.append(item)
                if cleaned_list:  # Only add non-empty lists
                    cleaned[key] = cleaned_list
            else:
                cleaned[key] = value
        
        return cleaned
    
    async def scrape_startup_batch(self, session: aiohttp.ClientSession, startup_urls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scrape a batch of startups concurrently"""
        tasks = []
        for startup_info in startup_urls:
            task = self.get_startup_details(session, startup_info)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        successful_results = []
        failed_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Exception for {startup_urls[i]['title']}: {result}")
                failed_count += 1
            elif result is not None:
                successful_results.append(result)
            else:
                failed_count += 1
        
        if failed_count > 0:
            logger.warning(f"Failed to scrape {failed_count} startups in this batch")
        
        return successful_results
    
    async def scrape_all_details(self) -> List[Dict[str, Any]]:
        """Scrape details for all startups"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=60)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Get all URLs first
            startup_urls = await self.get_all_startup_urls(session)
            
            if not startup_urls:
                logger.error("No startup URLs found")
                return []
            
            logger.info(f"Starting to scrape details for {len(startup_urls)} startups...")
            
            all_details = []
            batch_size = 50  # Process in batches to manage memory
            
            for i in range(0, len(startup_urls), batch_size):
                batch = startup_urls[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(startup_urls) + batch_size - 1) // batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} startups)")
                
                batch_results = await self.scrape_startup_batch(session, batch)
                all_details.extend(batch_results)
                
                logger.info(f"Batch {batch_num} completed. Total scraped: {len(all_details)}")
                
                # Brief pause between batches
                if i + batch_size < len(startup_urls):
                    await asyncio.sleep(1)
            
            logger.info(f"Successfully scraped {len(all_details)} startup details")
            return all_details
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: str) -> None:
        """Save data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Saved {len(data)} records to {filename}")

async def main():
    """Main async function"""
    logger.info("Starting async startup details scraper...")
    
    # Initialize scraper with moderate concurrency
    scraper = StartupDetailsScraper(max_concurrent=10, request_delay=0.3)
    
    try:
        # Scrape all startup details
        all_details = await scraper.scrape_all_details()
        
        if all_details:
            # Save to JSON
            scraper.save_to_json(all_details, 'startup_details.json')
            
            # Show summary
            logger.info(f"✅ Scraping completed successfully!")
            logger.info(f"📊 Total startups scraped: {len(all_details)}")
            
            # Sample data
            if all_details:
                sample = all_details[0]
                logger.info(f"📋 Sample startup: {sample.get('title', 'N/A')}")
        else:
            logger.error("No data scraped")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())