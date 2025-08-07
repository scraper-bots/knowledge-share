import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class AzjobAzScraper(BaseScraper):
    """
    azjob.az job scraper for various job categories
    Scrapes job listings with URL-based pagination support
    """
    
    @scraper_error_handler
    async def scrape_azjob_az(self, session):
        """
        Scrape job listings from azjob.az with pagination
        Uses start parameter for page navigation
        """
        base_url = "https://azjob.az/homelist/"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,az;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }

        job_data = []
        max_pages = 15  # Reasonable limit
        jobs_per_page = 20  # Estimated based on typical job board pagination
        
        for page in range(max_pages):
            start_param = page * jobs_per_page  # Calculate start parameter
            
            # Build URL with start parameter
            if start_param == 0:
                url = base_url  # First page without start parameter
            else:
                url = f"{base_url}?start={start_param}"
            
            logger.info(f"Fetching azjob.az page {page + 1} (start={start_param})")
            response = await self.fetch_url_async(url, session, headers=headers, verify_ssl=True)

            if not response:
                logger.error(f"Failed to fetch page {page + 1} from azjob.az")
                break

            # Parse job listings from this page
            page_jobs = self._parse_job_listings(response)
            
            if not page_jobs:
                logger.info(f"No jobs found on page {page + 1}, stopping pagination")
                break
            
            job_data.extend(page_jobs)
            logger.info(f"Scraped {len(page_jobs)} jobs from azjob.az page {page + 1}")
            
            # If we got less than expected jobs per page, we might be at the end
            if len(page_jobs) < jobs_per_page:
                logger.info(f"Got {len(page_jobs)} jobs (less than {jobs_per_page}), likely last page")
                break
        
        return self._create_dataframe(job_data)
    
    def _parse_job_listings(self, html_content):
        """Parse job listings from HTML content"""
        jobs = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all job items using the class structure from the provided HTML
            job_divs = soup.find_all('div', class_='jobdiv')
            
            if not job_divs:
                logger.warning("No job divs found with class 'jobdiv'")
                return jobs
            
            for job_div in job_divs:
                try:
                    # Extract job title and link
                    job_full = job_div.find('div', class_='job_full')
                    if not job_full:
                        continue
                    
                    # Get job title and apply link
                    title_link = job_full.find('h3')
                    if title_link:
                        anchor = title_link.find('a')
                        if anchor:
                            job_title = anchor.text.strip()
                            job_href = anchor.get('href', '')
                            
                            # Build full URL
                            if job_href.startswith('/'):
                                apply_link = f"https://azjob.az{job_href}"
                            elif job_href.startswith('http'):
                                apply_link = job_href
                            else:
                                apply_link = f"https://azjob.az/{job_href}"
                        else:
                            continue
                    else:
                        continue
                    
                    # Extract company/user info
                    job_user_div = job_full.find('div', class_='job_user')
                    company = job_user_div.text.strip() if job_user_div else 'Unknown Company'
                    
                    # Extract additional info (date and location)
                    job_addons_div = job_full.find('div', class_='job_addons')
                    location = ''
                    post_date = ''
                    
                    if job_addons_div:
                        addons_text = job_addons_div.get_text()
                        
                        # Common Azerbaijan city names
                        cities = [
                            'Bakı', 'Gəncə', 'Sumqayıt', 'Mingəçevir', 'Quba', 'Lənkəran', 
                            'Şəki', 'Yevlax', 'Naxçıvan', 'Şamaxı', 'Qəbələ', 'Xaçmaz',
                            'Bərdə', 'Ağdaş', 'Şirvan', 'Zaqatala', 'Qazax', 'Salyan',
                            'Şabran', 'Masallı', 'İsmayıllı', 'Ağsu', 'Göyçay'
                        ]
                        
                        # Extract location by checking for known cities
                        for city in cities:
                            if city in addons_text:
                                location = city
                                break
                        
                        if not location:
                            # Try to extract any location after splitting by common separators
                            import re
                            parts = re.split(r'&nbsp;|\s+', addons_text)
                            for part in reversed(parts):  # Check from end
                                clean_part = part.strip()
                                if clean_part and len(clean_part) > 2 and clean_part.isalpha():
                                    location = clean_part
                                    break
                        
                        # Extract date (after time icon, before location)
                        date_parts = addons_text.split('&nbsp;')
                        if len(date_parts) > 0:
                            # Date is typically the first part after the time icon
                            date_part = date_parts[0].strip()
                            if any(char.isdigit() for char in date_part):
                                post_date = date_part
                    
                    # Extract job category info from avatar
                    job_avatar = job_div.find('div', class_='job_avatar')
                    category_info = ''
                    if job_avatar:
                        avatar_classes = job_avatar.get('class', [])
                        for cls in avatar_classes:
                            if cls.startswith('jobcat_'):
                                category_info = f"Category: {cls}"
                                break
                    
                    # Build comprehensive job title
                    title_parts = [job_title]
                    
                    if location:
                        title_parts.append(f"({location})")
                    
                    if post_date:
                        title_parts.append(f"- Posted: {post_date}")
                    
                    if category_info:
                        title_parts.append(f"[{category_info}]")
                    
                    final_title = ' '.join(title_parts)
                    
                    jobs.append({
                        'company': company,
                        'vacancy': final_title,
                        'apply_link': apply_link
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing individual job item: {str(e)}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error parsing job listings: {str(e)}")
            return []
    
    def _create_dataframe(self, job_data):
        """Create and return pandas DataFrame from job data"""
        if job_data:
            df = pd.DataFrame(job_data)
            logger.info(f"azjob.az scraping completed - total jobs: {len(job_data)}")
            return df
        else:
            logger.info("No jobs found from azjob.az")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])