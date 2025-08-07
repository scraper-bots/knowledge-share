import logging
import pandas as pd
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class JobnetAzScraper(BaseScraper):
    """
    JobNet.az job scraper for job listings from api.jobnet.az API
    """
    
    @scraper_error_handler
    async def scrape_jobnet_az(self, session):
        """
        Scrape job listings from JobNet.az API for first 3 pages
        """
        api_url = "https://api.jobnet.az/api/v1/vacancies"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://jobnet.az/"
        }

        job_data = []
        max_pages = 3  # Scrape first 3 pages as requested

        for page in range(1, max_pages + 1):
            params = {'page': page}
            
            response = await self.fetch_url_async(api_url, session, params=params, headers=headers, verify_ssl=True)

            if not response:
                logger.error(f"Failed to fetch JobNet.az API data for page {page}")
                continue

            # Parse JSON response
            try:
                if isinstance(response, dict):
                    data = response
                elif isinstance(response, str):
                    import json
                    data = json.loads(response)
                else:
                    logger.error(f"Unexpected response format from JobNet.az API: {type(response)}")
                    continue
            except Exception as parse_error:
                logger.error(f"Error parsing JobNet.az API response: {str(parse_error)}")
                continue

            # Extract job data from the nested structure
            if 'data' not in data or not data['data']:
                logger.warning(f"No data found in JobNet.az API response for page {page}")
                continue
                
            api_data = data['data'][0] if isinstance(data['data'], list) else data['data']
            pagination_data = api_data.get('data', {})
            
            if 'data' not in pagination_data:
                logger.warning(f"No job listings found for page {page}")
                continue
                
            jobs = pagination_data['data']
            
            if not jobs:
                logger.info(f"No jobs found on page {page}")
                continue

            for job in jobs:
                try:
                    # Extract basic job information
                    job_id = job.get('id', 'n/a')
                    job_title = job.get('job_title', 'n/a')
                    slug = job.get('slug', '')
                    
                    # Extract employer information
                    employer_info = job.get('employer', {})
                    employer_name = employer_info.get('name', 'n/a')
                    
                    # Extract city information
                    city_info = job.get('city', {})
                    city_name = city_info.get('name', 'n/a')
                    
                    # Extract category information
                    category_info = job.get('category', {})
                    category_name = category_info.get('name', 'n/a')
                    parent_category = category_info.get('parent', {})
                    parent_category_name = parent_category.get('name', 'n/a') if parent_category else 'n/a'
                    
                    # Extract salary information
                    salary_min = job.get('salary_min')
                    salary_max = job.get('salary_max')
                    
                    # Build comprehensive job title
                    full_title = job_title
                    
                    # Add location if available
                    if city_name != 'n/a':
                        full_title = f"{full_title} - {city_name}"
                    
                    # Add category information
                    if parent_category_name != 'n/a' and category_name != 'n/a':
                        full_title = f"{full_title} ({parent_category_name}: {category_name})"
                    elif category_name != 'n/a':
                        full_title = f"{full_title} ({category_name})"
                    
                    # Add salary information if available
                    salary_parts = []
                    if salary_min and salary_min > 0:
                        salary_parts.append(f"{salary_min} AZN+")
                    elif salary_max and salary_max > 0:
                        salary_parts.append(f"up to {salary_max} AZN")
                    
                    if salary_min and salary_max and salary_min != salary_max:
                        salary_parts = [f"{salary_min}-{salary_max} AZN"]
                    
                    if salary_parts:
                        full_title = f"{full_title} | {salary_parts[0]}"
                    
                    # Build apply URL
                    if slug:
                        apply_url = f"https://jobnet.az/vacancy/{slug}"
                    else:
                        apply_url = f"https://jobnet.az/vacancy/{job_id}"
                    
                    # Extract additional info
                    views = job.get('viewed', 0)
                    if views and views > 50:  # Show popular jobs
                        full_title = f"{full_title} 🔥 {views} views"

                    job_data.append({
                        'company': employer_name,
                        'vacancy': full_title,
                        'apply_link': apply_url
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing JobNet.az job: {str(e)}")
                    continue

            logger.info(f"Scraped {len(jobs)} jobs from JobNet.az page {page}")

        df = pd.DataFrame(job_data)
        logger.info(f"JobNet.az scraping completed - total jobs: {len(job_data)} from {max_pages} pages")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])