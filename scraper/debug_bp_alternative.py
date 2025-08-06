#!/usr/bin/env python3
"""
Try alternative BP career endpoints
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def try_bp_alternatives():
    """Try alternative BP career endpoints"""
    
    # Alternative career page URLs
    alternative_urls = [
        "https://www.bp.com/en/global/corporate/careers.html",
        "https://www.bp.com/content/bp/global/corporate/careers/search-and-apply",
        "https://careers.bp.com/",
        "https://bp.wd1.myworkdayjobs.com/en-US/bp_jobs",
        "https://bp.wd1.myworkdayjobs.com/bp_jobs",
        "https://jobs.bp.com/",
        # Try regional pages
        "https://www.bp.com/en_az/azerbaijan/home/careers.html",
        "https://www.bp.com/en/azerbaijan/home/careers.html",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    async with aiohttp.ClientSession() as session:
        for url in alternative_urls:
            try:
                print(f"🧪 Testing: {url}")
                
                async with session.get(url, headers=headers) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Look for job-related content
                        job_indicators = [
                            soup.find_all(string=lambda text: text and 'Pore Pressure' in text),
                            soup.find_all(string=lambda text: text and 'Azerbaijan' in text),
                            soup.find_all('a', href=lambda x: x and 'job' in x.lower()),
                            soup.find_all('div', class_=lambda x: x and 'job' in x.lower()),
                            soup.find_all(string=lambda text: text and 'career' in text.lower()),
                        ]
                        
                        total_indicators = sum(len(indicators) for indicators in job_indicators)
                        print(f"   Job indicators found: {total_indicators}")
                        
                        if total_indicators > 0:
                            print(f"   ✅ This page has job-related content!")
                            
                            # Show sample content
                            job_links = soup.find_all('a', href=lambda x: x and 'job' in x.lower())
                            if job_links:
                                print(f"   Sample job links:")
                                for link in job_links[:3]:
                                    print(f"     • {link.get('href')} - {link.get_text(strip=True)[:50]}")
                        else:
                            print(f"   ❌ No job content found")
                    
                    elif response.status in [301, 302, 303, 307, 308]:
                        location = response.headers.get('location', 'No location header')
                        print(f"   Redirect to: {location}")
                    
                    else:
                        print(f"   ❌ Failed")
                
                print()
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                print()

if __name__ == "__main__":
    asyncio.run(try_bp_alternatives())