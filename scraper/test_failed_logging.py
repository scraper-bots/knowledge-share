#!/usr/bin/env python3
"""
Test the enhanced logging system with scrapers that are likely to fail
"""

import asyncio
import os
from scraper_manager import ScraperManager

# Simulate GitHub Actions environment for testing
os.environ['GITHUB_ACTIONS'] = 'true'

async def test_failed_logging():
    """Test the logging system with scrapers that are likely to fail"""
    manager = ScraperManager()
    
    # Run scrapers that are known to have issues based on our previous analysis
    original_scrapers = manager.scrapers.copy()
    test_scrapers = {}
    
    # Pick scrapers that are likely to fail or have issues
    problem_scrapers = ['jobbox_az', 'ekaryera', 'isqur', 'andersen', 'revolut']
    
    for name in problem_scrapers:
        if name in original_scrapers:
            test_scrapers[name] = original_scrapers[name]
    
    manager.scrapers = test_scrapers
    
    print("🧪 Testing failure logging with problematic scrapers...")
    print(f"Selected problem scrapers: {list(test_scrapers.keys())}")
    
    # Run the scrapers
    result = await manager.run_all_scrapers(max_concurrent=2)
    
    print(f"\n📊 Test completed - got {len(result)} total jobs")
    print(f"Failed scrapers: {len(manager.failed_scrapers)}")
    
    # Show failed scrapers details outside of the logging system
    if manager.failed_scrapers:
        print(f"\n🔍 Detailed failure analysis:")
        for name, info in manager.failed_scrapers.items():
            print(f"  {name}: {info['status']} - {info.get('error', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(test_failed_logging())