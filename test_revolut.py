#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

from sources.revolut import RevolutScraper
import aiohttp
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_revolut():
    """Test Revolut scraper locally"""
    logger.info("Testing Revolut scraper...")
    
    scraper = RevolutScraper()
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test build ID extraction
            logger.info("=" * 50)
            logger.info("Testing build ID extraction...")
            
            build_id = await scraper.get_build_id(session)
            logger.info(f"Build ID result: {build_id}")
            
            if build_id:
                logger.info("Build ID extraction successful!")
                
                # Test scraping one team
                logger.info("=" * 50)
                logger.info("Testing team scraping...")
                jobs = await scraper._scrape_team(session, "engineering")
                logger.info(f"Engineering jobs found: {len(jobs)}")
                
                if jobs:
                    logger.info("Sample job:")
                    logger.info(jobs[0])
                
            else:
                logger.error("Build ID extraction failed")
                
        except Exception as e:
            logger.error(f"Test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_revolut())