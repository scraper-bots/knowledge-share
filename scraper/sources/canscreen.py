import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class CanscreenScraper(BaseScraper):
    """
    CanScreen job scraper
    """
    
    @scraper_error_handler
    async def scrape_canscreen(self, session):
        """
        Scrape vacancies from the CanScreen API with dynamic build ID handling.
        """
        # First, fetch the main page to get the current build ID
        base_url = "https://canscreen.io"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        
        try:
            # Get the main page first
            async with session.get(f"{base_url}/en/vacancies", headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch main page. Status code: {response.status}")
                    return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
                
                html_content = await response.text()
                
                # Extract the build ID from the page
                # Look for the script containing __NEXT_DATA__
                import re
                build_id_match = re.search(r'"buildId":"([^"]+)"', html_content)
                
                if not build_id_match:
                    logger.error("Could not find build ID in the page")
                    return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
                    
                build_id = build_id_match.group(1)
                
                # Now construct the API URL with the current build ID
                api_url = f"{base_url}/_next/data/{build_id}/en/vacancies.json"
                
                # Fetch the actual vacancy data
                async with session.get(api_url, headers=headers) as api_response:
                    if api_response.status == 200:
                        data = await api_response.json()
                        vacancies = data.get('pageProps', {}).get('vacancies', [])
                        
                        jobs = []
                        for vacancy in vacancies:
                            jobs.append({
                                'company': vacancy.get('company', 'Unknown'),
                                'vacancy': vacancy.get('title', 'Unknown'),
                                'apply_link': f"{base_url}/vacancies/{vacancy.get('id')}/"
                            })
                        
                        return pd.DataFrame(jobs)
                    else:
                        logger.error(f"Failed to fetch vacancy data. Status: {api_response.status}")
                        return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
                        
        except Exception as e:
            logger.error(f"Error in CanScreen scraper: {str(e)}")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])