# Async Startup Details Scraper for knowledge-share.eu

High-performance async Python scraper that gets detailed information for all startups from knowledge-share.eu without images or HTML content.

## Features

- **🚀 Async/Concurrent**: Uses aiohttp and asyncio for high performance
- **🔄 Retry Mechanisms**: Automatic retries with exponential backoff
- **⚡ Batch Processing**: Processes startups in batches for efficiency  
- **🧹 Clean Data**: Removes images, HTML, and unnecessary metadata
- **🛡️ Rate Limiting**: Built-in semaphore and delay controls
- **📊 Progress Tracking**: Real-time batch progress updates
- **🎯 Error Resilience**: Continues scraping even if individual requests fail

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python scraper.py
```

The scraper will:
1. Get all startup URLs from the listings API (async)
2. Scrape detailed information in concurrent batches
3. Apply retry mechanisms for failed requests
4. Clean the data (remove images/HTML)
5. Save to `startup_details.json`

## Performance

- **Concurrent requests**: Up to 10 simultaneous connections
- **Batch processing**: 50 startups per batch
- **Retry logic**: Up to 3 attempts with exponential backoff
- **Rate limiting**: 0.3s delay between requests

## Output

- `startup_details.json`: Complete detailed data for all startups

## Configuration

Adjust performance in the scraper initialization:

```python
scraper = StartupDetailsScraper(
    max_concurrent=10,    # Max simultaneous requests
    request_delay=0.3     # Delay between requests (seconds)
)
```