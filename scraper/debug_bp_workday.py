#!/usr/bin/env python3
"""
Try to find BP's Workday instance or other job board platform
"""

import asyncio
import aiohttp
import json

async def find_bp_workday():
    """Try to find BP's Workday or other job platform"""
    
    # Common Workday patterns for large companies
    workday_patterns = [
        "https://bp.wd1.myworkdayjobs.com/bp",
        "https://bp.wd1.myworkdayjobs.com/BP",
        "https://bp.wd1.myworkdayjobs.com/bp_jobs",
        "https://bp.wd1.myworkdayjobs.com/BP_Jobs",
        "https://bp.wd1.myworkdayjobs.com/External",
        "https://bp.wd5.myworkdayjobs.com/bp",
        "https://bp.wd5.myworkdayjobs.com/External",
        "https://bp.wd3.myworkdayjobs.com/bp",
        "https://bp.wd3.myworkdayjobs.com/External",
        # Try with different subdomain patterns
        "https://bpplc.wd1.myworkdayjobs.com/bp",
        "https://bpplc.wd1.myworkdayjobs.com/External",
        "https://britishpetroleum.wd1.myworkdayjobs.com/bp",
    ]
    
    # Other platform patterns
    other_patterns = [
        "https://bp.greenhouse.io/jobs",
        "https://jobs.lever.co/bp",
        "https://bp.smartrecruiters.com/jobs",
        "https://bp.bamboohr.com/jobs",
        "https://careers.bp.com/jobs",
        "https://apply.bp.com/jobs"
    ]
    
    all_patterns = workday_patterns + other_patterns
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    async with aiohttp.ClientSession() as session:
        for url in all_patterns:
            try:
                print(f"🧪 Testing: {url}")
                
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        print(f"   Content-Type: {content_type}")
                        
                        content = await response.text()
                        print(f"   Content length: {len(content)}")
                        
                        # Check for job-related content
                        job_indicators = [
                            'Azerbaijan' in content,
                            'job' in content.lower(),
                            'position' in content.lower(),
                            'vacancy' in content.lower(),
                            'career' in content.lower()
                        ]
                        
                        indicator_count = sum(job_indicators)
                        print(f"   Job indicators: {indicator_count}/5")
                        
                        if indicator_count >= 3:
                            print(f"   ✅ This looks like a working job board!")
                            
                            # Look for Azerbaijan jobs specifically
                            if 'Azerbaijan' in content:
                                print(f"   🎯 Contains Azerbaijan jobs!")
                                
                                # Try to extract some job info
                                from bs4 import BeautifulSoup
                                soup = BeautifulSoup(content, 'html.parser')
                                
                                # Look for job titles near Azerbaijan
                                az_context = []
                                for text in soup.find_all(string=lambda t: t and 'azerbaijan' in t.lower()):
                                    parent = text.parent
                                    if parent:
                                        context = parent.get_text(strip=True)
                                        az_context.append(context[:100])
                                
                                if az_context:
                                    print(f"   Azerbaijan context samples:")
                                    for i, ctx in enumerate(az_context[:3]):
                                        print(f"     {i+1}. {ctx}")
                            
                    elif response.status in [301, 302, 303, 307, 308]:
                        location = response.headers.get('location', 'No location header')
                        print(f"   Redirect to: {location}")
                        
                        # If it redirects to another workday instance, follow it
                        if 'myworkdayjobs.com' in location and location not in all_patterns:
                            print(f"   🔄 Following Workday redirect...")
                            all_patterns.append(location)
                    
                    else:
                        print(f"   ❌ Failed")
                
                print()
                await asyncio.sleep(0.5)
                
            except asyncio.TimeoutError:
                print(f"   ⏰ Timeout")
                print()
            except Exception as e:
                print(f"   ❌ Error: {e}")
                print()

if __name__ == "__main__":
    asyncio.run(find_bp_workday())