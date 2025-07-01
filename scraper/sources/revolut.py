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
    Revolut careers API scraper with dynamic build ID extraction
    """
    
    BASE_URL = "https://www.revolut.com/_next/data"
    
    TEAM_SLUGS = [
        "business-development", "credit", "data", "engineering",
        "executive", "finance", "legal", "marketing-comms",
        "operations", "people-recruitment", "product-design",
        "risk-compliance-audit", "sales", "support-fin-crime"
    ]
    
    def __init__(self):
        super().__init__()
        self.build_id = None
    
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
            self._extract_from_script_tag,
            self._extract_from_homepage,
            self._try_common_build_ids
        ]
        
        for method in methods:
            try:
                build_id = await method(session)
                if build_id and await self._test_build_id(session, build_id):
                    self.build_id = build_id
                    logger.info(f"Found valid build ID: {build_id} via {method.__name__}")
                    return build_id
                elif build_id:
                    logger.warning(f"Build ID {build_id} from {method.__name__} failed validation")
            except Exception as e:
                logger.warning(f"Method {method.__name__} failed: {e}")
                continue
        
        raise Exception("Could not extract valid build ID using any method")
    
    async def _extract_from_ssg_manifest(self, session) -> Optional[str]:
        """Extract build ID from _ssgManifest.js script tag (most reliable)"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = await self.fetch_url_async("https://www.revolut.com/careers", session, headers=headers, timeout=20)
        if not response:
            logger.warning("Failed to fetch Revolut careers page for build ID extraction")
            return None
        
        logger.info(f"Revolut careers page response length: {len(response)}")
        
        # Check if we got the right page
        if 'careers' not in response.lower() and 'revolut' not in response.lower():
            logger.warning("Response doesn't look like Revolut careers page - might be blocked/redirected")
            logger.debug(f"Response start: {response[:500]}")
        
        # Multiple patterns to try
        patterns = [
            r'/_next/static/([a-zA-Z0-9_-]+)/_ssgManifest\.js',
            r'/static/([a-zA-Z0-9_-]+)/_ssgManifest\.js',
            r'_next/static/([a-zA-Z0-9_-]+)/_ssgManifest\.js'
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, response)
            logger.info(f"SSG Pattern {i+1}: {len(matches)} matches found")
            if matches:
                logger.info(f"Found build ID from SSG manifest pattern {i+1}: {matches[0]}")
                return matches[0]
        
        # Look for any _next references for debugging
        next_refs = re.findall(r'_next/[^"\s]+', response)
        logger.info(f"Found {len(next_refs)} _next references: {next_refs[:5]}")
        
        return None
    
    async def _extract_from_build_manifest(self, session) -> Optional[str]:
        """Extract build ID from _buildManifest.js script tag (second most reliable)"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        response = await self.fetch_url_async("https://www.revolut.com/careers", session, headers=headers)
        if not response:
            logger.warning("Failed to fetch Revolut careers page for build manifest")
            return None
        
        # Multiple patterns to try
        patterns = [
            r'/_next/static/([a-zA-Z0-9_-]+)/_buildManifest\.js',
            r'/static/([a-zA-Z0-9_-]+)/_buildManifest\.js',
            r'_next/static/([a-zA-Z0-9_-]+)/_buildManifest\.js'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response)
            if matches:
                logger.info(f"Found build ID from build manifest: {matches[0]}")
                return matches[0]
        
        return None
    
    async def _extract_from_next_data_urls(self, session) -> Optional[str]:
        """Extract build ID from _next/data URLs in page content"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        response = await self.fetch_url_async("https://www.revolut.com/careers", session, headers=headers)
        if not response:
            logger.warning("Failed to fetch Revolut careers page for data URLs")
            return None
        
        patterns = [
            r'/_next/data/([a-zA-Z0-9_-]+)/',
            r'/data/([a-zA-Z0-9_-]+)/',
            r'_next/data/([a-zA-Z0-9_-]+)/'
        ]
        
        all_matches = []
        for pattern in patterns:
            matches = re.findall(pattern, response)
            all_matches.extend(matches)
        
        # Test each unique build ID found
        for build_id in set(all_matches):
            logger.info(f"Testing build ID from data URLs: {build_id}")
            if await self._test_build_id(session, build_id):
                logger.info(f"Found valid build ID from data URLs: {build_id}")
                return build_id
        return None
    
    async def _extract_from_script_tag(self, session) -> Optional[str]:
        """Extract from __NEXT_DATA__ script"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        response = await self.fetch_url_async("https://www.revolut.com/careers", session, headers=headers)
        if not response:
            logger.warning("Failed to fetch Revolut careers page for script tag")
            return None
        
        logger.info(f"Script tag response length: {len(response)}")
        
        # Try multiple patterns for Next.js data
        patterns = [
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            r'"buildId":"([a-zA-Z0-9_-]+)"',
            r'buildId\s*:\s*"([a-zA-Z0-9_-]+)"'
        ]
        
        for i, pattern in enumerate(patterns):
            if i == 0:  # First pattern returns JSON
                match = re.search(pattern, response, re.DOTALL)
                logger.info(f"Script pattern {i+1}: {'Match found' if match else 'No match'}")
                if match:
                    try:
                        next_data = json.loads(match.group(1))
                        build_id = next_data.get('buildId')
                        if build_id:
                            logger.info(f"Found build ID from __NEXT_DATA__: {build_id}")
                            return build_id
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse __NEXT_DATA__ JSON: {e}")
            else:  # Other patterns return build ID directly
                matches = re.findall(pattern, response)
                logger.info(f"Script pattern {i+1}: {len(matches)} matches found")
                if matches:
                    build_id = matches[0]
                    logger.info(f"Found build ID from pattern {i+1}: {build_id}")
                    return build_id
        
        # Debug: look for any script tags
        script_tags = re.findall(r'<script[^>]*>', response)
        logger.info(f"Found {len(script_tags)} script tags total")
        
        return None
    
    async def _extract_from_homepage(self, session) -> Optional[str]:
        """Extract build ID from Revolut homepage instead of careers page"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        response = await self.fetch_url_async("https://www.revolut.com", session, headers=headers, timeout=20)
        if not response:
            logger.warning("Failed to fetch Revolut homepage")
            return None
        
        logger.info(f"Homepage response length: {len(response)}")
        
        # Try all patterns on homepage
        patterns = [
            r'/_next/static/([a-zA-Z0-9_-]+)/_ssgManifest\.js',
            r'/_next/static/([a-zA-Z0-9_-]+)/_buildManifest\.js',
            r'/_next/data/([a-zA-Z0-9_-]+)/',
            r'"buildId":"([a-zA-Z0-9_-]+)"'
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, response)
            logger.info(f"Homepage pattern {i+1}: {len(matches)} matches")
            if matches:
                logger.info(f"Found build ID from homepage pattern {i+1}: {matches[0]}")
                return matches[0]
        
        return None
    
    async def _try_common_build_ids(self, session) -> Optional[str]:
        """Try common/recent build ID patterns as last resort"""
        logger.info("Trying common build ID patterns as fallback")
        
        # Try to get current build IDs from a working Revolut page
        # First let's try some recently found patterns or bypass the API entirely
        logger.info("Attempting direct API access without build ID...")
        
        # Try bypassing the build ID requirement entirely
        direct_api_test = await self._test_direct_api_access(session)
        if direct_api_test:
            return direct_api_test
        
        # These are example patterns - in reality, you might want to maintain a list
        # of recently seen build IDs or try to guess patterns  
        common_patterns = [
            "hqlIjzBKE4aut5_VDl56J",  # Original hardcoded one
            "kFq2h3m8N9pL5rT6sW7x",  # Example pattern
            "aB3dE5fG7hI9jK1mN3oP",  # Example pattern
        ]
        
        for build_id in common_patterns:
            logger.info(f"Testing common build ID: {build_id}")
            if await self._test_build_id(session, build_id):
                logger.info(f"Success with common build ID: {build_id}")
                return build_id
        
        return None
    
    async def _test_direct_api_access(self, session) -> Optional[str]:
        """Test if we can access Revolut careers without NextJS API"""
        try:
            # Try different API endpoints that might not need build ID
            test_urls = [
                "https://www.revolut.com/api/careers",
                "https://www.revolut.com/careers-api",
                "https://jobs.revolut.com/api/jobs",
                "https://careers.revolut.com/api/positions"
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*'
            }
            
            for url in test_urls:
                logger.info(f"Testing direct API: {url}")
                response = await self.fetch_url_async(url, session, headers=headers, timeout=10)
                if response:
                    try:
                        data = json.loads(response)
                        if 'jobs' in data or 'positions' in data or 'careers' in data:
                            logger.info(f"Found direct API endpoint: {url}")
                            # Set a special marker to use direct scraping
                            return "DIRECT_API"
                    except json.JSONDecodeError:
                        pass
            
            return None
            
        except Exception as e:
            logger.warning(f"Direct API test failed: {e}")
            return None
    
    async def _test_build_id(self, session, build_id: str) -> bool:
        """Validate build ID with test API call"""
        test_url = f"{self.BASE_URL}/{build_id}/en-GB/careers/team/engineering.json"
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*'
            }
            response = await self.fetch_url_async(test_url, session, headers=headers, params={"slug": "engineering"}, timeout=10)
            if response:
                # Try to parse as JSON to ensure it's valid
                try:
                    data = json.loads(response)
                    return "pageProps" in data  # Valid Revolut careers API response
                except json.JSONDecodeError:
                    return False
            return False
        except Exception as e:
            logger.warning(f"Build ID test failed for {build_id}: {e}")
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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