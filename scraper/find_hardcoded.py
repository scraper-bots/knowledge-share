#!/usr/bin/env python3
"""
Find all hardcoded scrapers in the codebase
"""

import os
import re
from pathlib import Path

def find_hardcoded_scrapers():
    """Find all scrapers with hardcoded data"""
    
    sources_dir = Path("sources")
    hardcoded_scrapers = []
    
    print("🔍 SCANNING FOR HARDCODED SCRAPERS")
    print("=" * 50)
    
    for py_file in sources_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        try:
            content = py_file.read_text()
            scraper_name = py_file.stem
            
            # Look for hardcoded DataFrame patterns
            hardcoded_patterns = [
                r"return pd\.DataFrame\(\s*\[\s*\{",  # return pd.DataFrame([{
                r"sample_jobs\s*=\s*\[",              # sample_jobs = [
                r"jobs_data\s*=\s*\[\s*\{.*company.*vacancy.*apply_link",  # hardcoded job dictionaries
                r"fake.*data|test.*data|hardcoded",   # comments indicating fake data
                r"TODO.*Replace.*actual"              # TODO comments
            ]
            
            is_hardcoded = False
            reasons = []
            
            for pattern in hardcoded_patterns:
                if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                    is_hardcoded = True
                    if "sample_jobs" in pattern:
                        reasons.append("Has sample_jobs variable")
                    elif "return pd.DataFrame" in pattern:
                        reasons.append("Returns hardcoded DataFrame")
                    elif "TODO" in pattern:
                        reasons.append("Has TODO to implement real scraping")
                    else:
                        reasons.append("Contains hardcoded data patterns")
            
            if is_hardcoded:
                hardcoded_scrapers.append((scraper_name, reasons))
                print(f"❌ {scraper_name}.py")
                for reason in reasons:
                    print(f"   • {reason}")
            
        except Exception as e:
            print(f"⚠️  Error reading {scraper_name}.py: {e}")
    
    print(f"\n📊 RESULTS:")
    print(f"   Found {len(hardcoded_scrapers)} hardcoded scrapers")
    
    if hardcoded_scrapers:
        print(f"\n🚨 HARDCODED SCRAPERS TO FIX:")
        for scraper_name, reasons in hardcoded_scrapers:
            print(f"   ❌ {scraper_name}")
    
    return hardcoded_scrapers

if __name__ == "__main__":
    hardcoded = find_hardcoded_scrapers()
    
    if hardcoded:
        print(f"\n⚠️  ACTION REQUIRED:")
        print(f"   {len(hardcoded)} scrapers need to be converted from hardcoded to real scraping")
    else:
        print(f"\n✅ All scrapers appear to be implementing real scraping!")