#!/usr/bin/env python3
"""
Test the new BP scraper
"""

import asyncio
import aiohttp
import logging
from sources.bp import BpScraper

# Enable INFO logging to see details
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_bp():
    """Test BP scraper"""
    print("🧪 Testing BP scraper...")
    
    scraper = BpScraper()
    
    async with aiohttp.ClientSession() as session:
        result = await scraper.parse_bp(session)
        
        print(f"✓ Scraped {len(result)} jobs from BP")
        
        if not result.empty:
            print("\n📋 Jobs found:")
            for i, row in result.iterrows():
                print(f"  {i+1:2d}. {row['vacancy']}")
                print(f"      Link: {row['apply_link']}")
                print()
        else:
            print("❌ No jobs found")

if __name__ == "__main__":
    asyncio.run(test_bp())