import aiohttp
import asyncio
import pandas as pd
from bs4 import BeautifulSoup
import re
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_scraper import BaseScraper, scraper_error_handler


class JobuAzScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://jobu.az"
        self.vacancies_url = "https://jobu.az/vakansiyalar"
        
    @scraper_error_handler
    async def parse_jobu_az(self, session) -> pd.DataFrame:
        """Scrape job listings from jobu.az"""
        jobs_data = []
        
        # Scrape multiple pages
        for page in range(1, 6):  # Scrape first 5 pages
            try:
                page_url = f"{self.vacancies_url}/page/{page}/"
                content = await self.fetch_url_async(page_url, session, verify_ssl=False)
                
                if not content:
                    break
                    
                jobs_data.extend(self.parse_jobs_page(content))
                
                # Add small delay between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                await self.log_scraper_error("jobu_az", f"Error scraping page {page}: {str(e)}", page_url)
                continue
        
        return pd.DataFrame(jobs_data, columns=['company', 'vacancy', 'apply_link'])
    
    def parse_jobs_page(self, html_content: str) -> list:
        """Parse job listings from a single page"""
        jobs = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find the main container with job listings
            jobs_container = soup.find('div', class_='items-wrapper-list-v4')
            if not jobs_container:
                return jobs
            
            # Find all job items
            job_items = jobs_container.find_all('div', class_='item-job')
            
            for item in job_items:
                try:
                    job_data = self.extract_job_info(item)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    continue  # Skip individual job parsing errors
            
        except Exception as e:
            # Log error but continue processing
            pass
        
        return jobs
    
    def extract_job_info(self, job_item) -> dict:
        """Extract job information from a job item element"""
        try:
            # Extract job title and apply link
            job_title_element = job_item.find('bold', class_='job-title')
            if not job_title_element:
                return None
                
            title_link = job_title_element.find('a')
            if not title_link:
                return None
                
            vacancy = title_link.get_text(strip=True)
            apply_link = title_link.get('href', '')
            
            # Make sure apply_link is absolute
            if apply_link and not apply_link.startswith('http'):
                apply_link = self.base_url + apply_link
            
            # Extract company name from employer logo
            company = "n/a"
            employer_logo = job_item.find('div', class_='employer-logo')
            if employer_logo:
                # Try to get company from alt text of logo image
                logo_img = employer_logo.find('img')
                if logo_img:
                    company = logo_img.get('alt', '').strip()
                    if not company:
                        # Try to extract from image src filename
                        src = logo_img.get('src', '')
                        if src:
                            # Extract filename without extension
                            filename = src.split('/')[-1].split('.')[0]
                            # Clean up filename to make it readable
                            company = filename.replace('-', ' ').replace('_', ' ').title()
            
            # Clean company name
            if company and company.lower() != 'n/a':
                # Capitalize first letter of each word
                company = ' '.join(word.capitalize() for word in company.split())
            else:
                company = "n/a"
            
            return {
                'company': company,
                'vacancy': vacancy,
                'apply_link': apply_link
            }
            
        except Exception as e:
            return None


async def main():
    """Test the scraper"""
    scraper = JobuAzScraper()
    
    try:
        df = await scraper.scrape_jobs()
        print(f"Scraped {len(df)} jobs from jobu.az")
        
        if not df.empty:
            print("\nSample data:")
            print(df.head())
            
            # Save to database if data was found
            scraper.save_to_db(df)
            print("Data saved to database")
        else:
            print("No data scraped")
            
    except Exception as e:
        print(f"Error running scraper: {e}")


if __name__ == "__main__":
    asyncio.run(main())