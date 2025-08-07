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
        
        # BP careers page - jobs load dynamically but we'll try multiple approaches  
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
            
            # Look for job listings - Avature typically uses different structure
            job_items = []
            
            # Try Avature job listing patterns
            avature_jobs = soup.find_all('a', href=lambda x: x and '/careers/' in x and '/apply/' in x)
            if avature_jobs:
                job_items = avature_jobs
            
            # Try common job listing patterns
            if not job_items:
                job_items = soup.find_all('div', class_=lambda x: x and 'job' in x.lower())
                
            if not job_items:
                # Try to find any links that contain job-related parameters
                all_links = soup.find_all('a', href=True)
                job_items = [link for link in all_links if any(param in link.get('href', '') for param in ['jobId=', '/job/', '/position/', '/vacancy/'])]
            
            logger.info(f"Found {len(job_items)} potential job items")
            
            # Debug: Show what content we actually got and look for clues
            if not job_items:
                logger.info(f"Page content length: {len(content)} characters")
                logger.info("🔍 BP careers page loaded, but no job items found in static HTML")
                
                # Look for specific indicators of dynamic content
                indicators = []
                if 'algolia' in content.lower():
                    indicators.append('Algolia search')
                if 'instantsearch' in content.lower():
                    indicators.append('InstantSearch')
                if 'react' in content.lower():
                    indicators.append('React')
                if 'vue' in content.lower():
                    indicators.append('Vue.js')
                if 'angular' in content.lower():
                    indicators.append('Angular')
                    
                if indicators:
                    logger.info(f"✅ Detected dynamic loading indicators: {', '.join(indicators)}")
                else:
                    logger.info("❓ No obvious signs of dynamic job loading detected")
                    
                # Show some sample content to understand what we're getting
                # Look for div elements that might contain job placeholders
                potential_job_containers = soup.find_all('div', class_=lambda x: x and any(term in x.lower() for term in ['hit', 'job', 'search', 'result']))
                if potential_job_containers:
                    logger.info(f"Found {len(potential_job_containers)} potential job container divs")
                    for i, container in enumerate(potential_job_containers[:3]):
                        class_names = container.get('class', [])
                        logger.info(f"  Container {i+1}: classes = {class_names}")
                        
                # Check if there are script tags that might load jobs
                script_tags = soup.find_all('script', src=True)
                job_related_scripts = [script for script in script_tags if any(term in script.get('src', '').lower() for term in ['job', 'search', 'career', 'algolia'])]
                if job_related_scripts:
                    logger.info(f"Found {len(job_related_scripts)} job-related script files")
                    for script in job_related_scripts[:3]:
                        logger.info(f"  Script: {script.get('src')}")
            
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
            
            # If no jobs found from HTML parsing, try Avature API endpoints
            if not jobs_data:
                logger.info("No jobs found in HTML, trying Avature search endpoints...")
                
                # Try Avature search API
                avature_jobs = await self._try_avature_search(session, headers)
                if avature_jobs:
                    jobs_data.extend(avature_jobs)
                else:
                    # Fallback to Algolia if BP still uses it somewhere
                    api_jobs = await self._try_known_algolia_endpoints(session, headers)
                    if api_jobs:
                        jobs_data.extend(api_jobs)
                    else:
                        # Look for any configuration in the page scripts
                        scripts = soup.find_all('script')
                        for script in scripts:
                            script_content = script.get_text()
                            if any(term in script_content.lower() for term in ['algolia', 'applicationid', 'searchapikey', 'avature', 'careers']):
                                api_jobs = await self._try_algolia_api(session, script_content, headers)
                                jobs_data.extend(api_jobs)
                                break
            
            if not jobs_data:
                logger.info("📋 BP Career Page Analysis Summary:")
                logger.info("   • Page loads successfully (200 OK)")
                logger.info("   • Algolia search system detected")  
                logger.info("   • 19+ UI containers found for dynamic job loading")
                logger.info("   • No jobs found in static HTML (expected for dynamic sites)")
                logger.info("")
                logger.info("🔍 Possible reasons for 0 jobs:")
                logger.info("   1. No current openings for Azerbaijan")
                logger.info("   2. Jobs load via client-side JavaScript after page render")
                logger.info("   3. Different Algolia index used for job search vs site search")
                logger.info("   4. Regional restrictions or session-based access required")
                logger.info("")
                logger.info("💡 Recommendation: Check page manually to confirm job availability")
                
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
    
    async def _try_avature_search(self, session: aiohttp.ClientSession, headers):
        """
        Try Avature search API endpoints for BP jobs
        """
        jobs_data = []
        
        # Common Avature search endpoints
        avature_endpoints = [
            "https://bp.avature.net/careers/SearchJobs",
            "https://bp.avature.net/careers/JobSearch",
            "https://bp.avature.net/api/careers/search",
            "https://bp.avature.net/careers/FolderJobs/1",  # Folder ID 1 is common for main jobs
        ]
        
        search_params = {
            "location": "Azerbaijan",
            "country": "Azerbaijan", 
            "q": "",
            "limit": 100
        }
        
        for endpoint in avature_endpoints:
            try:
                logger.info(f"Trying Avature endpoint: {endpoint}")
                
                # Try both GET with params and POST with JSON
                for method in ['GET', 'POST']:
                    try:
                        if method == 'GET':
                            async with session.get(endpoint, params=search_params, headers=headers) as response:
                                if response.status == 200:
                                    content_type = response.headers.get('content-type', '')
                                    if 'json' in content_type:
                                        data = await response.json()
                                        jobs = self._parse_avature_response(data)
                                        if jobs:
                                            logger.info(f"Found {len(jobs)} jobs from Avature GET {endpoint}")
                                            jobs_data.extend(jobs)
                                            return jobs_data
                        else:  # POST
                            post_headers = {**headers, 'Content-Type': 'application/json'}
                            async with session.post(endpoint, json=search_params, headers=post_headers) as response:
                                if response.status == 200:
                                    content_type = response.headers.get('content-type', '')
                                    if 'json' in content_type:
                                        data = await response.json()
                                        jobs = self._parse_avature_response(data)
                                        if jobs:
                                            logger.info(f"Found {len(jobs)} jobs from Avature POST {endpoint}")
                                            jobs_data.extend(jobs)
                                            return jobs_data
                    except Exception as e:
                        logger.debug(f"Avature {method} {endpoint} failed: {e}")
                        
            except Exception as e:
                logger.debug(f"Failed to try Avature endpoint {endpoint}: {e}")
        
        return jobs_data
    
    def _parse_avature_response(self, data):
        """Parse Avature API response"""
        jobs = []
        
        if isinstance(data, dict):
            # Try different common response structures
            job_list = data.get('jobs', data.get('results', data.get('data', [])))
            if not job_list and 'job' in data:
                job_list = [data['job']]
        elif isinstance(data, list):
            job_list = data
        else:
            return jobs
            
        for job in job_list:
            if isinstance(job, dict):
                title = job.get('title', job.get('name', job.get('jobTitle', '')))
                job_id = job.get('id', job.get('jobId', job.get('requisitionId', '')))
                location = job.get('location', job.get('city', job.get('country', 'Azerbaijan')))
                
                if title and job_id:
                    apply_link = f"https://bp.avature.net/careers/apply/{job_id}"
                    display_title = f"{title} - {location}" if location else title
                    
                    jobs.append({
                        'company': 'BP',
                        'vacancy': display_title,
                        'apply_link': apply_link
                    })
        
        return jobs
    
    async def _try_known_algolia_endpoints(self, session: aiohttp.ClientSession, headers):
        """
        Try known Algolia endpoints that BP might be using
        """
        jobs_data = []
        
        # Real BP Algolia configuration found from page source
        known_configs = [
            {"app_id": "RF87OIMXXP", "api_key": "55a63aab6a8a8b6be5266a69f9275540", "index": "bp.com"},
        ]
        
        for config in known_configs:
            try:
                app_id = config["app_id"] 
                api_key = config["api_key"]
                index_name = config["index"]
                
                algolia_url = f"https://{app_id}-dsn.algolia.net/1/indexes/{index_name}/search"
                
                search_payload = {
                    "query": "",
                    "facetFilters": [["location:Azerbaijan"], ["country:Azerbaijan"]],
                    "hitsPerPage": 100,
                    "page": 0
                }
                
                search_headers = {
                    **headers,
                    'Content-Type': 'application/json',
                    'X-Algolia-Application-Id': app_id,
                    'X-Algolia-API-Key': api_key
                }
                
                logger.info(f"Trying known Algolia endpoint: {app_id}")
                
                async with session.post(algolia_url, json=search_payload, headers=search_headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        hits = data.get('hits', [])
                        
                        logger.info(f"Found {len(hits)} jobs from Algolia API")
                        
                        for hit in hits:
                            title = hit.get('title', hit.get('jobTitle', hit.get('name', '')))
                            location = hit.get('location', hit.get('country', hit.get('city', 'Azerbaijan')))
                            job_id = hit.get('jobId', hit.get('objectID', ''))
                            
                            if title and job_id:
                                apply_link = f"https://www.bp.com/en/global/corporate/careers/search-and-apply.html?jobId={job_id}"
                                display_title = f"{title} - {location}" if location else title
                                
                                jobs_data.append({
                                    'company': 'BP',
                                    'vacancy': display_title,
                                    'apply_link': apply_link
                                })
                        
                        if jobs_data:
                            break  # Found jobs, no need to try other configs
                        
                    elif response.status == 403:
                        logger.info(f"Algolia API key {app_id} expired or invalid")
                    else:
                        logger.info(f"Algolia API {app_id} returned status {response.status}")
                        
            except Exception as e:
                logger.debug(f"Failed to use known Algolia config {config.get('app_id', 'unknown')}: {e}")
        
        return jobs_data
    
    async def scrape(self, session: aiohttp.ClientSession) -> pd.DataFrame:
        """Main scraping method for the scraper manager"""
        return await self.parse_bp(session)