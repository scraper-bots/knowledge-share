#!/usr/bin/env python3
"""
Quick diagnostic tool to identify broken scrapers
"""

import asyncio
import aiohttp
import time
from scraper_manager import ScraperManager

async def quick_test_scraper(manager, session, scraper_name, timeout=10):
    """Test a single scraper with timeout"""
    try:
        start_time = time.time()
        
        # Create a timeout for the scraper test
        result = await asyncio.wait_for(
            manager.run_single_scraper(scraper_name, session),
            timeout=timeout
        )
        
        elapsed = time.time() - start_time
        jobs = len(result) if result is not None else 0
        
        return {
            'name': scraper_name,
            'status': 'working' if jobs > 0 else 'no_jobs',
            'jobs': jobs,
            'time': round(elapsed, 1),
            'error': None
        }
        
    except asyncio.TimeoutError:
        return {
            'name': scraper_name,
            'status': 'timeout',
            'jobs': 0,
            'time': timeout,
            'error': 'Timeout'
        }
    except Exception as e:
        return {
            'name': scraper_name,
            'status': 'error',
            'jobs': 0,
            'time': 0,
            'error': str(e)[:50]
        }

async def diagnose_all_scrapers():
    """Diagnose all scrapers quickly"""
    manager = ScraperManager()
    all_scrapers = list(manager.scrapers.keys())
    
    print(f"🔍 Diagnosing all {len(all_scrapers)} scrapers...")
    print("=" * 70)
    
    results = []
    
    # Use a shorter timeout connector
    connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=60)
    timeout = aiohttp.ClientTimeout(total=15, connect=5)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Test scrapers in batches to avoid overwhelming
        batch_size = 5
        for i in range(0, len(all_scrapers), batch_size):
            batch = all_scrapers[i:i+batch_size]
            
            print(f"\nTesting batch {i//batch_size + 1}: {', '.join(batch)}")
            
            # Test batch concurrently with short timeout
            batch_tasks = [
                quick_test_scraper(manager, session, name, timeout=8)
                for name in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, dict):
                    results.append(result)
                    status_icon = {
                        'working': '✅',
                        'no_jobs': '⚠️ ',
                        'timeout': '⏰',
                        'error': '❌'
                    }.get(result['status'], '❓')
                    
                    print(f"  {status_icon} {result['name']}: {result['jobs']} jobs ({result['time']}s)")
                    if result['error']:
                        print(f"     Error: {result['error']}")
                else:
                    print(f"  ❌ Unexpected error: {result}")
            
            # Small delay between batches
            await asyncio.sleep(1)
    
    # Summary
    working = [r for r in results if r['status'] == 'working']
    no_jobs = [r for r in results if r['status'] == 'no_jobs']
    timeouts = [r for r in results if r['status'] == 'timeout']
    errors = [r for r in results if r['status'] == 'error']
    
    print("\n" + "=" * 70)
    print("📊 DIAGNOSIS SUMMARY:")
    print(f"   ✅ Working:    {len(working):2d} scrapers")
    print(f"   ⚠️  No jobs:    {len(no_jobs):2d} scrapers")
    print(f"   ⏰ Timeouts:   {len(timeouts):2d} scrapers")
    print(f"   ❌ Errors:     {len(errors):2d} scrapers")
    print(f"   📊 Total:      {len(results):2d} scrapers")
    
    total_jobs = sum(r['jobs'] for r in working)
    print(f"   🎯 Total jobs: {total_jobs}")
    
    # Broken scrapers analysis
    broken = no_jobs + timeouts + errors
    print(f"\n🔴 BROKEN SCRAPERS ({len(broken)}):")
    for result in broken:
        reason = result['error'] or result['status']
        print(f"   ❌ {result['name']}: {reason}")
    
    # Working scrapers
    print(f"\n🟢 WORKING SCRAPERS ({len(working)}):")
    for result in sorted(working, key=lambda x: x['jobs'], reverse=True):
        print(f"   ✅ {result['name']}: {result['jobs']} jobs")
    
    return len(working), len(broken), total_jobs

if __name__ == "__main__":
    working, broken, jobs = asyncio.run(diagnose_all_scrapers())
    print(f"\n🎯 FINAL RESULT: {working} working, {broken} broken, {jobs} total jobs")