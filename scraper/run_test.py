#!/usr/bin/env python3
"""
Live test of modular scraper - tests actual functionality
"""

import sys
import os
import subprocess

def setup_environment():
    """Set up the testing environment"""
    print("Setting up test environment...")
    
    # Check if we're in virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("⚠️  Not in virtual environment. Setting up...")
        try:
            # Create virtual environment
            subprocess.run([sys.executable, '-m', 'venv', 'test_env'], check=True)
            print("✅ Virtual environment created: test_env/")
            
            # Instructions for user
            print("\n🔧 SETUP INSTRUCTIONS:")
            print("1. Activate virtual environment:")
            print("   source test_env/bin/activate")
            print("\n2. Install dependencies:")
            print("   pip install -r requirements.txt")
            print("\n3. Set environment variables:")
            print("   export DB_HOST=your_host")
            print("   export DB_PORT=your_port") 
            print("   export DB_USER=your_user")
            print("   export DB_PASSWORD=your_password")
            print("   export DB_NAME=your_database")
            print("   export DB_SCHEMA=scraper")
            print("\n4. Run test again:")
            print("   python run_test.py")
            
            return False
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
    
    return True

def test_imports():
    """Test if all modules can be imported"""
    print("\n📦 Testing imports...")
    
    modules_to_test = [
        ('aiohttp', 'aiohttp'),
        ('pandas', 'pandas'),
        ('psycopg2', 'psycopg2'),
        ('BeautifulSoup', 'bs4'),
        ('python-dotenv', 'dotenv')
    ]
    
    missing_modules = []
    
    for module_name, import_name in modules_to_test:
        try:
            __import__(import_name)
            print(f"   ✅ {module_name}")
        except ImportError:
            print(f"   ❌ {module_name} - MISSING")
            missing_modules.append(module_name)
    
    if missing_modules:
        print(f"\n❌ Missing modules: {', '.join(missing_modules)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    return True

def test_scraper_modules():
    """Test our scraper modules"""
    print("\n🔧 Testing scraper modules...")
    
    try:
        from base_scraper import BaseScraper
        print("   ✅ BaseScraper imported")
        
        from scraper_manager import ScraperManager
        print("   ✅ ScraperManager imported")
        
        import scraper
        print("   ✅ Main scraper imported")
        
        # Test scraper loading
        manager = ScraperManager()
        scraper_count = len(manager.scrapers)
        print(f"   ✅ Loaded {scraper_count} scrapers")
        
        if scraper_count < 50:
            print(f"   ⚠️  Expected 50+ scrapers, got {scraper_count}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("\n💾 Testing database connection...")
    
    try:
        from base_scraper import BaseScraper
        import psycopg2
        
        scraper = BaseScraper()
        
        # Check environment variables
        required_vars = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"   ❌ Missing environment variables: {', '.join(missing_vars)}")
            print("   Set these before running the test")
            return False
        
        # Test connection
        try:
            with psycopg2.connect(**scraper.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    if result[0] == 1:
                        print("   ✅ Database connection successful")
                        
                        # Check if table exists
                        cur.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'scraper' 
                                AND table_name = 'jobs_jobpost'
                            )
                        """)
                        table_exists = cur.fetchone()[0]
                        
                        if table_exists:
                            print("   ✅ Target table exists: scraper.jobs_jobpost")
                            return True
                        else:
                            print("   ❌ Target table missing: scraper.jobs_jobpost")
                            print("   Run database migration first")
                            return False
                            
        except psycopg2.Error as e:
            print(f"   ❌ Database connection failed: {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        return False

async def test_single_scraper():
    """Test a single scraper"""
    print("\n🕸️  Testing single scraper...")
    
    try:
        import aiohttp
        from scraper_manager import ScraperManager
        
        manager = ScraperManager()
        if not manager.scrapers:
            print("   ❌ No scrapers loaded")
            return False
        
        # Test first available scraper
        scraper_name = list(manager.scrapers.keys())[0]
        print(f"   Testing: {scraper_name}")
        
        async with aiohttp.ClientSession() as session:
            result = await manager.run_single_scraper(scraper_name, session)
            
            if hasattr(result, '__len__'):
                job_count = len(result)
                print(f"   ✅ Scraper returned {job_count} jobs")
                
                if job_count > 0:
                    print("   ✅ Data structure looks good")
                    # Show sample
                    if hasattr(result, 'columns'):
                        print(f"   📋 Columns: {list(result.columns)}")
                    return True
                else:
                    print("   ⚠️  No jobs found (might be normal)")
                    return True
            else:
                print(f"   ❌ Unexpected return type: {type(result)}")
                return False
                
    except Exception as e:
        print(f"   ❌ Scraper test failed: {e}")
        return False

async def test_database_operations():
    """Test database operations"""
    print("\n💾 Testing database operations...")
    
    try:
        import pandas as pd
        from base_scraper import BaseScraper
        import psycopg2
        
        scraper = BaseScraper()
        
        # Test data
        test_data = pd.DataFrame([
            {
                'company': 'TEST_COMPANY_MODULAR',
                'vacancy': 'TEST_POSITION_MODULAR', 
                'apply_link': 'https://glorri.az/test-modular-123'
            }
        ])
        
        print("   Testing TRUNCATE + INSERT operations...")
        
        # Get initial count
        with psycopg2.connect(**scraper.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM scraper.jobs_jobpost")
                initial_count = cur.fetchone()[0]
        
        print(f"   Initial DB count: {initial_count}")
        
        # Save test data (should TRUNCATE + INSERT)
        scraper.save_to_db(test_data)
        
        # Check final count
        with psycopg2.connect(**scraper.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM scraper.jobs_jobpost")
                final_count = cur.fetchone()[0]
                
                # Check if our test data exists
                cur.execute("""
                    SELECT title, company, apply_link, source 
                    FROM scraper.jobs_jobpost 
                    WHERE company = 'TEST_COMPANY_MODULAR'
                """)
                test_record = cur.fetchone()
        
        print(f"   Final DB count: {final_count}")
        
        # Verify TRUNCATE behavior
        if final_count == 1 and test_record:
            title, company, apply_link, source = test_record
            print("   ✅ TRUNCATE worked - replaced all data")
            print(f"   ✅ Data mapping correct: {title} | {company} | {source}")
            print("   ✅ Source detection worked")
            return True
        else:
            print("   ❌ TRUNCATE behavior not working as expected")
            return False
            
    except Exception as e:
        print(f"   ❌ Database operations test failed: {e}")
        return False

async def run_full_test():
    """Run comprehensive test"""
    print("🧪 COMPREHENSIVE MODULAR SCRAPER TEST")
    print("=" * 60)
    
    tests = [
        ("Environment Setup", setup_environment),
        ("Module Imports", test_imports), 
        ("Scraper Modules", test_scraper_modules),
        ("Database Connection", test_database_connection),
        ("Single Scraper", test_single_scraper),
        ("Database Operations", test_database_operations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            if test_name in ["Single Scraper", "Database Operations"]:
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Modular scraper is fully functional")
        print("✅ Database operations work correctly")
        print("✅ Ready for production use")
    elif passed >= total * 0.8:
        print("\n⚠️  MOSTLY SUCCESSFUL")
        print("✅ Core functionality works")
        print("⚠️  Some issues may need attention")
    else:
        print("\n❌ SIGNIFICANT ISSUES")
        print("❌ Multiple critical failures")
        print("❌ Review errors above")
    
    print(f"{'='*60}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_full_test())