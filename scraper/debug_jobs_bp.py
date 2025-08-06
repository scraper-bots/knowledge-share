#!/usr/bin/env python3
"""
Debug the jobs.bp.com page to see if it has actual job listings
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def debug_jobs_bp():
    """Debug jobs.bp.com page"""
    url = "https://jobs.bp.com/"
    
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
                    
                    # Look for job listings or job links
                    print("\n🔍 Searching for job elements...")
                    
                    # Look for common job listing patterns
                    job_links = soup.find_all('a', href=lambda x: x and ('job' in x.lower() or 'vacancy' in x.lower()))
                    print(f"Found {len(job_links)} potential job links")
                    
                    if job_links:
                        print("Sample job links:")
                        for i, link in enumerate(job_links[:5]):
                            href = link.get('href')
                            text = link.get_text(strip=True)
                            print(f"  {i+1}. {href} - {text[:50]}")
                    
                    # Look for Azerbaijan-specific content
                    az_content = soup.find_all(string=lambda text: text and 'azerbaijan' in text.lower())
                    print(f"\nFound {len(az_content)} mentions of Azerbaijan")
                    
                    if az_content:
                        print("Sample Azerbaijan mentions:")
                        for i, text in enumerate(az_content[:3]):
                            print(f"  {i+1}. {text.strip()[:100]}")
                    
                    # Look for any form or search functionality
                    forms = soup.find_all('form')
                    print(f"\nFound {len(forms)} forms")
                    
                    if forms:
                        for i, form in enumerate(forms):
                            action = form.get('action', 'No action')
                            method = form.get('method', 'GET')
                            print(f"  Form {i+1}: {method} {action}")
                    
                    # Check if this is a redirect page
                    meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
                    if meta_refresh:
                        content_attr = meta_refresh.get('content', '')
                        print(f"\nFound meta refresh: {content_attr}")
                    
                    # Look for external career site references
                    external_patterns = ['workday', 'greenhouse', 'lever', 'bamboohr', 'smartrecruiters']
                    external_found = []
                    
                    for pattern in external_patterns:
                        if pattern in content.lower():
                            external_found.append(pattern)
                    
                    if external_found:
                        print(f"\nFound external career platforms: {', '.join(external_found)}")
                    
                    # Show first 2000 characters if no specific job content found
                    if not job_links and not az_content:
                        print(f"\n📄 First 2000 characters of page:")
                        print(content[:2000])
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_jobs_bp())