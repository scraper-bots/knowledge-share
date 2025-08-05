#!/usr/bin/env python3
"""
Audit script to find hardcoded scrapers that return fake data
"""

import os
import re
from pathlib import Path

def audit_hardcoded_scrapers():
    """Find all scrapers with hardcoded data"""
    
    sources_dir = Path("sources")
    hardcoded_scrapers = []
    suspicious_patterns = []
    
    print("🔍 AUDITING SCRAPERS FOR HARDCODED DATA")
    print("=" * 60)
    
    for py_file in sources_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        try:
            content = py_file.read_text()
            scraper_name = py_file.stem
            issues = []
            
            # Check for obvious hardcoded patterns
            hardcoded_patterns = [
                (r"sample_jobs\s*=", "Contains sample_jobs variable"),
                (r"return pd\.DataFrame\(\s*\[.*\{", "Returns hardcoded DataFrame list"),
                (r"hardcoded|fake|test.*data", "Contains hardcoded/fake/test data comments"),
                (r"TODO.*Replace.*actual", "Has TODO to replace with actual scraping"),
                (r"for now.*returning.*sample", "Explicitly mentions returning sample data"),
                (r"\[\s*\{\s*['\"]company['\"]:\s*['\"][^'\"]+['\"]", "Contains hardcoded job dictionaries")
            ]
            
            for pattern, description in hardcoded_patterns:
                if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                    issues.append(description)
            
            # Check for very small, static return data
            job_dicts = re.findall(r'\{\s*[\'"]company[\'"]:\s*[\'"][^\'\"]+[\'"].*?\}', content, re.DOTALL)
            if len(job_dicts) > 5 and "sample_jobs" in content:
                issues.append("Large hardcoded job list detected")
            
            if issues:
                hardcoded_scrapers.append((scraper_name, issues))
                print(f"❌ {scraper_name}.py:")
                for issue in issues:
                    print(f"   • {issue}")
            else:
                # Check for suspicious but not definitely hardcoded
                suspicious_patterns_check = [
                    (r"return pd\.DataFrame\(\[", "Returns DataFrame with list (check manually)"),
                    (r"jobs.*=.*\[", "Has jobs list assignment (check manually)")
                ]
                
                for pattern, description in suspicious_patterns_check:
                    if re.search(pattern, content):
                        suspicious_patterns.append((scraper_name, description))
        
        except Exception as e:
            print(f"⚠️  Error reading {scraper_name}.py: {e}")
    
    print(f"\n📊 AUDIT RESULTS:")
    print(f"   ❌ Definitely hardcoded: {len(hardcoded_scrapers)} scrapers")
    print(f"   ⚠️  Suspicious patterns: {len(suspicious_patterns)} scrapers")
    
    if suspicious_patterns:
        print(f"\n⚠️  SUSPICIOUS (manual check needed):")
        for scraper_name, description in suspicious_patterns:
            if scraper_name not in [h[0] for h in hardcoded_scrapers]:
                print(f"   ⚠️  {scraper_name}.py: {description}")
    
    return hardcoded_scrapers

def fix_andersen_scraper():
    """Fix the Andersen scraper to actually scrape jobs"""
    print(f"\n🔧 FIXING ANDERSEN SCRAPER...")
    
    andersen_content = '''import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class AndersenScraper(BaseScraper):
    """
    Andersen job scraper - scrapes actual jobs from Andersen careers page
    """
    
    @scraper_error_handler
    async def parse_andersen(self, session):
        logger.info("Started scraping Andersen careers")
        
        url = "https://people.andersenlab.com/vacancies"
        jobs_data = []
        
        try:
            # Fetch the careers page
            response = await self.fetch_url_async(url, session)
            
            if not response:
                logger.warning("Failed to fetch Andersen careers page")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            
            soup = BeautifulSoup(response, 'html.parser')
            
            # Look for job listings (you may need to adjust selectors based on actual page structure)
            job_elements = soup.find_all('div', class_='vacancy-item') or soup.find_all('a', href=lambda x: x and '/vacancy/' in x)
            
            if not job_elements:
                # Try alternative selectors
                job_elements = soup.find_all('a', href=re.compile(r'/vacancy/\\d+'))
            
            for job_element in job_elements:
                try:
                    # Extract job title
                    title_elem = job_element.find('h3') or job_element.find('h2') or job_element.find('.title')
                    if not title_elem:
                        title_elem = job_element
                    
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown Position"
                    
                    # Extract apply link
                    if job_element.name == 'a':
                        apply_link = job_element.get('href')
                    else:
                        link_elem = job_element.find('a')
                        apply_link = link_elem.get('href') if link_elem else None
                    
                    if apply_link and not apply_link.startswith('http'):
                        apply_link = f"https://people.andersenlab.com{apply_link}"
                    
                    if title and apply_link:
                        jobs_data.append({
                            'company': 'Andersen',
                            'vacancy': title,
                            'apply_link': apply_link
                        })
                
                except Exception as e:
                    logger.warning(f"Error parsing job element: {e}")
                    continue
            
            if not jobs_data:
                logger.warning("No jobs found on Andersen careers page")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
            
            logger.info(f"Successfully scraped {len(jobs_data)} jobs from Andersen")
            return pd.DataFrame(jobs_data)
            
        except Exception as e:
            logger.error(f"Error scraping Andersen: {e}")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
'''
    
    with open("sources/andersen.py", "w") as f:
        f.write(andersen_content)
    
    print("✅ Andersen scraper fixed - now scrapes actual jobs")

if __name__ == "__main__":
    hardcoded = audit_hardcoded_scrapers()
    
    if hardcoded:
        print(f"\n🚨 ACTION REQUIRED:")
        print(f"   Found {len(hardcoded)} scrapers with hardcoded data that need fixing")
        
        for scraper_name, issues in hardcoded:
            print(f"   ❌ {scraper_name}.py needs to be updated")
    
    # Fix Andersen scraper
    fix_andersen_scraper()