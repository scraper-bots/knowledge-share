#!/usr/bin/env python3
"""
Debug BP careers page to understand its structure
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def debug_bp():
    """Debug BP careers page"""
    url = "https://www.bp.com/en/global/corporate/careers/search-and-apply.html?country%5B0%5D=Azerbaijan"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('content-type')}")
                
                if response.status == 200:
                    content = await response.text()
                    print(f"Content length: {len(content)}")
                    
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Look for various job-related elements
                    print("\n🔍 Searching for job elements...")
                    
                    # Check for the exact classes from your HTML
                    hits_divs = soup.find_all('div', class_='ais-Hits')
                    print(f"Found {len(hits_divs)} 'ais-Hits' divs")
                    
                    hit_items = soup.find_all('li', class_='ais-Hits-item')
                    print(f"Found {len(hit_items)} 'ais-Hits-item' li elements")
                    
                    hit_links = soup.find_all('a', class_='Hit_hit__lKdvb')
                    print(f"Found {len(hit_links)} 'Hit_hit__lKdvb' a elements")
                    
                    # Look for any jobId links
                    jobid_links = [a for a in soup.find_all('a', href=True) if 'jobId=' in a.get('href', '')]
                    print(f"Found {len(jobid_links)} links with 'jobId=' parameter")
                    
                    # Look for scripts that might contain Algolia config
                    scripts = soup.find_all('script')
                    algolia_scripts = 0
                    for script in scripts:
                        script_text = script.get_text()
                        if 'algolia' in script_text.lower() or 'applicationid' in script_text.lower():
                            algolia_scripts += 1
                    
                    print(f"Found {algolia_scripts} scripts mentioning Algolia")
                    
                    # Show a sample of the content around potential job areas
                    if hits_divs:
                        print(f"\n📄 Sample content from first ais-Hits div:")
                        print(hits_divs[0].prettify()[:500])
                    elif jobid_links:
                        print(f"\n📄 Sample jobId link:")
                        print(jobid_links[0].prettify())
                    else:
                        # Look for any div with "job" in class name
                        job_divs = soup.find_all('div', class_=lambda x: x and 'job' in x.lower())
                        print(f"Found {len(job_divs)} divs with 'job' in class name")
                        
                        if job_divs:
                            print(f"\n📄 Sample job div:")
                            print(job_divs[0].prettify()[:300])
                        else:
                            # Show the first 1000 characters of the page
                            print(f"\n📄 First 1000 characters of page:")
                            print(content[:1000])
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_bp())