#!/usr/bin/env python3
"""
Debug BP page to find API calls in JavaScript
"""

import asyncio
import aiohttp
import re
from bs4 import BeautifulSoup

async def analyze_bp_scripts():
    """Analyze BP scripts for API endpoints"""
    url = "https://www.bp.com/en/global/corporate/careers/search-and-apply.html"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    print(f"Failed to fetch page: {response.status}")
                    return
                
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                print("🔍 Analyzing scripts for API patterns...")
                
                scripts = soup.find_all('script')
                print(f"Found {len(scripts)} script elements")
                
                api_patterns = [
                    r'https?://[^\s"\']+/api/[^\s"\']*job[^\s"\']*',
                    r'https?://[^\s"\']+\.algolia[^\s"\']*',
                    r'https?://[^\s"\']+workday[^\s"\']*',
                    r'https?://[^\s"\']+greenhouse[^\s"\']*',
                    r'https?://[^\s"\']+lever[^\s"\']*',
                    r'https?://[^\s"\']+bamboohr[^\s"\']*',
                    r'https?://[^\s"\']+smartrecruiters[^\s"\']*',
                    r'applicationId["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'searchApiKey["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'indexName["\']?\s*:\s*["\']([^"\']+)["\']',
                ]
                
                found_apis = set()
                
                for i, script in enumerate(scripts):
                    script_content = script.get_text()
                    if not script_content.strip():
                        continue
                    
                    # Check for external script sources
                    src = script.get('src')
                    if src and any(keyword in src.lower() for keyword in ['job', 'career', 'algolia', 'api']):
                        print(f"📄 Interesting script src: {src}")
                    
                    # Search for API patterns in script content
                    for pattern in api_patterns:
                        matches = re.findall(pattern, script_content, re.IGNORECASE)
                        for match in matches:
                            found_apis.add(match)
                
                if found_apis:
                    print(f"\n🎯 Found potential API endpoints:")
                    for api in found_apis:
                        print(f"  • {api}")
                else:
                    print(f"\n❌ No API endpoints found in scripts")
                
                # Look for job-related configuration
                print(f"\n🔍 Looking for job-related configuration...")
                
                config_patterns = [
                    r'jobSearch["\']?\s*:\s*\{[^}]+\}',
                    r'careerSite["\']?\s*:\s*\{[^}]+\}',
                    r'searchConfig["\']?\s*:\s*\{[^}]+\}',
                ]
                
                for script in scripts:
                    script_content = script.get_text()
                    for pattern in config_patterns:
                        matches = re.findall(pattern, script_content, re.IGNORECASE | re.DOTALL)
                        for match in matches:
                            print(f"  📋 Config found: {match[:200]}...")
                
                # Look for specific job board platforms
                platforms = ['workday', 'greenhouse', 'lever', 'bamboohr', 'smartrecruiters', 'icims', 'jobvite']
                found_platforms = []
                
                for script in scripts:
                    script_content = script.get_text().lower()
                    for platform in platforms:
                        if platform in script_content:
                            found_platforms.append(platform)
                
                if found_platforms:
                    print(f"\n🏢 Detected job board platforms: {', '.join(set(found_platforms))}")
                else:
                    print(f"\n❓ No known job board platforms detected")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_bp_scripts())