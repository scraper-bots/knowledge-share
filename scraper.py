#!/usr/bin/env python3
"""
Simple startup details scraper for knowledge-share.eu
Scrapes all startup details without images or HTML content
"""

import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StartupDetailsScraper:
    """Scraper for startup details only"""
    
    BASE_URL = "https://www.knowledge-share.eu"
    LISTINGS_API = f"{BASE_URL}/api/pages/"
    
    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self.session = requests.Session()
        
        # Set required headers
        self.session.headers.update({
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'en',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'referer': 'https://www.knowledge-share.eu/en/start-ups',
            'cookie': 'sessionid=xqwssxzsexmi4kxif427o2zqlmrzgmpb'
        })
    
    def get_all_startup_urls(self):
        """Get all startup detail URLs from listings API"""
        detail_urls = []
        offset = 0
        limit = 50
        
        logger.info("Getting startup URLs...")
        
        while True:
            params = {
                'limit': str(limit),
                'offset': str(offset),
                'site': 'www.knowledge-share.eu',
                'order': '-first_published_at',
                'fields': 'abstract,categories,funding_stage,initiative,looking_for,options,preview_image,title,trl',
                'locale': 'en',
                'type': 'startups.StartUpPage'
            }
            
            try:
                response = self.session.get(self.LISTINGS_API, params=params)
                response.raise_for_status()
                data = response.json()
                
                items = data.get('items', [])
                if not items:
                    break
                
                for item in items:
                    detail_urls.append({
                        'id': item['id'],
                        'title': item['title'],
                        'detail_url': item['meta']['detailUrl']
                    })
                
                logger.info(f"Found {len(items)} URLs (total: {len(detail_urls)})")
                
                total_count = data.get('meta', {}).get('totalCount', 0)
                if len(detail_urls) >= total_count:
                    break
                
                offset += limit
                time.sleep(self.rate_limit)
                
            except Exception as e:
                logger.error(f"Error getting URLs at offset {offset}: {e}")
                break
        
        logger.info(f"Total startup URLs found: {len(detail_urls)}")
        return detail_urls
    
    def get_startup_details(self, detail_url):
        """Get detailed startup information"""
        try:
            response = self.session.get(detail_url)
            response.raise_for_status()
            data = response.json()
            
            # Remove image and HTML fields
            cleaned_data = self.clean_data(data)
            time.sleep(self.rate_limit)
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error getting details from {detail_url}: {e}")
            return None
    
    def clean_data(self, data):
        """Remove image, HTML and unnecessary fields"""
        # Fields to exclude (images, HTML, meta info)
        exclude_fields = {
            'previewImage', 'coverImage', 'logo', 'meta', 'options',
            'htmlUrl', 'pagePath', 'detailUrl'
        }
        
        cleaned = {}
        for key, value in data.items():
            if key in exclude_fields:
                continue
            
            if isinstance(value, dict):
                # Recursively clean nested dictionaries
                if any(img_key in value for img_key in ['url', 'renditions', 'alt']):
                    continue  # Skip image objects
                cleaned[key] = self.clean_data(value)
            elif isinstance(value, list):
                # Clean lists
                cleaned_list = []
                for item in value:
                    if isinstance(item, dict):
                        cleaned_item = self.clean_data(item)
                        if cleaned_item:  # Only add non-empty items
                            cleaned_list.append(cleaned_item)
                    else:
                        cleaned_list.append(item)
                cleaned[key] = cleaned_list
            else:
                cleaned[key] = value
        
        return cleaned
    
    def scrape_all_details(self):
        """Scrape details for all startups"""
        # Get all URLs first
        startup_urls = self.get_all_startup_urls()
        
        if not startup_urls:
            logger.error("No startup URLs found")
            return []
        
        all_details = []
        logger.info(f"Starting to scrape details for {len(startup_urls)} startups...")
        
        for i, startup_info in enumerate(startup_urls):
            logger.info(f"Scraping {i+1}/{len(startup_urls)}: {startup_info['title']}")
            
            details = self.get_startup_details(startup_info['detail_url'])
            if details:
                all_details.append(details)
            else:
                logger.warning(f"Failed to get details for {startup_info['title']}")
        
        logger.info(f"Successfully scraped {len(all_details)} startup details")
        return all_details
    
    def save_to_json(self, data, filename):
        """Save data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Saved {len(data)} records to {filename}")

def main():
    logger.info("Starting startup details scraper...")
    
    scraper = StartupDetailsScraper(rate_limit=1.0)
    
    try:
        # Scrape all startup details
        all_details = scraper.scrape_all_details()
        
        # Save to JSON
        scraper.save_to_json(all_details, 'startup_details.json')
        
        logger.info("Scraping completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise

if __name__ == "__main__":
    main()