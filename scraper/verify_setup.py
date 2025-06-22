#!/usr/bin/env python3
"""
Quick verification script to check modular scraper setup
"""

import os
import sys

def check_files():
    """Check if all required files exist"""
    print("Checking file structure...")
    
    required_files = [
        'base_scraper.py',
        'scraper_manager.py', 
        'scraper.py',
        'sources/__init__.py'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            return False
    
    # Check sources directory
    sources_dir = 'sources'
    if os.path.exists(sources_dir):
        py_files = [f for f in os.listdir(sources_dir) if f.endswith('.py') and f != '__init__.py']
        print(f"✅ sources/ directory with {len(py_files)} scraper files")
        
        if len(py_files) >= 50:
            print(f"✅ Sufficient scrapers found ({len(py_files)})")
        else:
            print(f"⚠️  Only {len(py_files)} scrapers found, expected 50+")
    else:
        print(f"❌ sources/ directory - MISSING")
        return False
    
    return True

def check_imports():
    """Check if modules can be imported"""
    print("\nChecking imports...")
    
    try:
        from base_scraper import BaseScraper
        print("✅ base_scraper imports successfully")
    except ImportError as e:
        print(f"❌ base_scraper import failed: {e}")
        return False
    
    try:
        from scraper_manager import ScraperManager
        print("✅ scraper_manager imports successfully")
    except ImportError as e:
        print(f"❌ scraper_manager import failed: {e}")
        return False
    
    try:
        import scraper
        print("✅ scraper imports successfully")
    except ImportError as e:
        print(f"❌ scraper import failed: {e}")
        return False
    
    return True

def check_scraper_loading():
    """Check if scrapers can be loaded"""
    print("\nChecking scraper loading...")
    
    try:
        from scraper_manager import ScraperManager
        manager = ScraperManager()
        
        loaded_count = len(manager.scrapers)
        print(f"✅ Loaded {loaded_count} scrapers")
        
        if loaded_count >= 50:
            print("✅ Sufficient scrapers loaded")
            
            # Show some examples
            sample_scrapers = list(manager.scrapers.keys())[:5]
            print(f"   Sample scrapers: {', '.join(sample_scrapers)}")
            return True
        else:
            print(f"⚠️  Only {loaded_count} scrapers loaded, expected 50+")
            return False
            
    except Exception as e:
        print(f"❌ Failed to load scrapers: {e}")
        return False

def check_environment():
    """Check environment variables"""
    print("\nChecking environment variables...")
    
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    optional_vars = ['EMAIL', 'PASSWORD']
    
    all_present = True
    
    for var in required_vars:
        if var in os.environ:
            print(f"✅ {var}")
        else:
            print(f"❌ {var} - MISSING")
            all_present = False
    
    for var in optional_vars:
        if var in os.environ:
            print(f"✅ {var} (optional)")
        else:
            print(f"⚠️  {var} - MISSING (optional)")
    
    return all_present

def main():
    """Run all verification checks"""
    print("Modular Scraper Setup Verification")
    print("=" * 40)
    
    checks = [
        ("File Structure", check_files),
        ("Module Imports", check_imports), 
        ("Scraper Loading", check_scraper_loading),
        ("Environment Variables", check_environment)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        print("-" * 20)
        result = check_func()
        results.append((check_name, result))
    
    # Summary
    print(f"\n{'='*40}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*40}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! Setup is ready for testing.")
        print("\nNext steps:")
        print("1. Ensure database is accessible")
        print("2. Run: python test_modular_scraper.py")
        print("3. Run: python scraper.py (to test full scraping)")
    else:
        print("⚠️  Some checks failed. Please fix the issues above before proceeding.")
    
    print(f"{'='*40}")

if __name__ == "__main__":
    main()