import aiohttp
import asyncio
import pandas as pd
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_scraper import BaseScraper, scraper_error_handler


class JoobleAzScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://igrtzfvphltnoiwedbtz.supabase.co/rest/v1"
        self.api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlncnR6ZnZwaGx0bm9pd2VkYnR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIyMTQzMDYsImV4cCI6MjA2Nzc5MDMwNn0.afoeynzfpIZMqMRgpD0fDQ_NdULXEML-LZ-SocnYKp0"
        self.jobs_endpoint = f"{self.base_url}/jobs"
        
    def get_headers(self):
        """Get headers required for API requests"""
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Origin': 'https://jooble.az',
            'Referer': 'https://jooble.az/',
            'DNT': '1',
            'Sec-Ch-Ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'X-Client-Info': 'supabase-js-web/2.50.5',
            'apikey': self.api_key,
            'Authorization': f'Bearer {self.api_key}',
            'Accept-Profile': 'public'
        }
        
    def get_api_params(self, offset=0, limit=25):
        """Get API parameters for job listings"""
        return {
            'select': 'id,title,location,type,salary,tags,views,created_at,company_id,companies!inner(id,name,logo,is_verified),categories!inner(name)',
            'is_active': 'eq.true',
            'offset': str(offset),
            'limit': str(limit),
            'order': 'created_at.desc'
        }
        
    @scraper_error_handler
    async def scrape_jobs(self) -> pd.DataFrame:
        """Scrape job listings from jooble.az API"""
        connector = aiohttp.TCPConnector(ssl=True)
        timeout = aiohttp.ClientTimeout(total=60)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            jobs_data = []
            offset = 0
            limit = 25
            max_pages = 20  # Limit to avoid too many requests
            
            for page in range(max_pages):
                try:
                    params = self.get_api_params(offset, limit)
                    headers = self.get_headers()
                    
                    async with session.get(
                        self.jobs_endpoint, 
                        params=params, 
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if not data:  # No more data
                                break
                                
                            # Parse jobs from API response
                            page_jobs = await self.parse_api_jobs(data)
                            jobs_data.extend(page_jobs)
                            
                            # If we got less than the limit, we've reached the end
                            if len(data) < limit:
                                break
                                
                            offset += limit
                            
                            # Add small delay between requests
                            await asyncio.sleep(0.5)
                        else:
                            await self.log_scraper_error("jooble_az", f"HTTP {response.status} for page {page+1}")
                            break
                            
                except Exception as e:
                    await self.log_scraper_error("jooble_az", f"Error scraping page {page+1}: {str(e)}")
                    continue
            
            return pd.DataFrame(jobs_data, columns=['company', 'vacancy', 'apply_link'])
    
    async def parse_api_jobs(self, jobs_data: list) -> list:
        """Parse job listings from API response"""
        jobs = []
        
        try:
            for job in jobs_data:
                try:
                    job_info = await self.extract_job_info(job)
                    if job_info:
                        jobs.append(job_info)
                except Exception as e:
                    continue  # Skip individual job parsing errors
                    
        except Exception as e:
            await self.log_scraper_error("jooble_az", f"Error parsing API response: {str(e)}")
        
        return jobs
    
    async def extract_job_info(self, job_data: dict) -> dict:
        """Extract job information from API response item"""
        try:
            # Extract basic job information
            job_id = job_data.get('id', '')
            title = job_data.get('title', '').strip()
            location = job_data.get('location', '').strip()
            
            # Extract company information
            company_info = job_data.get('companies', {})
            company_name = company_info.get('name', 'n/a').strip()
            
            # Create apply link (assuming jooble.az uses job IDs in URLs)
            apply_link = f"https://jooble.az/job/{job_id}" if job_id else "https://jooble.az/"
            
            # Format vacancy title with location if available
            vacancy = title
            if location and location.lower() not in title.lower():
                vacancy = f"{title} - {location}"
            
            return {
                'company': company_name if company_name else 'n/a',
                'vacancy': vacancy,
                'apply_link': apply_link
            }
            
        except Exception as e:
            return None


async def main():
    """Test the scraper"""
    scraper = JoobleAzScraper()
    
    try:
        df = await scraper.scrape_jobs()
        print(f"Scraped {len(df)} jobs from jooble.az")
        
        if not df.empty:
            print("\nSample data:")
            print(df.head(10))
            
            # Show some statistics
            print(f"\nUnique companies: {df['company'].nunique()}")
            print(f"Jobs with 'n/a' company: {len(df[df['company'] == 'n/a'])}")
            
            # Show some sample job titles and companies
            print("\nSample job listings:")
            for i, row in df.head(5).iterrows():
                print(f"- {row['company']}: {row['vacancy']}")
            
            # Save to database if data was found
            scraper.save_to_db(df)
            print("Data saved to database")
        else:
            print("No data scraped")
            
    except Exception as e:
        print(f"Error running scraper: {e}")


if __name__ == "__main__":
    asyncio.run(main())