import logging
import pandas as pd
import json
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class PashapayScraper(BaseScraper):
    """
    PashaPay job scraper - fetches jobs from Huntflow API
    """
    
    @scraper_error_handler
    async def parse_pashapay(self, session):
        logger.info("Started scraping PashaPay careers via API")
        
        jobs_data = []
        page = 1
        
        try:
            # Headers for API requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Referer': 'https://pashapay.huntflow.io/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Cache-Control': 'no-cache'
            }
            
            # Fetch all pages of jobs
            while True:
                api_url = f"https://pashapay.huntflow.io/api/vacancy?preview=false&count=20&page={page}"
                
                try:
                    # Make direct API call to get JSON response
                    async with session.get(api_url, headers=headers) as response:
                        if response.status != 200:
                            logger.warning(f"API returned status {response.status} for page {page}")
                            break
                        
                        # Get JSON response directly
                        data = await response.json()
                        
                except Exception as e:
                    logger.error(f"Failed to fetch PashaPay API page {page}: {e}")
                    break
                
                # Check if we have items
                items = data.get('items', [])
                
                if not items:
                    break
                
                # Process each job item
                for job in items:
                    try:
                        # Skip archived jobs
                        if job.get('archived_at'):
                            continue
                        
                        position = (job.get('position') or '').strip()
                        slug = (job.get('slug') or '').strip()
                        city = (job.get('city') or '').strip()
                        division = (job.get('division') or '').strip()
                        
                        if not position or not slug:
                            continue
                        
                        # Build job title with location and division info
                        title_parts = [position]
                        
                        if city:
                            title_parts.append(f"({city})")
                        
                        if division:
                            title_parts.append(f"[{division}]")
                        
                        display_title = " ".join(title_parts)
                        
                        # Construct apply link from slug
                        apply_link = f"https://pashapay.huntflow.io/vacancy/{slug}"
                        
                        jobs_data.append({
                            'company': 'PashaPay',
                            'vacancy': display_title,
                            'apply_link': apply_link
                        })
                        
                    except Exception as e:
                        logger.warning(f"Error processing job item: {e}")
                        continue
                
                # Check pagination - if we got fewer items than requested (20), we're on the last page
                if len(items) < 20:
                    break
                
                page += 1
                
                # Safety limit to prevent infinite loops
                if page > 10:
                    logger.warning("Reached page limit (10), stopping pagination")
                    break
            
            if not jobs_data:
                logger.warning("No jobs found from PashaPay API")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            
            logger.info(f"Successfully scraped {len(jobs_data)} jobs from PashaPay API")
            return pd.DataFrame(jobs_data)
            
        except Exception as e:
            logger.error(f"Error scraping PashaPay API: {e}")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])