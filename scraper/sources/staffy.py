import asyncio
import logging
import pandas as pd
import aiohttp
from base_scraper import BaseScraper, scraper_error_handler

logger = logging.getLogger(__name__)


class StaffyScraper(BaseScraper):
    """
    Staffy.az job scraper using GraphQL API
    """
    
    @scraper_error_handler
    async def scrape_staffy(self, session):
        """
        Scrape job listings from Staffy.az using GraphQL API
        """
        async def fetch_jobs(page=1):
            url = "https://api.staffy.az/graphql"
            headers = {
                "Content-Type": "application/json",
                "Accept": "*/*",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Origin": "https://staffy.az",
                "Sec-Fetch-Site": "same-site",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Google Chrome\";v=\"126\"",
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": "\"macOS\""
            }

            query = f"""
            {{
            jobs(page: {page}) {{
                totalCount
                pageInfo {{
                hasNextPage
                hasPreviousPage
                page
                totalPages
                }}
                edges {{
                node {{
                    id
                    slug
                    title
                    createdAt
                    publishedAt
                    expiresAt
                    viewCount
                    salary {{
                    from
                    to
                    }}
                    company {{
                    id
                    name
                    verified
                    }}
                }}
                }}
            }}
            }}
            """

            payload = {"query": query}

            try:
                async with session.post(url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                logger.error(f"Failed to fetch jobs: {e}")
                return None

        async def save_jobs_to_dataframe(jobs_data_list):
            all_jobs = []
            for jobs_data in jobs_data_list:
                if jobs_data and 'data' in jobs_data and 'jobs' in jobs_data['data']:
                    jobs = jobs_data['data']['jobs']['edges']
                    for job in jobs:
                        job_node = job['node']
                        job_info = {
                            "vacancy": job_node['title'],
                            "company": job_node['company']['name'],
                            "verified": job_node['company']['verified'],
                            "salary_from": job_node['salary']['from'] if job_node['salary'] else None,
                            "salary_to": job_node['salary']['to'] if job_node['salary'] else None,
                            "created_at": job_node['createdAt'],
                            "published_at": job_node['publishedAt'],
                            "expires_at": job_node['expiresAt'],
                            "view_count": job_node['viewCount'],
                            "job_id": job_node['id'],
                            "job_slug": job_node['slug'],
                            "apply_link": f"https://staffy.az/job/{job_node['slug']}"
                        }
                        all_jobs.append(job_info)

            df = pd.DataFrame(all_jobs)
            return df

        # Fetch and display job listings with pagination
        page = 1
        max_pages = 8  # Set limit for the number of pages to fetch
        all_jobs_data = []

        while page <= max_pages:
            jobs_data = await fetch_jobs(page)
            if jobs_data:
                all_jobs_data.append(jobs_data)
                if not jobs_data['data']['jobs']['pageInfo']['hasNextPage']:
                    break
                page += 1
            else:
                break

        # Save all fetched job data to a DataFrame
        jobs_df = await save_jobs_to_dataframe(all_jobs_data)

        # Return only the specific columns with renamed columns
        result_df = jobs_df[['company', 'vacancy', 'apply_link']]
        return result_df