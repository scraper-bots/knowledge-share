import asyncio
import json
import logging
import pandas as pd
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class GlorriScraper(BaseScraper):
    """
    Glorri job scraper with comprehensive error handling and modern headers
    """
    
    @scraper_error_handler
    async def parse_glorri(self, session):
        """
        Glorri job scraper with comprehensive error handling and modern headers
        """
        logger.info("Started scraping Glorri")
        
        # API endpoints
        companies_url = "https://atsapp.glorri.com/user-service-v2/companies/public"
        jobs_url = "https://atsapp.glorri.az/job-service-v2/jobs/company/{}/public"
        
        # Modern browser-like headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://jobs.glorri.az',
            'Referer': 'https://jobs.glorri.az/',
            'Connection': 'keep-alive',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        try:
            jobs = []
            offset = 0
            limit = 20
            max_retries = 3
            retry_delay = 2
            
            while True:
                # Fetch companies with pagination and retry logic
                companies_params = {
                    'limit': limit,
                    'offset': offset
                }
                
                companies_response = None
                for retry in range(max_retries):
                    try:
                        logger.info(f"Fetching companies with offset {offset} (Attempt {retry + 1}/{max_retries})")
                        companies_response = await self.fetch_url_async(
                            companies_url, 
                            session, 
                            params=companies_params,
                            headers=headers,
                            verify_ssl=False
                        )
                        
                        if companies_response:
                            break
                        
                        logger.warning(f"Attempt {retry + 1} failed, retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay * (retry + 1))
                        
                    except Exception as e:
                        logger.error(f"Error during company fetch attempt {retry + 1}: {str(e)}")
                        if retry < max_retries - 1:
                            await asyncio.sleep(retry_delay * (retry + 1))
                        else:
                            logger.error("Max retries exceeded for company fetch")
                            break
                
                if not companies_response:
                    logger.error(f"Failed to fetch companies at offset {offset} after all retries")
                    break
                    
                try:
                    if isinstance(companies_response, str):
                        companies_response = json.loads(companies_response)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse companies response at offset {offset}: {str(e)}")
                    break
                
                companies = companies_response.get('entities', [])
                if not companies:
                    break
                    
                total_companies = companies_response.get('totalCount', 0)
                logger.info(f"Processing {len(companies)} companies (Total: {total_companies})")
                
                # Process each company's jobs
                for company in companies:
                    company_name = company.get('name')
                    company_slug = company.get('slug')
                    job_count = company.get('jobCount', 0)
                    
                    if not company_slug:
                        continue
                        
                    logger.info(f"Fetching jobs for {company_name} (Expected: {job_count} jobs)")
                    
                    # Fetch jobs with pagination
                    job_skip = 0
                    job_limit = 18
                    
                    while True:
                        company_jobs_url = jobs_url.format(company_slug)
                        jobs_params = {
                            'skip': job_skip,
                            'limit': job_limit
                        }
                        
                        # Add retry logic for job fetching
                        jobs_response = None
                        for retry in range(max_retries):
                            try:
                                jobs_response = await self.fetch_url_async(
                                    company_jobs_url,
                                    session,
                                    params=jobs_params,
                                    headers=headers,
                                    verify_ssl=False
                                )
                                
                                if jobs_response:
                                    break
                                    
                                logger.warning(f"Job fetch attempt {retry + 1} failed, retrying...")
                                await asyncio.sleep(retry_delay * (retry + 1))
                                
                            except Exception as e:
                                logger.error(f"Error during job fetch attempt {retry + 1}: {str(e)}")
                                if retry < max_retries - 1:
                                    await asyncio.sleep(retry_delay * (retry + 1))
                                else:
                                    logger.error("Max retries exceeded for job fetch")
                                    break
                        
                        if not jobs_response:
                            logger.warning(f"No jobs response for {company_name} at skip {job_skip} after all retries")
                            break
                            
                        try:
                            if isinstance(jobs_response, str):
                                jobs_response = json.loads(jobs_response)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse jobs response for {company_name}: {str(e)}")
                            break
                        
                        company_jobs = jobs_response.get('entities', [])
                        if not company_jobs:
                            break
                        
                        for job in company_jobs:
                            jobs.append({
                                'company': company_name,
                                'vacancy': job.get('title', 'Unknown Position'),
                                'apply_link': f"https://jobs.glorri.az/vacancies/{company_slug}/{job.get('slug')}/apply"
                            })
                        
                        logger.info(f"Fetched {len(company_jobs)} jobs for {company_name} (batch starting at {job_skip})")
                        
                        if len(company_jobs) < job_limit:
                            break
                        
                        job_skip += job_limit
                        await asyncio.sleep(1)  # Rate limiting between job batches
                
                offset += limit
                if offset >= total_companies:
                    break
                
                await asyncio.sleep(2)  # Rate limiting between company batches
            
            total_jobs = len(jobs)
            logger.info(f"Completed scraping Glorri. Found {total_jobs} total jobs")
            
            return pd.DataFrame(jobs) if jobs else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            
        except Exception as e:
            logger.error(f"Unexpected error in Glorri scraper: {str(e)}")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

