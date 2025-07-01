import logging
import pandas as pd
import asyncio
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class RevolutScraper(BaseScraper):
    """
    Revolut careers API scraper
    """
    
    BASE_URL = "https://www.revolut.com/_next/data"
    BUILD_ID = "hqlIjzBKE4aut5_VDl56J"  # May need updates
    
    TEAM_SLUGS = [
        "business-development", "credit", "data", "engineering",
        "executive", "finance", "legal", "marketing-comms",
        "operations", "people-recruitment", "product-design",
        "risk-compliance-audit", "sales", "support-fin-crime"
    ]
    
    @scraper_error_handler
    async def scrape_revolut(self, session):
        """
        Scrape jobs from Revolut careers API
        """
        logger.info("Started scraping Revolut careers")
        
        all_jobs = []
        
        for team_slug in self.TEAM_SLUGS:
            try:
                jobs = await self._scrape_team(session, team_slug)
                all_jobs.extend(jobs)
                logger.info(f"Scraped {len(jobs)} jobs from {team_slug}")
                
                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error scraping team {team_slug}: {str(e)}")
                continue
        
        logger.info(f"Successfully scraped {len(all_jobs)} total jobs from Revolut")
        return pd.DataFrame(all_jobs) if all_jobs else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
    
    async def _scrape_team(self, session, team_slug):
        """
        Scrape jobs for a specific team
        """
        url = f"{self.BASE_URL}/{self.BUILD_ID}/en-GB/careers/team/{team_slug}.json"
        params = {"slug": team_slug}
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'https://www.revolut.com/careers/team/{team_slug}',
            'Cache-Control': 'no-cache'
        }
        
        response = await self.fetch_url_async(url, session, headers=headers, params=params)
        if not response:
            logger.warning(f"Failed to fetch data for team: {team_slug}")
            return []
        
        try:
            import json
            data = json.loads(response)
            return self._extract_jobs(data, team_slug)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for team {team_slug}: {str(e)}")
            return []
    
    def _extract_jobs(self, api_response, team_slug):
        """
        Extract job listings from API response
        """
        try:
            positions = api_response.get("pageProps", {}).get("positions", [])
            team_info = api_response.get("pageProps", {}).get("page", {})
            team_name = team_info.get("meta", {}).get("title", team_slug.replace('-', ' ').title())
            
            jobs = []
            for position in positions:
                # Handle multiple locations per job
                locations = position.get("locations", [])
                if not locations:
                    # If no locations specified, create one entry anyway
                    locations = [{"name": "Not specified", "type": "office", "country": ""}]
                
                for location in locations:
                    # Create individual job entry for each location
                    job_title = position.get("text", "Unknown Position")
                    location_name = location.get("name", "Not specified")
                    work_type = location.get("type", "office")
                    country = location.get("country", "")
                    
                    # Create display title with location info
                    if location_name != "Not specified":
                        if work_type == "remote":
                            title_with_location = f"{job_title} - {location_name} (Remote)"
                        else:
                            title_with_location = f"{job_title} - {location_name}"
                    else:
                        title_with_location = job_title
                    
                    # Construct apply link
                    job_id = position.get("id", "")
                    apply_link = f"https://www.revolut.com/careers/position/{job_id}" if job_id else f"https://www.revolut.com/careers/team/{team_slug}"
                    
                    job = {
                        'company': 'Revolut',
                        'vacancy': title_with_location,
                        'apply_link': apply_link
                    }
                    jobs.append(job)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error extracting jobs from API response: {str(e)}")
            return []