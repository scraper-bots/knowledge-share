import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class IseqebulAzScraper(BaseScraper):
    """
    iseqebul.az job scraper for administrative positions
    Scrapes from administrative staff job category with AJAX pagination support
    """
    
    @scraper_error_handler
    async def scrape_iseqebul_az(self, session):
        """
        Scrape job listings from iseqebul.az administrative positions category
        Supports AJAX pagination to get multiple pages of results
        """
        base_url = "https://iseqebul.az/job-category/inzibati-heyet/"
        ajax_url = "https://iseqebul.az/wp-admin/admin-ajax.php"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,az;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        job_data = []
        max_pages = 5  # Limit to avoid overwhelming requests
        
        # First, get the initial page to extract pagination parameters
        logger.info("Fetching initial page from iseqebul.az...")
        response = await self.fetch_url_async(base_url, session, headers=headers, verify_ssl=True)

        if not response:
            logger.error("Failed to fetch initial page from iseqebul.az")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

        # Parse initial page
        initial_jobs = self._parse_job_listings(response, base_url)
        job_data.extend(initial_jobs)
        logger.info(f"Scraped {len(initial_jobs)} jobs from initial page")

        # Extract pagination parameters from initial page
        soup = BeautifulSoup(response, 'html.parser')
        pagination_div = soup.find('div', class_='felan-pagination ajax-call')
        
        if not pagination_div:
            logger.info("No pagination found, returning initial results")
            return self._create_dataframe(job_data)
        
        # Extract pagination parameters
        paged_input = pagination_div.find('input', {'name': 'paged'})
        current_term_input = pagination_div.find('input', {'name': 'current_term'})
        type_term_input = pagination_div.find('input', {'name': 'type_term'})
        
        if not all([paged_input, current_term_input, type_term_input]):
            logger.warning("Could not extract pagination parameters, returning initial results")
            return self._create_dataframe(job_data)
        
        current_term = current_term_input.get('value', '285')
        type_term = type_term_input.get('value', 'jobs-categories')
        
        # Headers for AJAX requests
        ajax_headers = {
            **headers,
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": base_url,
            "Origin": "https://iseqebul.az"
        }
        
        # Load additional pages via AJAX POST requests
        for page in range(2, max_pages + 1):
            try:
                # Prepare AJAX request data
                ajax_data = {
                    'action': 'felan_archive_loadmore',
                    'paged': str(page),
                    'current_term': current_term,
                    'type_term': type_term,
                    'post_type': 'jobs',
                    'posts_per_page': '15'
                }
                
                logger.info(f"Fetching page {page} via AJAX POST...")
                
                # Use aiohttp directly for POST request since fetch_url_async doesn't support POST
                async with session.post(
                    ajax_url,
                    data=ajax_data,
                    headers=ajax_headers,
                    ssl=True
                ) as ajax_resp:
                    if ajax_resp.status == 200:
                        ajax_content = await ajax_resp.text()
                        
                        # Parse AJAX response - it should contain HTML for new job items
                        page_jobs = self._parse_job_listings(ajax_content, base_url)
                        
                        if not page_jobs:
                            logger.info(f"No more jobs found on page {page}, stopping")
                            break
                        
                        job_data.extend(page_jobs)
                        logger.info(f"Scraped {len(page_jobs)} jobs from AJAX page {page}")
                    else:
                        logger.warning(f"AJAX request failed with status {ajax_resp.status} for page {page}")
                        break
                
            except Exception as e:
                logger.error(f"Error fetching AJAX page {page}: {str(e)}")
                break
        
        return self._create_dataframe(job_data)
    
    def _parse_job_listings(self, html_content, base_url):
        """Parse job listings from HTML content"""
        jobs = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all job items
            job_items = soup.find_all('div', class_='felan-jobs-item')
            
            for item in job_items:
                try:
                    # Extract company info
                    company_link = item.find('a', class_='authour')
                    company = company_link.text.strip() if company_link else 'Unknown Company'
                    
                    # Extract job title and URL
                    job_title_link = item.find('h3', class_='jobs-title')
                    if job_title_link:
                        title_anchor = job_title_link.find('a')
                        if title_anchor:
                            job_title = title_anchor.text.strip()
                            apply_link = title_anchor.get('href', base_url)
                        else:
                            continue
                    else:
                        continue
                    
                    # Extract location
                    location_link = item.find('a', class_='cate-location')
                    location = location_link.text.strip() if location_link else ''
                    
                    # Extract job type
                    job_type_link = item.find('a', class_='cate-type')
                    job_type = job_type_link.text.strip() if job_type_link else ''
                    
                    # Extract salary
                    price_div = item.find('div', class_='price')
                    salary = price_div.text.strip() if price_div else ''
                    
                    # Extract days remaining
                    days_elem = item.find('p', class_='days')
                    days_remaining = ''
                    if days_elem:
                        days_span = days_elem.find('span')
                        if days_span:
                            days_remaining = days_span.text.strip() + ' gün qalıb'
                    
                    # Check if urgent
                    is_urgent = item.find('span', class_='tooltip urgent') is not None
                    
                    # Build comprehensive job title
                    title_parts = [job_title]
                    
                    if location:
                        title_parts.append(f"({location})")
                    
                    if job_type and job_type != 'Full time':  # Don't show full time as it's common
                        title_parts.append(f"[{job_type}]")
                    
                    if salary:
                        title_parts.append(f"- {salary}")
                    
                    if days_remaining:
                        title_parts.append(f"({days_remaining})")
                    
                    if is_urgent:
                        title_parts.append("🔥 URGENT")
                    
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
            logger.info(f"iseqebul.az scraping completed - total jobs: {len(job_data)}")
            return df
        else:
            logger.info("No jobs found from iseqebul.az")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])