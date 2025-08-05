#!/usr/bin/env python3
"""
Check the actual table structure and column names
"""

import psycopg2
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

def check_table_structure():
    """Check table structure"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("🔍 CHECKING TABLE STRUCTURE")
        print("=" * 40)
        
        # Get table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'scraper' AND table_name = 'jobs_jobpost'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        if columns:
            print("📊 Table: scraper.jobs_jobpost")
            print("Columns:")
            for col_name, data_type, nullable in columns:
                print(f"  • {col_name} ({data_type}) - {'NULL' if nullable == 'YES' else 'NOT NULL'}")
        
        # Get sample data to understand structure
        cursor.execute("SELECT * FROM scraper.jobs_jobpost LIMIT 3")
        sample_data = cursor.fetchall()
        
        if sample_data:
            print(f"\n📝 Sample data (first 3 rows):")
            col_names = [desc[0] for desc in cursor.description]
            print(f"Columns: {col_names}")
            for i, row in enumerate(sample_data, 1):
                print(f"Row {i}: {row}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_table_structure()