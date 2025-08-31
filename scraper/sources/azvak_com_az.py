import asyncio
import logging
import pandas as pd
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class AzvakComAzScraper(BaseScraper):
    """
    Azvak.com.az job scraper - uses JSON API
    """
    
    @scraper_error_handler
    async def parse_azvak_com_az(self, session) -> pd.DataFrame:
        """Scrape job listings from azvak.com.az API"""
        jobs_data = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://azvak.az',
            'Referer': 'https://azvak.az/',
            'Sec-Ch-Ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'DNT': '1'
        }

        try:
            # Scrape first 5 pages (120 jobs total, 24 per page)
            for page in range(1, 6):
                try:
                    # Add delay between requests
                    if page > 1:
                        await asyncio.sleep(random.uniform(1, 3))
                    
                    url = "https://rest.azvak.com.az/api/vacancies"
                    params = {
                        'page': page,
                        'count': 24,
                        'title': '',
                        'category': '',
                        'location': '',
                        'company': '',
                        'department': '',
                        'experience_interval': '',
                        'salary': '',
                        'sort': ''
                    }
                    
                    # Use direct session call to handle JSON properly
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            response_data = await response.json()
                        else:
                            logger.warning(f"HTTP {response.status} for page {page}")
                            continue
                    
                    if response_data and isinstance(response_data, dict):
                        # Parse JSON response - expect {"data": [...]}
                        vacancies = response_data.get('data', [])
                        
                        if not vacancies and page == 1:
                            logger.warning("No vacancies found in API response")
                            break
                        elif not vacancies:
                            # No more pages
                            break
                        
                        for vacancy in vacancies:
                            try:
                                # Handle nested company object
                                company_obj = vacancy.get('company', {})
                                if isinstance(company_obj, dict):
                                    company = company_obj.get('name', '').strip()
                                else:
                                    company = str(company_obj).strip()
                                
                                title = vacancy.get('title', '').strip()
                                vacancy_id = vacancy.get('id', '')
                                
                                # Create apply link
                                if vacancy_id:
                                    apply_link = f"https://azvak.az/vacancy/{vacancy_id}"
                                else:
                                    apply_link = "https://azvak.az/"
                                
                                if company and title:
                                    jobs_data.append({
                                        'company': company,
                                        'vacancy': title,
                                        'apply_link': apply_link
                                    })
                                    
                            except Exception as e:
                                logger.warning(f"Error parsing vacancy: {e}")
                                continue
                    else:
                        logger.warning(f"Invalid or empty response for page {page}")
                        
                except Exception as e:
                    logger.error(f"Error scraping page {page}: {e}")
                    continue
                    
        except Exception as e:
            await self.log_scraper_error("azvak_com_az", f"Error accessing API: {str(e)}", "https://rest.azvak.com.az/api/vacancies")
        
        logger.info(f"Scraping completed for azvak.com.az - found {len(jobs_data)} jobs")
        return pd.DataFrame(jobs_data, columns=['company', 'vacancy', 'apply_link'])


async def main():
    """Test the scraper"""
    scraper = AzvakComAzScraper()
    
    import aiohttp
    async with aiohttp.ClientSession() as session:
        try:
            df = await scraper.parse_azvak_com_az(session)
            print(f"Scraped {len(df)} jobs from azvak.com.az")
            
            if not df.empty:
                print("\nSample data:")
                print(df.head())
                
                print("\nSample job listings:")
                for i, row in df.head(5).iterrows():
                    print(f"- {row['company']}: {row['vacancy']}")
            else:
                print("No data scraped")
                
        except Exception as e:
            print(f"Error running scraper: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())