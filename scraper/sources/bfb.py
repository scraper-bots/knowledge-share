import logging
import pandas as pd
from bs4 import BeautifulSoup
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class BfbScraper(BaseScraper):
    """
    Baku Stock Exchange (BFB) job scraper
    """
    
    @scraper_error_handler
    async def scrape_bfb(self, session):
        # Try multiple possible career URLs
        urls = [
            "https://www.bfb.az/en/careers", 
            "https://www.bfb.az/careers",
            "https://www.bfb.az/en/about/careers",
            "https://www.bfb.az/about/careers"
        ]
        
        for url in urls:
            response = await self.fetch_url_async(url, session)
            if response and '404' not in response:
                soup = BeautifulSoup(response, "html.parser")

                titles = []
                
                # Try original selector
                job_listings = soup.select("ul.page-list > li")
                
                for listing in job_listings:
                    title_tag = listing.find("h3", class_="accordion-title")
                    title = title_tag.get_text(strip=True) if title_tag else "N/A"
                    if title != "N/A":
                        titles.append(title)
                
                # If no jobs found with original selector, try alternatives
                if not titles:
                    # Look for job/career related content
                    for text_elem in soup.find_all(string=lambda text: text and ('position' in text.lower() or 'vacancy' in text.lower() or 'opening' in text.lower())):
                        parent = text_elem.parent
                        if parent and parent.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div']:
                            clean_text = text_elem.strip()
                            if len(clean_text) > 5 and len(clean_text) < 200:  # Reasonable job title length
                                titles.append(clean_text)
                
                if titles:
                    return pd.DataFrame({
                        'company': 'BFB',
                        "vacancy": titles,
                        "apply_link": url,
                    })

        # No jobs found on any URL
        logger.warning("No job listings found on BFB career pages")
        return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])