#!/usr/bin/env python3
"""
Debug the BP Azerbaijan career page
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def debug_bp_az():
    """Debug BP Azerbaijan career page"""
    url = "https://www.bp.com/en_az/azerbaijan/home/careers.html"
    
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
                    
                    # Look for job-related links
                    print("\n🔍 Searching for job elements...")
                    
                    # Look for links to job pages or external career sites
                    job_links = soup.find_all('a', href=lambda x: x and any(keyword in x.lower() for keyword in ['job', 'career', 'vacancy', 'workday', 'apply']))
                    print(f"Found {len(job_links)} potential job-related links")
                    
                    if job_links:
                        print("Job-related links:")
                        for i, link in enumerate(job_links):
                            href = link.get('href')
                            text = link.get_text(strip=True)
                            print(f"  {i+1}. {href}")
                            print(f"      Text: {text[:80]}")
                            print()
                    
                    # Look for specific job position mentions
                    job_keywords = ['engineer', 'specialist', 'manager', 'analyst', 'coordinator', 'technician', 'supervisor', 'director']
                    
                    for keyword in job_keywords:
                        matches = soup.find_all(string=lambda text: text and keyword in text.lower())
                        if matches:
                            print(f"Found {len(matches)} mentions of '{keyword}'")
                            for match in matches[:2]:  # Show first 2
                                print(f"  - {match.strip()[:100]}")
                    
                    # Look for Workday or other external platforms
                    external_links = soup.find_all('a', href=lambda x: x and any(platform in x.lower() for platform in ['workday', 'greenhouse', 'lever', 'bamboo']))
                    if external_links:
                        print(f"\nFound {len(external_links)} external career platform links:")
                        for link in external_links:
                            print(f"  - {link.get('href')}")
                    
                    # Show any paragraphs with career-related content
                    career_paragraphs = soup.find_all('p', string=lambda text: text and any(word in text.lower() for word in ['career', 'job', 'opportunity', 'position']))
                    if career_paragraphs:
                        print(f"\nCareer-related paragraphs:")
                        for i, p in enumerate(career_paragraphs[:3]):
                            print(f"  {i+1}. {p.get_text(strip=True)[:150]}...")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_bp_az())