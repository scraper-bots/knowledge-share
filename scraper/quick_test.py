#!/usr/bin/env python3
"""
Quick test to verify basic functionality without database dependencies
"""

import asyncio
import sys
import os
import aiohttp

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_scrapers_basic():
    """Test basic scraper functionality"""
    print("Testing basic scraper functionality...")
    
    try:
        # Test 1: Import modules
        print("1. Testing imports...")
        from scraper_manager import ScraperManager
        print("   ✅ ScraperManager imported")
        
        # Test 2: Load scrapers
        print("2. Loading scrapers...")
        manager = ScraperManager()
        print(f"   ✅ Loaded {len(manager.scrapers)} scrapers")
        
        if len(manager.scrapers) == 0:
            print("   ❌ No scrapers loaded!")
            return False
        
        # Test 3: Show scraper list
        print("3. Available scrapers:")
        scraper_names = list(manager.scrapers.keys())
        for i, name in enumerate(scraper_names[:10], 1):
            print(f"   {i}. {name}")
        if len(scraper_names) > 10:
            print(f"   ... and {len(scraper_names) - 10} more")
        
        # Test 4: Test one scraper (without database)
        print("4. Testing individual scraper...")
        test_scraper_name = scraper_names[0]
        print(f"   Testing: {test_scraper_name}")
        
        async with aiohttp.ClientSession() as session:
            try:
                result = await manager.run_single_scraper(test_scraper_name, session)
                
                if hasattr(result, '__len__'):
                    print(f"   ✅ Scraper returned data: {len(result)} items")
                    
                    if len(result) > 0:
                        print("   📋 Sample data structure:")
                        if hasattr(result, 'columns'):
                            print(f"      Columns: {list(result.columns)}")
                            if not result.empty:
                                sample = result.iloc[0]
                                print("      Sample record:")
                                for col, val in sample.items():
                                    print(f"        {col}: {str(val)[:50]}...")
                    return True
                else:
                    print(f"   ⚠️ Scraper returned: {type(result)}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Scraper failed: {str(e)}")
                return False
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def test_base_scraper():
    """Test base scraper functionality"""
    print("\nTesting base scraper...")
    
    try:
        from base_scraper import BaseScraper
        
        # Test source determination
        base = BaseScraper()
        
        test_urls = [
            "https://glorri.az/jobs/123",
            "https://careers.azercell.com/job/456", 
            "https://djinni.co/jobs/789",
            "https://unknown-site.com/job"
        ]
        
        print("Testing source determination:")
        for url in test_urls:
            source = base.determine_source(url)
            print(f"   {url} -> {source}")
        
        return True
        
    except Exception as e:
        print(f"❌ Base scraper test failed: {e}")
        return False

async def main():
    """Run basic tests"""
    print("Quick Scraper Functionality Test")
    print("=" * 50)
    
    test1 = await test_scrapers_basic()
    test2 = await test_base_scraper()
    
    print("\n" + "=" * 50)
    print("QUICK TEST SUMMARY")
    print("=" * 50)
    
    if test1 and test2:
        print("✅ Basic functionality works!")
        print("✅ Ready for comprehensive testing")
        print("\nNext steps:")
        print("1. Ensure database credentials are set")
        print("2. Run: python comprehensive_test.py")
    else:
        print("❌ Basic functionality issues detected")
        print("❌ Fix these issues before running full tests")
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())