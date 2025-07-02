import logging
import pandas as pd
import asyncio
import json
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class RevolutScraper(BaseScraper):
    """
    Revolut careers API scraper - simplified version using working build ID
    """
    
    BASE_URL = "https://www.revolut.com/_next/data"
    BUILD_ID = "hqlIjzBKE4aut5_VDl56J"  # Working build ID from browser test
    
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
        
        # Try API approach first with limited teams
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
            
            # If we find any job-related content, create placeholder entries
            if job_elements:
                jobs.append({
                    'company': 'Revolut',
                    'vacancy': 'Various Positions Available',
                    'apply_link': 'https://www.revolut.com/careers'
                })
                logger.info("HTML fallback found careers page, created placeholder entry")
            
            return jobs
            
        except Exception as e:
            logger.error(f"HTML fallback failed: {str(e)}")
            return []
    
    async def _scrape_team_api(self, session, team_slug):
        """
        Scrape jobs for a specific team using the working API format
        """
        url = f"{self.BASE_URL}/{self.BUILD_ID}/en-GB/careers/team/{team_slug}.json"
        params = {"slug": team_slug}
        
        # Use exact headers from working browser request
        headers = {
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