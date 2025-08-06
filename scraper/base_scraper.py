import urllib3
import os
import aiohttp
import asyncio
import pandas as pd
import psycopg2
from psycopg2 import sql, extras
from psycopg2.extras import RealDictCursor
import json
import re
import random
from bs4 import BeautifulSoup
import logging
from typing import Optional, Union, Dict, Any, Callable
from functools import wraps
import chardet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def scraper_error_handler(func: Callable) -> Callable:
    """Decorator to handle errors in scraper methods"""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except BaseException as e:
            # Use BaseException to catch all possible exceptions
            logger.error(f"Error in {func.__name__}: {str(e)}")
            # Return empty DataFrame to maintain consistency
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
    return wrapper


class BaseScraper:
    def __init__(self):
        self.data = []
        self.credentials = self.load_credentials()
        self.db_params = self.load_db_credentials()

    def load_credentials(self):
        """Load email and password from environment variables"""
        return {
            'email': os.getenv('EMAIL'),
            'password': os.getenv('PASSWORD')
        }

    def load_db_credentials(self):
        """Load database credentials from environment variables"""
        return {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'options': f"-c search_path={os.getenv('DB_SCHEMA', 'public')}"
        }

    async def log_scraper_error(self, scraper_name: str, error_message: str, url: str = None, retry_count: int = 0):
        """Log scraper errors to database"""
        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            # Try the new schema first, fallback to simple logging
            try:
                insert_query = """
                    INSERT INTO scraper.scraper_errors (scraper_name, error_message, url, retry_count, timestamp)
                    VALUES (%s, %s, %s, %s, NOW())
                """
                cursor.execute(insert_query, (scraper_name, error_message, url, retry_count))
            except psycopg2.Error:
                # Fallback to simpler error logging
                insert_query = """
                    INSERT INTO scraper.scraper_errors (error_message, timestamp)
                    VALUES (%s, NOW())
                """
                cursor.execute(insert_query, (f"{scraper_name}: {error_message}",))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            # Just log to console if database logging fails
            logger.error(f"Scraper error ({scraper_name}): {error_message}")

    async def fetch_url_async(self, url: str, session: aiohttp.ClientSession, params=None, headers=None, verify_ssl=True, max_retries: int = 3) -> str:
        """Asynchronously fetch URL content with enhanced retry logic for CI environments"""
        
        # Detect if running in GitHub Actions
        is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        
        # Enhanced headers for CI environments
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        request_headers = {**default_headers, **(headers or {})}
        
        # Enhanced retry logic for CI environments
        if is_github_actions:
            max_retries = min(max_retries, 2)  # Reduce retries in CI to avoid timeouts
        
        for attempt in range(max_retries):
            try:
                # Increased timeout for CI environments
                timeout_duration = 45 if is_github_actions else 30
                timeout = aiohttp.ClientTimeout(total=timeout_duration, connect=15)
                
                async with session.get(url, params=params, headers=request_headers, ssl=verify_ssl, timeout=timeout) as response:
                    if response.status == 200:
                        # Handle different content types
                        content_type = response.headers.get('Content-Type', '').lower()
                        
                        if 'application/json' in content_type:
                            return await response.json()
                        else:
                            content = await response.read()
                            # Try to decode with UTF-8 first
                            try:
                                return content.decode('utf-8')
                            except UnicodeDecodeError:
                                # Detect encoding if UTF-8 fails
                                detected = chardet.detect(content)
                                encoding = detected.get('encoding', 'utf-8')
                                return content.decode(encoding, errors='ignore')
                    elif response.status in [403, 429, 503]:  # Common CI blocking statuses
                        if is_github_actions:
                            # Longer backoff in CI environments
                            wait_time = min((3 ** attempt) + random.uniform(1, 3), 15)
                        else:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return ""
            except (asyncio.TimeoutError, aiohttp.ClientTimeout) as e:
                if attempt < max_retries - 1:
                    # Extended backoff for timeout errors in CI
                    wait_time = (3 ** attempt) + random.uniform(2, 5) if is_github_actions else (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Timeout fetching {url} after {max_retries} attempts: {str(e)}")
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(1, 2) if is_github_actions else (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts: {str(e)}")
        return ""

    def determine_source(self, apply_link: str) -> str:
        """
        Determine the source based on the apply_link pattern.
        This uses the patterns from monitoring.sql.
        """
        source_patterns = {
            'Smartjob': '%smartjob%',
            'Glorri': '%glorri%',
            'Azercell': '%azercell%',
            'Azerconnect': '%oraclecloud%',
            'Djinni': '%djinni%',
            'ABB': '%abb-bank%',
            'HelloJob': '%hellojob%',
            'Boss.az': '%boss.az%',
            'eJob': '%ejob%',
            'Vakansiya.az': '%vakansiya.az%',
            'Ishelanlari': '%ishelanlari%',
            'Is-elanlari':'%is-elanlari%',
            'Banker.az': '%banker%',
            'Offer.az': '%offer.az%',
            'Isveren': '%isveren%',
            'Isqur': '%isqur%',
            'Kapital Bank': '%kapitalbank%',
            'Bank of Baku': '%bankofbaku%',
            'Jobbox': '%jobbox%',
            'Vakansiya.biz': '%vakansiya.biz%',
            'ITS Gov': '%its.gov%',
            'TABIB': '%tabib%',
            'ProJobs': '%projobs%',
            'AzerGold': '%azergold%',
            'Konsis': '%konsis%',
            'Baku Electronics': '%bakuelectronics.az%',
            'ASCO': '%asco%',
            'CBAR': '%cbar%',
            'ADA': '%ada.edu%',
            'JobFinder': '%jobfinder%',
            'Regulator': '%regulator%',
            'eKaryera': '%ekaryera%',
            'Bravo': '%bravosupermarket%',
            'MDM': '%mdm.gov%',
            'ARTI': '%arti.edu%',
            'Staffy': '%staffy%',
            'Position.az': '%position.az%',
            'HRIN': '%hrin.az%',
            'UN Jobs': '%un.org%',
            'Oil Fund': '%oilfund%',
            '1is.az': '%1is.az%',
            'The Muse': '%themuse%',
            'DEJobs': '%dejobs%',
            'HCB': '%hcb.az%',
            'BFB': '%bfb.az%',
            'Airswift': '%airswift%',
            'Orion': '%orionjobs%',
            'HRC Baku': '%hrcbaku%',
            'JobSearch': '%jobsearch%',
            'CanScreen': '%canscreen%',
            'Azercosmos': '%azercosmos%',
            'Fintech Farm': '%fintech-farm%',
            'Busy': '%busy%',
            'Ziraat': '%ziraat%',
            'Guavapay': '%guavalab%',
            'Revolut': '%revolut%',
            'Andersen': '%andersenlab%',
            'PashaPay': '%pashapay.huntflow%',
            'BP': '%bp.com%',
        }
        
        if not apply_link:
            return 'Unknown'
            
        # Extract domain from URL to avoid false matches in URL paths
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(apply_link)
            domain = parsed_url.netloc.lower()
        except Exception:
            # Fallback to original method if URL parsing fails
            domain = apply_link.lower()
        
        for source, pattern in source_patterns.items():
            # Convert SQL-style pattern to Python regex pattern
            regex_pattern = pattern.replace('%', '.*')
            if re.search(regex_pattern, domain, re.IGNORECASE):
                return source
                
        return 'Other'  # Default source if no pattern matches

    def save_to_db(self, df: pd.DataFrame, batch_size: int = 100):
        """Save DataFrame to database - matches original behavior exactly"""
        if df.empty:
            logger.warning("No data to save to the database.")
            return

        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    # Start transaction
                    conn.autocommit = False
                    
                    try:
                        # Step 1: Purify data by removing duplicates and invalid entries
                        df = df.copy()
                        df = df.drop_duplicates(subset=['company', 'vacancy', 'apply_link'])
                        
                        # Filter out rows where all values are 'n/a'
                        df = df[~((df['company'] == 'n/a') & 
                                (df['vacancy'] == 'n/a') & 
                                (df['apply_link'] == 'n/a'))]
                        
                        # Add source column based on apply_link patterns
                        df['source'] = df['apply_link'].apply(self.determine_source)
                        
                        # Step 2: Delete all existing data - COMPLETE REPLACEMENT
                        logger.info("Deleting all existing data from scraper.jobs_jobpost table...")
                        delete_query = sql.SQL("TRUNCATE TABLE scraper.jobs_jobpost CASCADE")
                        cur.execute(delete_query)
                        
                        # Step 3: Insert new data with proper column mapping
                        logger.info(f"Inserting {len(df)} new records...")
                        values = [
                            (
                                row.get('vacancy', '')[:500],  # vacancy -> title
                                row.get('company', '')[:500],   # company -> company
                                row.get('apply_link', '')[:1000],  # apply_link -> apply_link
                                row.get('source', '')[:100]     # source -> source
                            )
                            for _, row in df.iterrows()
                        ]
                        
                        insert_query = sql.SQL("""
                            INSERT INTO scraper.jobs_jobpost (title, company, apply_link, source)
                            VALUES %s
                        """)
                        extras.execute_values(cur, insert_query, values, page_size=batch_size)
                        
                        # Commit transaction
                        conn.commit()
                        logger.info(f"Successfully replaced data with {len(df)} job posts.")
                        
                    except Exception as e:
                        conn.rollback()
                        logger.error(f"Error during database operation: {e}")
                        raise
                            
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(f"Error saving data to the database: {error}")