#!/usr/bin/env python3
"""
Disable hardcoded scrapers by making them return empty DataFrames
"""

import os
import re
from pathlib import Path

def disable_hardcoded_scrapers():
    """Replace hardcoded data with empty DataFrame returns"""
    
    sources_dir = Path("sources")
    
    # Known hardcoded scrapers (add more as you find them)
    hardcoded_files = []
    
    print("🔧 DISABLING HARDCODED SCRAPERS")
    print("=" * 40)
    
    for py_file in sources_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        try:
            content = py_file.read_text()
            original_content = content
            scraper_name = py_file.stem
            
            # Skip the already fixed andersen scraper
            if scraper_name == "andersen":
                continue
            
            # Look for hardcoded patterns and replace them
            patterns_to_replace = [
                # Pattern 1: sample_jobs = [...]
                (r'sample_jobs\s*=\s*\[.*?\]', 
                 'return pd.DataFrame(columns=[\'company\', \'vacancy\', \'apply_link\'])  # Disabled hardcoded data'),
                
                # Pattern 2: return pd.DataFrame([{...}])
                (r'return pd\.DataFrame\(\s*\[\s*\{.*?\}\s*\]\s*\)', 
                 'return pd.DataFrame(columns=[\'company\', \'vacancy\', \'apply_link\'])  # Disabled hardcoded data'),
                
                # Pattern 3: jobs_data = [{...}] followed by return
                (r'jobs_data\s*=\s*\[\s*\{.*?\}\s*\].*?return pd\.DataFrame\(jobs_data\)', 
                 'return pd.DataFrame(columns=[\'company\', \'vacancy\', \'apply_link\'])  # Disabled hardcoded data')
            ]
            
            modified = False
            for pattern, replacement in patterns_to_replace:
                if re.search(pattern, content, re.DOTALL):
                    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                    modified = True
            
            if modified:
                # Write the modified content back
                py_file.write_text(content)
                hardcoded_files.append(scraper_name)
                print(f"✅ Disabled hardcoded data in {scraper_name}.py")
            
        except Exception as e:
            print(f"⚠️  Error processing {scraper_name}.py: {e}")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Disabled {len(hardcoded_files)} hardcoded scrapers")
    
    if hardcoded_files:
        print(f"\n🔧 DISABLED SCRAPERS:")
        for scraper in hardcoded_files:
            print(f"   • {scraper}")
        
        print(f"\n⚠️  These scrapers now return empty results.")
        print(f"   Implement real scraping logic for each one.")
    
    return hardcoded_files

if __name__ == "__main__":
    disabled = disable_hardcoded_scrapers()
    
    if disabled:
        print(f"\n🎯 NEXT STEPS:")
        print(f"   1. Test your scrapers - hardcoded ones will return 0 jobs")
        print(f"   2. Implement real scraping for each disabled scraper")
        print(f"   3. Clean database of any existing hardcoded entries")
    else:
        print(f"\n✅ No hardcoded scrapers found to disable!")