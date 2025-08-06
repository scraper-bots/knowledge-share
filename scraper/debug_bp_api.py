#!/usr/bin/env python3
"""
Try to find BP's job API endpoint
"""

import asyncio
import aiohttp
import json

async def find_bp_api():
    """Try to find BP's job API"""
    
    # Common API patterns for job sites
    potential_apis = [
        "https://www.bp.com/api/careers/jobs",
        "https://www.bp.com/api/jobs",
        "https://api.bp.com/careers/jobs", 
        "https://careers-api.bp.com/jobs",
        "https://www.bp.com/content/careers/jobs.json",
        # Add country filter variants
        "https://www.bp.com/api/careers/jobs?country=Azerbaijan",
        "https://www.bp.com/api/jobs?country=Azerbaijan",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.bp.com/en/global/corporate/careers/search-and-apply.html'
    }
    
    async with aiohttp.ClientSession() as session:
        for api_url in potential_apis:
            try:
                print(f"🧪 Testing: {api_url}")
                
                async with session.get(api_url, headers=headers) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        print(f"   Content-Type: {content_type}")
                        
                        if 'application/json' in content_type:
                            try:
                                data = await response.json()
                                print(f"   ✅ JSON response received!")
                                print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'Array'}")
                                
                                # If it's a list, show first item
                                if isinstance(data, list) and data:
                                    print(f"   First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else data[0]}")
                                
                            except json.JSONDecodeError:
                                text = await response.text()
                                print(f"   Response text (first 200 chars): {text[:200]}")
                        else:
                            text = await response.text()
                            print(f"   Text response (first 200 chars): {text[:200]}")
                    
                    elif response.status in [301, 302, 303, 307, 308]:
                        location = response.headers.get('location', 'No location header')
                        print(f"   Redirect to: {location}")
                    
                    else:
                        print(f"   ❌ Failed")
                
                print()
                await asyncio.sleep(0.5)  # Be nice to the server
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                print()

if __name__ == "__main__":
    asyncio.run(find_bp_api())