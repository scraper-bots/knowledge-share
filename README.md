# Startup Details Scraper for knowledge-share.eu

Simple Python script that scrapes detailed information for all startups from knowledge-share.eu without images or HTML content.

## Features

- **Complete scraping**: Gets detailed info for all startups automatically
- **Clean data**: Removes images, HTML, and unnecessary metadata
- **Rate limiting**: 1-second delay between requests
- **Error handling**: Continues scraping even if individual requests fail
- **JSON output**: Clean, structured data export

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python scraper.py
```

The script will:
1. Get all startup URLs from the listings API
2. Scrape detailed information for each startup
3. Clean the data (remove images/HTML)
4. Save to `startup_details.json`

## Output

- `startup_details.json`: Complete detailed data for all startups

## Rate Limiting

1-second delay between requests to be respectful to the server.