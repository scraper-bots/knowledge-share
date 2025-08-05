import os
from typing import Dict, Any

class ScraperConfig:
    """Configuration class for environment-specific scraper settings"""
    
    def __init__(self):
        self.is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        self.is_ci = os.getenv('CI') == 'true' or self.is_github_actions
        
    def get_scraper_settings(self) -> Dict[str, Any]:
        """Get scraper settings based on environment"""
        
        if self.is_github_actions:
            return {
                'max_concurrent': 3,
                'max_retries': 2,
                'timeout': 45,
                'connect_timeout': 15,
                'base_delay': 3,
                'connector_limit': 20,
                'connector_limit_per_host': 5,
                'stagger_start_delay': (0.5, 2),
                'skip_problematic_scrapers': [
                    'isqur',  # Always blocked in CI
                    'themuse',  # Rate limited heavily
                ]
            }
        elif self.is_ci:
            return {
                'max_concurrent': 5,
                'max_retries': 2,
                'timeout': 40,
                'connect_timeout': 12,
                'base_delay': 2,
                'connector_limit': 30,
                'connector_limit_per_host': 8,
                'stagger_start_delay': (0.2, 1),
                'skip_problematic_scrapers': []
            }
        else:
            # Local development settings
            return {
                'max_concurrent': 10,
                'max_retries': 3,
                'timeout': 30,
                'connect_timeout': 10,
                'base_delay': 1,
                'connector_limit': 50,
                'connector_limit_per_host': 10,
                'stagger_start_delay': (0, 0.5),
                'skip_problematic_scrapers': []
            }
    
    def should_skip_scraper(self, scraper_name: str) -> bool:
        """Check if a scraper should be skipped in current environment"""
        settings = self.get_scraper_settings()
        return scraper_name in settings.get('skip_problematic_scrapers', [])
    
    def get_user_agent_pool(self) -> list:
        """Get appropriate user agents for environment"""
        return [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        ]