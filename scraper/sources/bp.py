import logging
import pandas as pd
import json
import re
import aiohttp
from bs4 import BeautifulSoup
from base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BpScraper(BaseScraper):
    """
    BP job scraper - scrapes jobs from BP careers page for Azerbaijan
    """
    
    async def parse_bp(self, session: aiohttp.ClientSession) -> pd.DataFrame:
        logger.info("Started scraping BP careers for Azerbaijan")
        
        url = "https://www.bp.com/en/global/corporate/careers/search-and-apply.html?country%5B0%5D=Azerbaijan"
        jobs_data = []
        
        try:
            # Headers to mimic browser behavior
            headers = {
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
                'Cache-Control': 'no-cache'
            }
            
            # First, try to fetch the main page to see if we can get jobs directly
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch BP careers page: {response.status}")
                    return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
                
                content = await response.text()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for job listings in the HTML structure you provided
            # The jobs are in <li class="ais-Hits-item"> elements
            job_items = soup.find_all('li', class_='ais-Hits-item')
            
            if not job_items:
                # Try alternative selectors
                job_items = soup.find_all('a', class_='Hit_hit__lKdvb')
                
            if not job_items:
                # Try to find any links that contain jobId parameter
                all_links = soup.find_all('a', href=True)
                job_items = [link for link in all_links if 'jobId=' in link.get('href', '')]
            
            logger.info(f"Found {len(job_items)} potential job items")
            
            # Debug: Show what content we actually got
            if not job_items:
                logger.info(f"Page content length: {len(content)} characters")
                logger.info("🔍 BP careers page loaded, but no job items found in static HTML")
                logger.info("💡 This indicates the page uses dynamic JavaScript content loading")
                
                # Check if the page mentions dynamic loading or JavaScript
                if 'javascript' in content.lower() or 'js-' in content or 'algolia' in content.lower():
                    logger.info("✅ Detected JavaScript-based job loading (Algolia or similar)")
                else:
                    logger.info("❓ No obvious signs of dynamic job loading detected")
            
            for item in job_items:
                try:
                    # Case 1: If item is <li> with <a> inside
                    if item.name == 'li':
                        link_element = item.find('a', class_='Hit_hit__lKdvb')
                        if not link_element:
                            link_element = item.find('a', href=True)
                    else:
                        # Case 2: If item is the <a> element itself
                        link_element = item
                    
                    if not link_element:
                        continue
                    
                    # Extract job title
                    title_element = link_element.find('h3', class_='Hit_hitTitle__zzFsg')
                    if not title_element:
                        title_element = link_element.find('h3')
                    
                    if title_element:
                        # Look for span with class "mouldToParent" or just get text
                        title_span = title_element.find('span', class_='mouldToParent')
                        job_title = title_span.get_text(strip=True) if title_span else title_element.get_text(strip=True)
                    else:
                        # Fallback: try to get any text from the link
                        job_title = link_element.get_text(strip=True)
                        if not job_title or len(job_title) > 200:  # Skip if too long (likely not a title)
                            continue
                    
                    # Extract location
                    location_element = link_element.find('div', class_='Hit_hitRegionBox__A0iFv')
                    location = location_element.get_text(strip=True) if location_element else "Azerbaijan"
                    
                    # Extract apply link
                    apply_link = link_element.get('href')
                    if not apply_link:
                        continue
                    
                    # Convert relative URL to absolute URL
                    if apply_link.startswith('/'):
                        apply_link = f"https://www.bp.com{apply_link}"
                    
                    # Format job title with location
                    if location and location.lower() not in job_title.lower():
                        display_title = f"{job_title} - {location}"
                    else:
                        display_title = job_title
                    
                    if job_title and apply_link:
                        jobs_data.append({
                            'company': 'BP',
                            'vacancy': display_title,
                            'apply_link': apply_link
                        })
                        
                except Exception as e:
                    logger.warning(f"Error parsing BP job item: {e}")
                    continue
            
            # If no jobs found from HTML parsing, try to look for Algolia API calls
            if not jobs_data:
                logger.info("No jobs found in HTML, checking for API calls...")
                
                # Look for Algolia configuration or API endpoints in the page
                scripts = soup.find_all('script')
                for script in scripts:
                    script_content = script.get_text()
                    if 'algolia' in script_content.lower() or 'applicationid' in script_content.lower():
                        # Try to extract API configuration
                        api_jobs = await self._try_algolia_api(session, script_content, headers)
                        jobs_data.extend(api_jobs)
                        break
            
            if not jobs_data:
                logger.warning("No jobs found on BP careers page")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            
            logger.info(f"Successfully scraped {len(jobs_data)} jobs from BP")
            return pd.DataFrame(jobs_data)
            
        except Exception as e:
            logger.error(f"Error scraping BP: {e}")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
    
    async def _try_algolia_api(self, session, script_content, headers):
        """
        Try to extract and call Algolia API if configuration is found
        """
        jobs_data = []
        
        try:
            # Look for Algolia configuration patterns
            # Common patterns: applicationId, searchApiKey, indexName
            app_id_match = re.search(r'applicationId["\']?\s*:\s*["\']([^"\']+)["\']', script_content, re.IGNORECASE)
            api_key_match = re.search(r'searchApiKey["\']?\s*:\s*["\']([^"\']+)["\']', script_content, re.IGNORECASE)
            index_match = re.search(r'indexName["\']?\s*:\s*["\']([^"\']+)["\']', script_content, re.IGNORECASE)
            
            if app_id_match and api_key_match and index_match:
                app_id = app_id_match.group(1)
                api_key = api_key_match.group(1)
                index_name = index_match.group(1)
                
                logger.info(f"Found Algolia config: appId={app_id}, index={index_name}")
                
                # Construct Algolia search URL
                algolia_url = f"https://{app_id}-dsn.algolia.net/1/indexes/{index_name}/search"
                
                # Search payload for Azerbaijan jobs
                search_payload = {
                    "query": "",
                    "facetFilters": [["country:Azerbaijan"]],
                    "hitsPerPage": 100,
                    "page": 0
                }
                
                search_headers = {
                    **headers,
                    'Content-Type': 'application/json',
                    'X-Algolia-Application-Id': app_id,
                    'X-Algolia-API-Key': api_key
                }
                
                async with session.post(algolia_url, json=search_payload, headers=search_headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        hits = data.get('hits', [])
                        
                        for hit in hits:
                            title = hit.get('title', hit.get('jobTitle', ''))
                            location = hit.get('location', hit.get('country', 'Azerbaijan'))
                            job_id = hit.get('jobId', hit.get('objectID', ''))
                            
                            if title and job_id:
                                apply_link = f"https://www.bp.com/en/global/corporate/careers/search-and-apply.html?jobId={job_id}"
                                display_title = f"{title} - {location}" if location else title
                                
                                jobs_data.append({
                                    'company': 'BP',
                                    'vacancy': display_title,
                                    'apply_link': apply_link
                                })
                        
                        logger.info(f"Retrieved {len(jobs_data)} jobs from Algolia API")
                    
        except Exception as e:
            logger.warning(f"Failed to use Algolia API: {e}")
        
        return jobs_data
    
    async def scrape(self, session: aiohttp.ClientSession) -> pd.DataFrame:
        """Main scraping method for the scraper manager"""
        return await self.parse_bp(session)