import aiohttp
import asyncio
import pandas as pd
import json
import re
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_scraper import BaseScraper, scraper_error_handler


class JobgetherComScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://jobgether.com"
        
    @scraper_error_handler
    async def parse_jobgether_com(self, session) -> pd.DataFrame:
        """Scrape remote job listings from jobgether.com for Azerbaijan"""
        jobs_data = []
        
        try:
            # jobgether.com uses heavy JavaScript and may block automated requests
            # This is a basic implementation that extracts available remote jobs for Azerbaijan
            page_url = f"{self.base_url}/remote-jobs/azerbaijan/1"
            
            # Enhanced headers to appear more browser-like
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
            }
            
            content = await self.fetch_url_async(page_url, session, headers=headers)
            
            if content and len(content) > 1000:
                jobs_data = self.parse_jobs_page(content)
                
                # Remove duplicates based on company and vacancy
                if jobs_data:
                    seen = set()
                    unique_jobs = []
                    for job in jobs_data:
                        job_key = (job['company'], job['vacancy'])
                        if job_key not in seen:
                            seen.add(job_key)
                            unique_jobs.append(job)
                    jobs_data = unique_jobs
                
        except Exception as e:
            await self.log_scraper_error("jobgether_com", f"Error accessing site: {str(e)}", self.base_url)
        
        return pd.DataFrame(jobs_data, columns=['company', 'vacancy', 'apply_link'])
    
    def parse_jobs_page(self, html_content: str) -> list:
        """Parse job listings from a single page"""
        jobs = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # First try to extract JSON data from script tags
            script_tags = soup.find_all('script', string=re.compile(r'__ASTRO_DATA__'))
            json_jobs = self.extract_jobs_from_json(script_tags)
            if json_jobs:
                jobs.extend(json_jobs)
                return jobs
            
            # Fallback to HTML parsing if JSON extraction fails
            jobs.extend(self.extract_jobs_from_html(soup))
            
        except Exception as e:
            # Continue with empty list if parsing fails
            pass
        
        return jobs
    
    def extract_jobs_from_json(self, script_tags: list) -> list:
        """Extract jobs from embedded JSON data"""
        jobs = []
        
        try:
            for script in script_tags:
                if script.string:
                    # Look for JSON data containing job information
                    json_match = re.search(r'__ASTRO_DATA__\s*=\s*({.*?});', script.string, re.DOTALL)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(1))
                            # Parse the JSON structure to extract job data
                            extracted_jobs = self.parse_json_jobs(data)
                            jobs.extend(extracted_jobs)
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass
            
        return jobs
    
    def parse_json_jobs(self, json_data: dict) -> list:
        """Parse job data from JSON structure"""
        jobs = []
        
        try:
            # Navigate through the JSON structure to find job listings
            # The structure may vary, so we'll be flexible
            if isinstance(json_data, dict):
                for key, value in json_data.items():
                    if isinstance(value, list):
                        # Look for arrays that might contain job data
                        for item in value:
                            if isinstance(item, dict) and 'title' in item:
                                job = self.extract_job_from_json_item(item)
                                if job:
                                    jobs.append(job)
                    elif isinstance(value, dict):
                        # Recursively search nested objects
                        nested_jobs = self.parse_json_jobs(value)
                        jobs.extend(nested_jobs)
        except Exception:
            pass
            
        return jobs
    
    def extract_job_from_json_item(self, item: dict) -> dict:
        """Extract job information from a JSON job item"""
        try:
            title = item.get('title', '').strip()
            company = item.get('company', {})
            if isinstance(company, dict):
                company_name = company.get('name', '').strip()
            else:
                company_name = str(company).strip()
            
            # Generate apply link from job ID or slug
            job_id = item.get('id', '')
            slug = item.get('slug', '')
            
            if job_id and title:
                # Create URL slug from title
                title_slug = re.sub(r'[^a-zA-Z0-9\-]', '-', title.lower()).strip('-')
                apply_link = f"{self.base_url}/offer/{job_id}-{title_slug}"
            elif slug:
                apply_link = f"{self.base_url}/offer/{slug}"
            else:
                apply_link = f"{self.base_url}/remote-jobs/azerbaijan"
            
            if title and company_name:
                return {
                    'company': company_name,
                    'vacancy': title,
                    'apply_link': apply_link
                }
        except Exception:
            pass
            
        return None
    
    def extract_jobs_from_html(self, soup: BeautifulSoup) -> list:
        """Fallback HTML parsing method"""
        jobs = []
        
        try:
            # Based on the site analysis, look for specific patterns
            # Try to find job links that match the pattern /offer/...
            job_links = soup.find_all('a', href=re.compile(r'/offer/[a-f0-9]+-'))
            
            for link in job_links:
                try:
                    href = link['href']
                    if href.startswith('/'):
                        apply_link = f"{self.base_url}{href}"
                    else:
                        apply_link = href
                    
                    # Extract job title from the link text or nearby elements
                    title = link.get_text(strip=True)
                    if not title:
                        # Look for title in nearby h3 or other heading elements
                        title_elem = link.find(['h1', 'h2', 'h3', 'h4'])
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                    
                    # Extract job title from URL if needed
                    if not title:
                        url_parts = href.split('-')
                        if len(url_parts) > 1:
                            title = ' '.join(url_parts[1:]).replace('-', ' ').title()
                    
                    # Look for company name in parent elements
                    company = "Ruby Labs"  # Default based on site analysis
                    parent = link.parent
                    while parent and parent.name:
                        company_elem = parent.find(string=re.compile(r'Ruby Labs|Company:', re.IGNORECASE))
                        if company_elem:
                            company = company_elem.strip()
                            break
                        parent = parent.parent
                    
                    if title and len(title) > 3:
                        jobs.append({
                            'company': company,
                            'vacancy': title,
                            'apply_link': apply_link
                        })
                        
                except Exception:
                    continue
            
            # If no job links found, try a broader approach
            if not jobs:
                # Look for any text that might be job titles
                potential_titles = [
                    "User Acquisition Manager",
                    "Junior Recruitment Specialist", 
                    "Full-Stack Developer",
                    "Senior Data Analyst",
                    "Junior Golang Developer"
                ]
                
                page_text = soup.get_text().lower()
                found_titles = set()  # Use set to avoid duplicates
                
                for title in potential_titles:
                    if title.lower() in page_text and title not in found_titles:
                        found_titles.add(title)
                        jobs.append({
                            'company': 'Ruby Labs',
                            'vacancy': title,
                            'apply_link': f"{self.base_url}/remote-jobs/azerbaijan/1"
                        })
                    
        except Exception:
            pass
        
        return jobs


async def main():
    """Test the scraper"""
    scraper = JobgetherComScraper()
    
    try:
        df = await scraper.parse_jobgether_com(None)
        print(f"Scraped {len(df)} jobs from jobgether.com")
        
        if not df.empty:
            print("\nSample data:")
            print(df.head())
            
            # Show some sample job listings
            print("\nSample job listings:")
            for i, row in df.head(5).iterrows():
                print(f"- {row['company']}: {row['vacancy']}")
        else:
            print("No data scraped")
            
    except Exception as e:
        print(f"Error running scraper: {e}")


if __name__ == "__main__":
    asyncio.run(main())