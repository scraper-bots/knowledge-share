--select
--	id,
--	title,
--	company,
--	apply_link,
--	created_at
--from
--	public.jobs_jobpost
--where
--	apply_link like '%smartjob%'
--	and created_at = (
--	select
--		max(created_at)
--	from
--		public.jobs_jobpost jj)
--order by
--	created_at desc;





--WITH latest_scrape AS (
--  SELECT MAX(created_at) as latest_date
--  FROM public.jobs_jobpost
--),
--website_patterns AS (
--  SELECT *
--  FROM (VALUES
--    ('Smartjob', '%smartjob%'),
--    ('Glorri', '%glorri%'),
--    ('Azercell', '%azercell%'),
--    ('Azerconnect', '%azerconnect%'),
--    ('Djinni', '%djinni%'),
--    ('ABB', '%abb-bank%'),
--    ('HelloJob', '%hellojob%'),
--    ('Boss.az', '%boss.az%'),
--    ('eJob', '%ejob%'),
--    ('Vakansiya.az', '%vakansiya.az%'),
--    ('Ishelanlari', '%ishelanlari%'),
--    ('Banker.az', '%banker%'),
--    ('Offer.az', '%offer.az%'),
--    ('Isveren', '%isveren%'),
--    ('Isqur', '%isqur%'),
--    ('Kapital Bank', '%kapitalbank%'),
--    ('Bank of Baku', '%bankofbaku%'),
--    ('Jobbox', '%jobbox%'),
--    ('Vakansiya.biz', '%vakansiya.biz%'),
--    ('ITS Gov', '%its.gov%'),
--    ('TABIB', '%tabib%'),
--    ('ProJobs', '%projobs%'),
--    ('AzerGold', '%azergold%'),
--    ('Konsis', '%konsis%'),
--    ('Baku Electronics', '%bakuelectronics%'),
--    ('ASCO', '%asco%'),
--    ('CBAR', '%cbar%'),
--    ('ADA', '%ada.edu%'),
--    ('JobFinder', '%jobfinder%'),
--    ('Regulator', '%regulator%'),
--    ('eKaryera', '%ekaryera%'),
--    ('Bravo', '%bravosupermarket%'),
--    ('MDM', '%mdm.gov%'),
--    ('ARTI', '%arti.edu%'),
--    ('Staffy', '%staffy%'),
--    ('Position.az', '%position.az%'),
--    ('HRIN', '%hrin.co%'),
--    ('UN Jobs', '%un.org%'),
--    ('Oil Fund', '%oilfund%'),
--    ('1is.az', '%1is.az%'),
--    ('The Muse', '%themuse%'),
--    ('DEJobs', '%dejobs%'),
--    ('HCB', '%hcb.az%'),
--    ('BFB', '%bfb.az%'),
--    ('Airswift', '%airswift%'),
--    ('Orion', '%orionjobs%'),
--    ('HRC Baku', '%hrcbaku%'),
--    ('JobSearch', '%jobsearch%'),
--    ('CanScreen', '%canscreen%')
--  ) AS t(website_name, url_pattern)
--),
--scraping_status AS (
--  SELECT 
--    wp.website_name,
--    wp.url_pattern,
--    COUNT(j.id) as job_count,
--    MIN(j.created_at) as oldest_job,
--    MAX(j.created_at) as newest_job,
--    CASE 
--      WHEN COUNT(j.id) > 0 AND MAX(j.created_at) = (SELECT latest_date FROM latest_scrape)
--        THEN 'Active'
--      WHEN COUNT(j.id) > 0 
--        THEN 'Inactive (Last scrape: ' || TO_CHAR(MAX(j.created_at), 'YYYY-MM-DD HH24:MI') || ')'
--      ELSE 'No Jobs Found'
--    END as status
--  FROM website_patterns wp
--  LEFT JOIN public.jobs_jobpost j 
--    ON j.apply_link LIKE wp.url_pattern
--  GROUP BY wp.website_name, wp.url_pattern
--)
--SELECT 
--  website_name as "Website",
--  job_count as "Total Jobs",
--  TO_CHAR(newest_job, 'YYYY-MM-DD HH24:MI') as "Latest Job",
--  TO_CHAR(oldest_job, 'YYYY-MM-DD HH24:MI') as "Oldest Job",
--  status as "Status",
--  url_pattern as "URL Pattern"
--FROM scraping_status
--ORDER BY 
--  CASE 
--    WHEN status = 'Active' THEN 1
--    WHEN status LIKE 'Inactive%' THEN 2
--    ELSE 3
--  END,
--  job_count DESC,
--  website_name;




WITH latest_scrape AS (
  SELECT MAX(created_at) as latest_date
  FROM public.jobs_jobpost
),
website_patterns AS (
  SELECT *
  FROM (VALUES
    ('Smartjob', '%smartjob%'),
    ('Glorri', '%glorri%'),
    ('Azercell', '%azercell%'),
    ('Azerconnect', '%azerconnect%'),
    ('Djinni', '%djinni%'),
    ('ABB', '%abb-bank%'),
    ('HelloJob', '%hellojob%'),
    ('Boss.az', '%boss.az%'),
    ('eJob', '%ejob%'),
    ('Vakansiya.az', '%vakansiya.az%'),
    ('Ishelanlari', '%ishelanlari%'),
    ('Banker.az', '%banker%'),
    ('Offer.az', '%offer.az%'),
    ('Isveren', '%isveren%'),
    ('Isqur', '%isqur%'),
    ('Kapital Bank', '%kapitalbank%'),
    ('Bank of Baku', '%bankofbaku%'),
    ('Jobbox', '%jobbox%'),
    ('Vakansiya.biz', '%vakansiya.biz%'),
    ('ITS Gov', '%its.gov%'),
    ('TABIB', '%tabib%'),
    ('ProJobs', '%projobs%'),
    ('AzerGold', '%azergold%'),
    ('Konsis', '%konsis%'),
    ('Baku Electronics', '%bakuelectronics%'),
    ('ASCO', '%asco%'),
    ('CBAR', '%cbar%'),
    ('ADA', '%ada.edu%'),
    ('JobFinder', '%jobfinder%'),
    ('Regulator', '%regulator%'),
    ('eKaryera', '%ekaryera%'),
    ('Bravo', '%bravosupermarket%'),
    ('MDM', '%mdm.gov%'),
    ('ARTI', '%arti.edu%'),
    ('Staffy', '%staffy%'),
    ('Position.az', '%position.az%'),
    ('HRIN', '%hrin.co%'),
    ('UN Jobs', '%un.org%'),
    ('Oil Fund', '%oilfund%'),
    ('1is.az', '%1is.az%'),
    ('The Muse', '%themuse%'),
    ('DEJobs', '%dejobs%'),
    ('HCB', '%hcb.az%'),
    ('BFB', '%bfb.az%'),
    ('Airswift', '%airswift%'),
    ('Orion', '%orionjobs%'),
    ('HRC Baku', '%hrcbaku%'),
    ('JobSearch', '%jobsearch%'),
    ('CanScreen', '%canscreen%')
  ) AS t(website_name, url_pattern)
),
jobs_with_row_numbers AS (
  SELECT 
    j.*,
    ROW_NUMBER() OVER (PARTITION BY wp.website_name ORDER BY j.title) as rn
  FROM website_patterns wp
  LEFT JOIN public.jobs_jobpost j ON 
    j.apply_link LIKE wp.url_pattern
    AND j.created_at = (SELECT latest_date FROM latest_scrape)
)
SELECT 
    wp.website_name as "Website",
    COUNT(j.id) as "Job Count",
    CASE 
        WHEN COUNT(j.id) > 0 THEN 'Active'
        ELSE 'Inactive'
    END as "Status",
    MAX(j.created_at) as "Latest Job Date",
    wp.url_pattern as "Pattern",
    STRING_AGG(
        CASE 
            WHEN j.rn <= 3 THEN j.title 
            ELSE NULL 
        END,
        ' | ' 
        ORDER BY j.title
    ) as "Sample Titles"
FROM website_patterns wp
LEFT JOIN jobs_with_row_numbers j ON 
    j.apply_link LIKE wp.url_pattern
GROUP BY 
    wp.website_name,
    wp.url_pattern
ORDER BY 
    "Status" ASC,
    "Job Count" DESC,
    "Website";