#!/usr/bin/env python3
"""
Analyze scraper failures from database after GitHub Actions run
"""

import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432)
    )

def analyze_recent_scraper_run():
    """Analyze the most recent scraper run"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("🔍 ANALYZING GITHUB ACTIONS SCRAPER RUN")
        print("=" * 60)
        
        # Get the most recent scraper run data
        print("📊 Checking recent job insertions...")
        
        # Check jobs inserted in the last 2 hours
        recent_jobs_query = """
        SELECT 
            source,
            COUNT(*) as job_count,
            MAX(created_at) as latest_job,
            MIN(created_at) as earliest_job
        FROM scraper.jobs_jobpost 
        WHERE created_at >= NOW() - INTERVAL '2 hours'
        GROUP BY source
        ORDER BY job_count DESC
        """
        
        cursor.execute(recent_jobs_query)
        recent_jobs = cursor.fetchall()
        
        if recent_jobs:
            print(f"✅ Found jobs from recent run ({len(recent_jobs)} sources active):")
            total_jobs = 0
            active_sources = []
            
            for source, count, latest, earliest in recent_jobs:
                print(f"  ✅ {source}: {count} jobs (latest: {latest.strftime('%H:%M:%S')})")
                total_jobs += count
                active_sources.append(source)
            
            print(f"\n📈 ACTIVE SOURCES SUMMARY:")
            print(f"   Active sources: {len(active_sources)}")
            print(f"   Total jobs: {total_jobs}")
            
            # Check which scrapers should be active but aren't in recent data
            print(f"\n🔍 Checking for missing scrapers...")
            
            # Get all expected scrapers (from scraper_manager or known list)
            expected_scrapers = [
                'banker_az', 'bfb', 'hrcbaku', 'ada', 'cbar', 'azergold', 'jobbox_az', 'hrin_co',
                'azerconnect', 'offer_az', '1is_az', 'vakansiya_biz', 'smartjob_az', 'oilfund_jobs',
                'ziraat', 'dejobs', 'airswift', 'vakansiya_az', 'ekaryera', 'azercosmos', 'arti',
                'jobsearch_az', 'regulator', 'projobs_vacancies', 'revolut', 'isqur', 'hcb',
                'its_gov', 'andersen', 'ishelanlari_az', 'konsis', 'kapitalbank', 'glorri',
                'ejob_az', 'hellojob_az', 'canscreen', 'un_jobs', 'themuse', 'mdm',
                'tabib_vacancies', 'asco', 'boss_az', 'jobfinder', 'isveren_az', 'fintech_farm',
                'is_elanlari_iilkin', 'orion', 'djinni', 'busy', 'abb', 'bank_of_baku_az',
                'baku_electronics', 'bravosupermarket', 'guavapay', 'staffy', 'azercell', 'position_az'
            ]
            
            missing_scrapers = [s for s in expected_scrapers if s not in active_sources]
            
            print(f"\n❌ MISSING/FAILED SCRAPERS ({len(missing_scrapers)}):")
            for scraper in missing_scrapers:
                print(f"   ❌ {scraper}")
            
        else:
            print("⚠️  No recent jobs found. Checking last 24 hours...")
            
            # Check last 24 hours
            last_24h_query = """
            SELECT 
                source,
                COUNT(*) as job_count,
                MAX(created_at) as latest_job
            FROM scraper.jobs_jobpost 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY source
            ORDER BY latest_job DESC
            LIMIT 20
            """
            
            cursor.execute(last_24h_query)
            last_24h_jobs = cursor.fetchall()
            
            if last_24h_jobs:
                print("📊 Jobs from last 24 hours:")
                for source, count, latest in last_24h_jobs:
                    print(f"  {source}: {count} jobs (latest: {latest})")
            else:
                print("❌ No jobs found in last 24 hours")
        
        # Check for any error logs
        print(f"\n🚨 Checking for scraper errors...")
        try:
            error_query = """
            SELECT 
                scraper_name,
                COUNT(*) as error_count,
                MAX(timestamp) as latest_error,
                error_message
            FROM scraper.scraper_errors 
            WHERE timestamp >= NOW() - INTERVAL '2 hours'
            GROUP BY scraper_name, error_message
            ORDER BY error_count DESC
            """
            
            cursor.execute(error_query)
            errors = cursor.fetchall()
            
            if errors:
                print("❌ Recent scraper errors:")
                for scraper, count, latest, message in errors:
                    print(f"   ❌ {scraper}: {message[:60]}... ({count} times)")
            else:
                print("✅ No recent scraper errors in database")
                
        except Exception as e:
            print(f"⚠️  Could not check errors table: {str(e)}")
        
        cursor.close()
        conn.close()
        
        return len(active_sources) if recent_jobs else 0
        
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        print("\n🔧 Make sure your .env file has correct database credentials:")
        print("   DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT")
        return 0

def check_database_status():
    """Check basic database connectivity and schema"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if jobs table exists and has recent data
        cursor.execute("SELECT COUNT(*) FROM scraper.jobs_jobpost WHERE created_at >= NOW() - INTERVAL '1 day'")
        recent_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT source) FROM scraper.jobs_jobpost WHERE created_at >= NOW() - INTERVAL '1 day'")
        recent_sources = cursor.fetchone()[0]
        
        print(f"📊 Database Status:")
        print(f"   Recent jobs (24h): {recent_count}")
        print(f"   Active sources (24h): {recent_sources}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 GitHub Actions Scraper Analysis")
    print("=" * 50)
    
    if check_database_status():
        active_scrapers = analyze_recent_scraper_run()
        
        print(f"\n🎯 FINAL ANALYSIS:")
        if active_scrapers > 30:
            print(f"   ✅ GOOD: {active_scrapers} scrapers active in GitHub Actions")
        elif active_scrapers > 20:
            print(f"   ⚠️  FAIR: {active_scrapers} scrapers active (expected ~30-40)")
        else:
            print(f"   ❌ LOW: Only {active_scrapers} scrapers active (investigate issues)")
    else:
        print("❌ Could not connect to database for analysis")