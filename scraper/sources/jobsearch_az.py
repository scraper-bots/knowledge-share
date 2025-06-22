import logging
import pandas as pd
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class JobsearchAzScraper(BaseScraper):
    """
    Jobsearch.az job scraper
    """
    
    @scraper_error_handler
    async def parse_jobsearch_az(self, session):
        """Fetch job data from Jobsearch.az and return a DataFrame."""
        # Initial request to obtain cookies
        initial_url = "https://www.jobsearch.az"
        
        # Perform an initial request to the homepage to set up cookies in the session
        async with session.get(initial_url) as initial_response:
            if initial_response.status != 200:
                logger.error(f"Failed to obtain initial cookies: {initial_response.status}")
                return pd.DataFrame(columns=['vacancy', 'company', 'apply_link'])
            
            # Session cookies are now set and can be used in subsequent requests

        # Base URL for the API request
        base_url = "https://www.jobsearch.az/api-az/vacancies-az"
        params = {
            'hl': 'az',
            'q': '',
            'posted_date': '',
            'seniority': '',
            'categories': '',
            'industries': '',
            'ads': '',
            'location': '',
            'job_type': '',
            'salary': '',
            'order_by': ''
        }

        # Headers for the request
        headers = {
            'authority': 'www.jobsearch.az',
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6',
            'dnt': '1',
            'priority': 'u=1, i',
            'referer': 'https://www.jobsearch.az/vacancies',
            'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }

        # List to hold job data
        job_listings = []

        # Initialize page counter
        page_count = 0

        # Loop to fetch and process up to 5 pages
        while page_count < 5:
            async with session.get(base_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()

                    # Process each job in the current page
                    for job in data.get('items', []):
                        job_listings.append({
                            "vacancy": job['title'],
                            "company": job['company']['title'],
                            "apply_link": f"https://www.jobsearch.az/vacancies/{job['slug']}"
                        })

                    # Check if there is a next page URL
                    if 'next' in data:
                        next_page_url = data['next']
                        base_url = next_page_url
                        params = {}  # Reset params since the next page URL includes all parameters
                        page_count += 1  # Increment page counter
                    else:
                        break  # No more pages, exit the loop
                else:
                    logger.error(f"Failed to retrieve data: {response.status}")
                    break

        # Convert the list of jobs to a DataFrame
        df = pd.DataFrame(job_listings, columns=['vacancy', 'company', 'apply_link'])
        return df