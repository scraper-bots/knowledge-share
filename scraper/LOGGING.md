# Enhanced Scraper Logging System

This document describes the comprehensive logging system implemented for the job scraper, designed to provide detailed feedback in both local development and GitHub Actions environments.

## Features

### 🎯 Environment Detection
- Automatically detects GitHub Actions environment
- Adapts logging verbosity and format accordingly
- Uses GitHub Actions annotations for better visibility

### 📊 Comprehensive Status Tracking
Each scraper execution is tracked with:
- **Status types**: `success`, `no_jobs`, `timeout`, `network_error`, `exception`, `not_found`, `no_methods`
- **Timing information**: Individual scraper duration
- **Job counts**: Number of jobs successfully scraped
- **Error details**: Specific error messages and types

### 🔍 Detailed Error Classification

#### Network Errors
- HTTP client errors (403, 503, DNS issues)
- Timeout errors with duration tracking
- Connection failures

#### Scraper Implementation Issues
- Missing scraper methods
- Invalid return types
- Import/module loading errors

#### Runtime Exceptions
- Full stack trace in GitHub Actions
- Categorized by exception type
- Duration before failure

### 📈 Summary Reports

#### Success Summary
- Jobs collected per scraper
- Execution time per scraper
- Sorted by job count (most successful first)

#### Failure Analysis
- Grouped by failure type
- Duration before failure
- Specific error messages
- Clear categorization for debugging

### 🌐 GitHub Actions Integration

#### Annotations
- `::notice::` for successful scrapers
- `::warning::` for scrapers with no jobs
- `::error::` for failed scrapers
- `::group::` for organized log sections

#### Visibility Features
- Collapsible sections for better organization
- Progress indicators during execution
- Final summary with key metrics
- Individual scraper status in real-time

## Usage

### Local Development
```bash
python scraper.py
```
- Standard error-level logging
- Simple format for quick debugging
- Focus on critical issues only

### GitHub Actions
```bash
# Environment automatically detected
python scraper.py
```
- Verbose info-level logging
- GitHub Actions annotations
- Detailed timing and status information
- Organized output with collapsible sections

## Example Output

### GitHub Actions Format
```
::group::📈 Execution Summary - 34/57 successful
✅ Successful scrapers: 34
🟡 Empty results: 15
❌ Failed scrapers: 8
🕰️ Total time: 45.2s

❌ Failed Scrapers Details:

  Network Error:
    • jobbox_az (2.1s): HTTP/Network error: Cannot connect to host
    • ekaryera (1.8s): HTTP/Network error: 503 Service Unavailable

  Timeout:
    • complex_scraper (30.0s): Timeout after 30.0s: Task timeout

  Exception:
    • broken_scraper (0.3s): AttributeError: 'NoneType' object has no attribute 'find'

✅ Successful Scrapers:
  • glorri: 777 jobs (3.2s)
  • vakansiya_biz: 546 jobs (2.8s)
  • djinni: 465 jobs (4.1s)
::endgroup::
```

## Configuration

### Concurrency Adjustment
- Local: up to 10 concurrent scrapers
- GitHub Actions: limited to 3 for stability
- Automatic random delays between starts in CI

### Timeout Settings
- Local: 180 seconds per scraper
- GitHub Actions: 300 seconds per scraper
- Individual scraper method timeout tracking

### Connection Limits
- Local: 50 total connections, 10 per host
- GitHub Actions: 20 total connections, 5 per host
- Enhanced connection cleanup in CI

## Troubleshooting

### Common Failure Types

1. **Network Error**: Website blocking or down
   - Check if the target website is accessible
   - Review rate limiting and headers

2. **Timeout**: Scraper taking too long
   - Optimize scraper logic
   - Check for infinite loops or long waits

3. **No Methods**: Missing scraper implementation
   - Ensure class has `parse_*` or `scrape_*` methods
   - Check class inheritance from BaseScraper

4. **Exception**: Runtime errors in scraper code
   - Review full stack trace in GitHub Actions logs
   - Check for null pointer exceptions or missing data

### Debugging in GitHub Actions
- Full stack traces are available in collapsible sections
- Individual scraper timing helps identify bottlenecks
- Error classification helps prioritize fixes
- Success metrics show overall system health

## Performance Monitoring
- Track job collection rates over time
- Monitor scraper reliability percentages
- Identify consistently failing scrapers
- Optimize based on execution duration data