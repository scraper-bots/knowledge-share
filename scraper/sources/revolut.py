import logging
import pandas as pd
import asyncio
import json
import re
from typing import Optional
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class RevolutScraper(BaseScraper):
    """
    Revolut careers API scraper with dynamic build ID retrieval
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
    
    @scraper_error_handler
    async def scrape_revolut(self, session):
        """
        Scrape jobs from Revolut careers API
        """
        logger.info("Started scraping Revolut careers")
        
        all_jobs = []
        
        # Skip complex build ID extraction and go directly to HTML fallback
        logger.info("Using HTML fallback approach for Revolut scraper")
        html_jobs = await self._scrape_careers_html(session)
        all_jobs.extend(html_jobs)
        
        if all_jobs:
            return pd.DataFrame(all_jobs)
        
        # If HTML approach fails, try simple API approach with known build ID
        try:
            build_id = await self.get_build_id(session)
            logger.info(f"Using build ID: {build_id}")
        except Exception as e:
            logger.warning(f"Build ID extraction failed: {e}, returning HTML results only")
            return pd.DataFrame(all_jobs) if all_jobs else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
        
        # Try API approach with dynamic build ID
        api_working = False
        for team_slug in self.TEAM_SLUGS[:2]:  # Test first 2 teams
            try:
                jobs = await self._scrape_team_api(session, team_slug)
                if jobs:
                    all_jobs.extend(jobs)
                    logger.info(f"Scraped {len(jobs)} jobs from {team_slug} via API")
                    api_working = True
                    await asyncio.sleep(0.5)
                else:
                    break
            except Exception as e:
                logger.warning(f"API failed for {team_slug}: {str(e)}")
                break
        
        if api_working:
            # Continue with remaining teams
            for team_slug in self.TEAM_SLUGS[2:]:
                try:
                    jobs = await self._scrape_team_api(session, team_slug)
                    all_jobs.extend(jobs)
                    logger.info(f"Scraped {len(jobs)} jobs from {team_slug}")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error scraping team {team_slug}: {str(e)}")
                    continue
        else:
            # Fallback to HTML scraping
            logger.info("API blocked, trying HTML fallback")
            html_jobs = await self._scrape_careers_html(session)
            all_jobs.extend(html_jobs)
        
        logger.info(f"Successfully scraped {len(all_jobs)} total jobs from Revolut")
        return pd.DataFrame(all_jobs) if all_jobs else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
    
    async def get_build_id(self, session) -> str:
        """
        Dynamically extract the Next.js build ID from Revolut's website
        """
        if self.build_id:
            return self.build_id
        
        logger.info("Extracting Revolut build ID dynamically")
        
        # Headers for build ID extraction (mimic real browser)
        build_id_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Cache-Control': 'no-cache'
        }
        
        # Try multiple methods in order of reliability
        methods = [
            self._extract_from_careers_page,
            self._extract_from_homepage,
            self._extract_from_any_page
        ]
        
        for method in methods:
            try:
                build_id = await method(session, build_id_headers)
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
    
    async def _extract_from_careers_page(self, session, headers) -> Optional[str]:
        """Extract build ID from careers page (most reliable)"""
        response = await self.fetch_url_async("https://www.revolut.com/careers", session, headers=headers)
        if not response:
            return None
        
        return self._find_build_id_in_content(response, "careers page")
    
    async def _extract_from_homepage(self, session, headers) -> Optional[str]:
        """Extract build ID from homepage"""
        response = await self.fetch_url_async("https://www.revolut.com", session, headers=headers)
        if not response:
            return None
        
        return self._find_build_id_in_content(response, "homepage")
    
    async def _extract_from_any_page(self, session, headers) -> Optional[str]:
        """Try other Revolut pages"""
        test_pages = [
            "https://www.revolut.com/about",
            "https://www.revolut.com/business",
            "https://www.revolut.com/en-GB"
        ]
        
        for page_url in test_pages:
            try:
                response = await self.fetch_url_async(page_url, session, headers=headers)
                if response:
                    build_id = self._find_build_id_in_content(response, page_url)
                    if build_id:
                        return build_id
            except Exception:
                continue
        
        return None
    
    def _find_build_id_in_content(self, content: str, source: str) -> Optional[str]:
        """Find build ID in page content using multiple patterns"""
        logger.info(f"Searching for build ID in {source}, content length: {len(content)}")
        
        # Multiple patterns to try (in order of reliability)
        patterns = [
            r'/_next/static/([a-zA-Z0-9_-]+)/_ssgManifest\.js',      # SSG manifest
            r'/_next/static/([a-zA-Z0-9_-]+)/_buildManifest\.js',    # Build manifest  
            r'/_next/data/([a-zA-Z0-9_-]+)/',                         # Data URLs
            r'"buildId":"([a-zA-Z0-9_-]+)"',                      # JSON buildId
            r'buildId\s*:\s*"([a-zA-Z0-9_-]+)"',                  # JS buildId
            r'static/([a-zA-Z0-9_-]+)/_ssgManifest',                  # Alternative SSG
            r'static/([a-zA-Z0-9_-]+)/_buildManifest'                 # Alternative build
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, content)
            logger.info(f"Pattern {i+1} ({pattern[:30]}...): {len(matches)} matches")
            if matches:
                build_id = matches[0]
                logger.info(f"Found build ID from pattern {i+1}: {build_id}")
                return build_id
        
        # Debug: look for any _next references
        next_refs = re.findall(r'_next/[^"\s]{10,}', content)
        logger.info(f"Found {len(next_refs)} _next references: {next_refs[:3]}")
        
        return None
    
    async def _test_build_id(self, session, build_id: str) -> bool:
        """Validate build ID with test API call"""
        test_url = f"{self.BASE_URL}/{build_id}/en-GB/careers/team/engineering.json"
        
        # Headers for API validation
        api_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.revolut.com/careers/',
            'DNT': '1',
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'x-nextjs-data': '1'
        }
        
        try:
            response = await self.fetch_url_async(test_url, session, headers=api_headers, params={"slug": "engineering"})
            if response:
                try:
                    data = json.loads(response)
                    return "pageProps" in data  # Valid Revolut careers API response
                except json.JSONDecodeError:
                    return False
            return False
        except Exception as e:
            logger.warning(f"Build ID test failed for {build_id}: {e}")
            return False
    
    async def _scrape_careers_html(self, session):
        """Fallback: scrape Revolut careers page via HTML"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            response = await self.fetch_url_async("https://www.revolut.com/careers", session, headers=headers)
            if not response:
                logger.warning("Failed to fetch Revolut careers HTML page")
                return []
            
            # Simple extraction - look for job-related content
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response, 'html.parser')
            
            jobs = []
            # Look for common job listing patterns
            job_elements = soup.find_all(['a', 'div'], href=True) or soup.find_all(string=lambda text: text and 'engineer' in text.lower())
            
            # Look for actual job postings instead of creating placeholders
            if job_elements:
                logger.info("HTML fallback found careers page content, but no structured job data extracted")
            
            return jobs
            
        except Exception as e:
            logger.error(f"HTML fallback failed: {str(e)}")
            return []
    
    async def _scrape_team_api(self, session, team_slug):
        """
        Scrape jobs for a specific team using the working API format
        """
        url = f"{self.BASE_URL}/{self.build_id}/en-GB/careers/team/{team_slug}.json"
        params = {"slug": team_slug}
        
        # Enhanced headers for API calls (from user's browser example)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://www.revolut.com/careers/',
            'Origin': 'https://www.revolut.com',
            'DNT': '1',
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'x-nextjs-data': '1',
            'x-middleware-prefetch': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
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