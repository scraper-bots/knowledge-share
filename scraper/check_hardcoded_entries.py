#!/usr/bin/env python3
"""
Check database for hardcoded job entries that need to be removed
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

def check_for_hardcoded_entries():
    """Check for potentially hardcoded job entries"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("🔍 CHECKING FOR HARDCODED JOB ENTRIES")
        print("=" * 50)
        
        # Look for the specific hardcoded Andersen jobs the user mentioned
        hardcoded_andersen_titles = [
            "Senior Java Developer",
            "Frontend Developer (React)",
            "DevOps Engineer",
            "Business Analyst",
            "QA Engineer",
            "Product Manager",
            "UI/UX Designer",
            "Data Scientist",
            "Marketing Specialist",
            "HR Manager"
        ]
        
        print("🔍 Checking for specific hardcoded Andersen jobs...")
        
        for job_title in hardcoded_andersen_titles:
            cursor.execute("""
                SELECT id, title, company, apply_link, created_at 
                FROM scraper.jobs_jobpost 
                WHERE company = 'Andersen' AND title = %s
                ORDER BY created_at DESC
                LIMIT 5
            """, (job_title,))
            
            results = cursor.fetchall()
            if results:
                print(f"  ❌ Found hardcoded job: '{job_title}' ({len(results)} entries)")
                for job_id, title, company, link, created in results:
                    print(f"    ID: {job_id}, Created: {created}, Link: {link}")
        
        # Check for suspicious patterns
        print(f"\n🔍 Checking for suspicious job patterns...")
        
        # Look for jobs with generic apply links
        cursor.execute("""
            SELECT company, COUNT(*) as count
            FROM scraper.jobs_jobpost 
            WHERE apply_link = 'https://people.andersenlab.com/careers'
               OR apply_link = 'https://www.revolut.com/careers'
               OR apply_link LIKE '%/careers' 
            GROUP BY company
            HAVING COUNT(*) > 10
            ORDER BY count DESC
        """)
        
        generic_links = cursor.fetchall()
        if generic_links:
            print("  ⚠️  Companies with generic career page links:")
            for company, count in generic_links:
                print(f"    {company}: {count} jobs with generic links")
        
        # Check for duplicate job titles from same company
        cursor.execute("""
            SELECT company, title, COUNT(*) as count
            FROM scraper.jobs_jobpost 
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY company, title
            HAVING COUNT(*) > 5
            ORDER BY count DESC
            LIMIT 20
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"\n  ⚠️  Potential duplicate jobs (same title, same company):")
            for company, title, count in duplicates:
                print(f"    {company}: '{title}' ({count} entries)")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ Database check completed")
        
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")

if __name__ == "__main__":
    check_for_hardcoded_entries()