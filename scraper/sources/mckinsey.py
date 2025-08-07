import logging
import pandas as pd
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class McKinseyScraper(BaseScraper):
    """
    McKinsey job scraper for job listings from mckapi.mckinsey.com API
    """
    
    @scraper_error_handler
    async def scrape_mckinsey(self, session):
        """
        Scrape job listings from McKinsey API for Baku positions
        Returns empty results if API is not accessible
        """
        # Try the API approach first
        api_url = "https://mckapi.mckinsey.com/api/jobsearch"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.mckinsey.com/careers/search-jobs?cities=Baku",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache"
        }

        job_data = []
        page_size = 20
        start = 1

        # Try to fetch from API with timeout and retry handling
        try:
            params = {
                'pageSize': page_size,
                'start': start,
                'cities': 'Baku',
                'lang': 'en'
            }
            
            response = await self.fetch_url_async(api_url, session, params=params, headers=headers, verify_ssl=True, max_retries=2)

            if not response:
                logger.warning("McKinsey API not accessible, no job data available")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
                
        except Exception as api_error:
            logger.warning(f"McKinsey API failed ({str(api_error)}), no job data available")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

        # Process API response if successful
        try:
            # The API returns JSON directly
            if isinstance(response, dict):
                data = response
            elif isinstance(response, str):
                import json
                data = json.loads(response)
            else:
                logger.warning(f"Unexpected response format from McKinsey API: {type(response)}, no job data available")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

            if data.get('status') != 'OK':
                logger.warning(f"API returned status: {data.get('status', 'Unknown')}, no job data available")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

            docs = data.get('docs', [])
            if not docs:
                logger.info("No jobs found from McKinsey API, no job data available")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

            # Process successful API response
            for job in docs:
                try:
                    # Extract job details
                    job_id = job.get('jobID', 'n/a')
                    title = job.get('title', 'n/a')
                    interest = job.get('interest', 'n/a')
                    
                    # Get job application URL
                    apply_url = job.get('jobApplyURL', '')
                    if not apply_url and job_id != 'n/a':
                        apply_url = f"https://mckinsey.avature.net/careers/ApplicationMethods?folderId={job_id}"
                    
                    # Build comprehensive job title with additional context
                    full_title = title
                    if interest != 'n/a' and interest != title:
                        full_title = f"{title} ({interest})"
                    
                    # Add salary information if available
                    salary_info = job.get('compensationRange', job.get('jobSalaryBenefits', ''))
                    if salary_info and salary_info not in ['n/a', '']:
                        full_title = f"{full_title} - {salary_info}"
                    
                    # Get cities list to show if job is available in multiple locations
                    cities = job.get('cities', [])
                    if isinstance(cities, list) and len(cities) > 1:
                        if 'Baku' in cities:
                            other_cities = [city for city in cities[:5] if city != 'Baku']
                            if other_cities:
                                cities_str = ', '.join(other_cities)
                                if len(cities) > 5:
                                    cities_str += f' (+{len(cities) - 5} more)'
                                full_title = f"{full_title} | Also: {cities_str}"

                    job_data.append({
                        'company': 'McKinsey & Company',
                        'vacancy': full_title,
                        'apply_link': apply_url
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing McKinsey job: {str(e)}")
                    continue

            logger.info(f"Scraped {len(docs)} jobs from McKinsey API")
            
        except Exception as processing_error:
            logger.warning(f"Error processing McKinsey API response: {str(processing_error)}, no job data available")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

        if job_data:
            df = pd.DataFrame(job_data)
            logger.info(f"McKinsey scraping completed - total jobs: {len(job_data)}")
            return df
        else:
            logger.info("No jobs from API, no job data available")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

