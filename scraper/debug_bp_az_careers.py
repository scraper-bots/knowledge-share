#!/usr/bin/env python3
"""
Debug the BP Azerbaijan-specific career pages
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def debug_bp_az_careers():
    """Debug BP Azerbaijan career pages"""
    
    urls = [
        "https://www.bp.com/en/global/corporate/careers/professionals/locations/azerbaijan.html",
        "https://www.bp.com/en/global/corporate/careers/students-and-graduates/locations/azerbaijan.html"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                print(f"🔍 Analyzing: {url}")
                
                async with session.get(url, headers=headers) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Look for direct job links or apply buttons
                        apply_links = soup.find_all('a', href=lambda x: x and any(keyword in x.lower() for keyword in ['apply', 'job', 'workday', 'vacancy']))
                        print(f"   Apply/Job links: {len(apply_links)}")
                        
                        if apply_links:
                            for i, link in enumerate(apply_links[:5]):
                                href = link.get('href')
                                text = link.get_text(strip=True)
                                print(f"     {i+1}. {href}")
                                print(f"        Text: {text[:60]}")
                        
                        # Look for Workday mentions
                        workday_mentions = soup.find_all(string=lambda text: text and 'workday' in text.lower())
                        print(f"   Workday mentions: {len(workday_mentions)}")
                        
                        # Look for specific job titles or opportunities
                        job_titles = soup.find_all(string=lambda text: text and any(title in text.lower() for title in ['engineer', 'analyst', 'specialist', 'manager', 'coordinator']))
                        print(f"   Job title mentions: {len(job_titles)}")
                        
                        if job_titles:
                            print(f"   Sample job titles:")
                            for title in job_titles[:3]:
                                print(f"     - {title.strip()[:80]}")
                        
                        # Look for specific opportunities section
                        opportunities = soup.find_all(text=lambda text: text and 'opportunities' in text.lower())
                        print(f"   'Opportunities' mentions: {len(opportunities)}")
                        
                        # Check for scripts that might load job data
                        scripts = soup.find_all('script')
                        job_related_scripts = 0
                        for script in scripts:
                            script_text = script.get_text()
                            if any(keyword in script_text.lower() for keyword in ['job', 'vacancy', 'workday', 'career']):
                                job_related_scripts += 1
                        
                        print(f"   Job-related scripts: {job_related_scripts}")
                    
                    elif response.status in [301, 302, 303, 307, 308]:
                        location = response.headers.get('location', 'No location header')
                        print(f"   Redirect to: {location}")
                    
                    else:
                        print(f"   Failed with status {response.status}")
                
                print()
                await asyncio.sleep(1)  # Be respectful
                
            except Exception as e:
                print(f"   Error: {e}")
                print()

if __name__ == "__main__":
    asyncio.run(debug_bp_az_careers())