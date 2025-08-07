import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class KabinetEhealthGovAzScraper(BaseScraper):
    """
    kabinet.e-health.gov.az job scraper for comprehensive healthcare positions
    
    NOTE: This site is a JavaScript-rendered SPA (Single Page Application) that loads
    job data dynamically via API calls. The getInterviewProgram API only contains
    interview programs/specializations, not actual job vacancies. The scraper attempts
    to find the correct job vacancy API endpoint, returning empty results if unavailable.
    """
    
    @scraper_error_handler
    async def scrape_kabinet_ehealth_gov_az(self, session):
        """
        Scrape job listings from kabinet.e-health.gov.az medical vacancy portal
        Attempts to find job vacancy API endpoints, returns empty results if unavailable
        """
        # Try multiple potential API endpoints for job vacancies
        api_endpoints = [
            "https://kabinet.e-health.gov.az/api/modul/miq/getVacancies",
            "https://kabinet.e-health.gov.az/api/modul/miq/vacancies",
            "https://kabinet.e-health.gov.az/api/modul/miq/getJobs",
            "https://kabinet.e-health.gov.az/api/modul/miq/getAllVacancies"
        ]
        
        base_url = "https://kabinet.e-health.gov.az/modul/miq/vacancies"
        
        # Headers based on the API request you provided
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6",
            "Referer": "https://kabinet.e-health.gov.az/modul/miq/vacancies",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }

        job_data = []
        
        # Try different API endpoints to find job vacancies
        for api_url in api_endpoints:
            logger.info(f"Trying API endpoint: {api_url}")
            response = await self.fetch_url_async(api_url, session, headers=headers, verify_ssl=True)
            
            if response:
                try:
                    # Parse API response
                    if isinstance(response, dict):
                        data = response
                    elif isinstance(response, str):
                        import json
                        data = json.loads(response)
                    else:
                        continue
                    
                    # Check if this looks like job vacancy data
                    if self._looks_like_vacancy_data(data):
                        logger.info(f"Found potential job data at: {api_url}")
                        job_data = self._parse_vacancy_data(data, base_url)
                        if job_data:
                            break
                        
                except Exception as e:
                    logger.debug(f"Error parsing response from {api_url}: {str(e)}")
                    continue

        if job_data:
            df = pd.DataFrame(job_data)
            logger.info(f"kabinet.e-health.gov.az API scraping completed - total jobs: {len(job_data)}")
            return df
        else:
            logger.info("No job vacancy API found. The getInterviewProgram endpoint only contains interview programs/specializations.")
            logger.info("No live job data available - returning empty DataFrame.")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
    
    def _looks_like_vacancy_data(self, data):
        """Check if the API response looks like job vacancy data rather than interview programs"""
        if not isinstance(data, dict):
            return False
            
        # Look for typical vacancy-related fields in the response
        vacancy_indicators = [
            'vacancies', 'jobs', 'positions', 'openings', 
            'institution', 'hospital', 'department', 'deadline',
            'applicationDeadline', 'startDate', 'endDate'
        ]
        
        data_str = str(data).lower()
        return any(indicator in data_str for indicator in vacancy_indicators)
    
    def _parse_vacancy_data(self, data, base_url):
        """Parse job vacancy data from API response"""
        job_data = []
        
        try:
            # Handle different possible API response structures
            jobs_list = []
            if isinstance(data, list):
                jobs_list = data
            elif isinstance(data, dict):
                if 'body' in data and isinstance(data['body'], list):
                    jobs_list = data['body']
                elif 'data' in data:
                    jobs_list = data['data'] if isinstance(data['data'], list) else [data['data']]
                elif 'items' in data:
                    jobs_list = data['items'] if isinstance(data['items'], list) else [data['items']]
                elif 'results' in data:
                    jobs_list = data['results'] if isinstance(data['results'], list) else [data['results']]

            for job in jobs_list:
                if not isinstance(job, dict):
                    continue
                
                # Extract job information from API response
                company = job.get('institution', job.get('company', job.get('employer', job.get('hospital', 'Medical Institution'))))
                position = job.get('position', job.get('title', job.get('vacancy', job.get('name', 'Medical Position'))))
                department = job.get('department', job.get('sector', job.get('unit', '')))
                specialty = job.get('specialty', job.get('specialization', job.get('field', '')))
                interview_type = job.get('interviewType', job.get('interview', 'Ümumi müsahibə'))
                end_date = job.get('endDate', job.get('deadline', job.get('applicationDeadline', '')))
                
                # Build comprehensive job title
                title_parts = [str(position)]
                
                if department:
                    title_parts.append(f"({department})")
                
                if specialty:
                    title_parts.append(f"[{specialty}]")
                
                if interview_type and interview_type != 'n/a':
                    title_parts.append(f"- {interview_type}")
                
                if end_date:
                    deadline_text = str(end_date)
                    if len(deadline_text) > 10:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(deadline_text.replace('Z', '+00:00'))
                            deadline_text = dt.strftime('%d.%m.%Y')
                        except:
                            deadline_text = deadline_text[:10] if len(deadline_text) >= 10 else deadline_text
                    
                    title_parts.append(f"(Deadline: {deadline_text})")
                
                final_title = ' '.join(title_parts)
                
                # Clean up company name
                company_str = str(company).replace('"', '').replace('publik hüquqi şəxsi', '').strip()
                
                job_data.append({
                    'company': company_str,
                    'vacancy': final_title,
                    'apply_link': base_url
                })
                
        except Exception as e:
            logger.error(f"Error parsing vacancy data: {str(e)}")
            
        return job_data

