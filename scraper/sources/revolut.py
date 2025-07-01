import logging
import pandas as pd
import asyncio
import re
import json
from typing import Optional
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class RevolutScraper(BaseScraper):
    """
    Revolut careers API scraper
    """
    
    BASE_URL = "https://www.revolut.com/_next/data"
    
    def __init__(self):
        super().__init__()
        self.build_id = None
    
    TEAM_SLUGS = [
        "business-development", "credit", "data", "engineering",
        "executive", "finance", "legal", "marketing-comms",
        "operations", "people-recruitment", "product-design",
        "risk-compliance-audit", "sales", "support-fin-crime"
    ]
    
    async def get_build_id(self, session) -> str:
        """
        Dynamically extract the Next.js build ID from Revolut's website
        """
        if self.build_id:
            return self.build_id
        
        logger.info("Extracting Revolut build ID dynamically")
        
        # Try multiple methods in order of reliability
        methods = [
            self._extract_from_ssg_manifest,
            self._extract_from_build_manifest,
            self._extract_from_next_data_urls,
            self._extract_from_script_tag
        ]
        
        for method in methods:
            try:
                build_id = await method(session)
                if build_id and await self._test_build_id(session, build_id):
                    self.build_id = build_id
                    logger.info(f"Found valid build ID: {build_id} via {method.__name__}")
                    return build_id
            except Exception as e:
                logger.warning(f"Method {method.__name__} failed: {e}")
                continue
        
        raise Exception("Could not extract valid build ID using any method")
    
    async def _extract_from_ssg_manifest(self, session) -> Optional[str]:
        """Extract build ID from _ssgManifest.js script tag (most reliable)"""
        response = await self.fetch_url_async("https://www.revolut.com/careers", session)
        if not response:
            return None
        
        pattern = r'/_next/static/([a-zA-Z0-9_-]+)/_ssgManifest\.js'
        matches = re.findall(pattern, response)
        return matches[0] if matches else None
    
    async def _extract_from_build_manifest(self, session) -> Optional[str]:
        """Extract build ID from _buildManifest.js script tag (second most reliable)"""
        response = await self.fetch_url_async("https://www.revolut.com/careers", session)
        if not response:
            return None
        
        pattern = r'/_next/static/([a-zA-Z0-9_-]+)/_buildManifest\.js'
        matches = re.findall(pattern, response)
        return matches[0] if matches else None
    
    async def _extract_from_next_data_urls(self, session) -> Optional[str]:
        """Extract build ID from _next/data URLs in page content"""
        response = await self.fetch_url_async("https://www.revolut.com/careers", session)
        if not response:
            return None
        
        pattern = r'/_next/data/([a-zA-Z0-9_-]+)/'
        matches = re.findall(pattern, response)
        
        # Test each unique build ID found
        for build_id in set(matches):
            if await self._test_build_id(session, build_id):
                return build_id
        return None
    
    async def _extract_from_script_tag(self, session) -> Optional[str]:
        """Extract from __NEXT_DATA__ script"""
        response = await self.fetch_url_async("https://www.revolut.com/careers", session)
        if not response:
            return None
        
        # Find and parse __NEXT_DATA__
        pattern = r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>'
        match = re.search(pattern, response, re.DOTALL)
        
        if match:
            try:
                next_data = json.loads(match.group(1))
                return next_data.get('buildId')
            except json.JSONDecodeError:
                pass
        return None
    
    async def _test_build_id(self, session, build_id: str) -> bool:
        """Validate build ID with test API call"""
        test_url = f"{self.BASE_URL}/{build_id}/en-GB/careers/team/engineering.json"
        try:
            response = await self.fetch_url_async(test_url, session, params={"slug": "engineering"}, timeout=5)
            return response is not None
        except:
            return False
    
    @scraper_error_handler
    async def scrape_revolut(self, session):
        """
        Scrape jobs from Revolut careers API
        """
        logger.info("Started scraping Revolut careers")
        
        all_jobs = []
        
        # Get build ID dynamically first
        try:
            build_id = await self.get_build_id(session)
            logger.info(f"Using build ID: {build_id}")
        except Exception as e:
            logger.error(f"Failed to get build ID: {e}")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
        
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
        if not self.build_id:
            raise Exception("Build ID not set. Call get_build_id() first.")
        
        url = f"{self.BASE_URL}/{self.build_id}/en-GB/careers/team/{team_slug}.json"
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