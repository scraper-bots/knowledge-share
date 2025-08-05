#!/usr/bin/env python3
"""
Test the enhanced logging system with a limited set of scrapers
"""

import asyncio
import os
from scraper_manager import ScraperManager

# Simulate GitHub Actions environment for testing
os.environ['GITHUB_ACTIONS'] = 'true'

async def test_logging():
    """Test the logging system with just a few scrapers"""
    manager = ScraperManager()
    
    # Run just 3 scrapers to see the output quickly
    original_scrapers = manager.scrapers.copy()
    test_scrapers = {}
    
    # Pick 3 scrapers for testing
    scraper_names = list(original_scrapers.keys())[:3]
    for name in scraper_names:
        test_scrapers[name] = original_scrapers[name]
    
    manager.scrapers = test_scrapers
    
    print("🧪 Testing enhanced logging with GitHub Actions format...")
    print(f"Selected scrapers for test: {list(test_scrapers.keys())}")
    
    # Run the scrapers
    result = await manager.run_all_scrapers(max_concurrent=2)
    
    print(f"\n📊 Test completed - got {len(result)} total jobs")

if __name__ == "__main__":
    asyncio.run(test_logging())