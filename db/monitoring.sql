WITH latest_scrape AS (
  SELECT MAX(created_at) as latest_date
  FROM scraper.jobs_jobpost  -- UPDATE THIS LINE
),
website_patterns AS (
  SELECT *
  FROM (VALUES
    ('Smartjob', '%smartjob%'),
    ('Glorri', '%glorri%'),
    ('Azercell', '%azercell%'),
    ('Azerconnect', '%azerconnect.az%'),
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
    ('Baku Electronics', '%bakuelectronics.az%'),
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
    ('CanScreen', '%canscreen%'),
    ('Azercosmos', '%azercosmos%'),
    ('Guavalab', '%guavalab%'),
    ('Fintech Farm', '%fintech-farm%')
  ) AS t(website_name, url_pattern)
),
jobs_with_row_numbers AS (
  SELECT 
    j.*,
    ROW_NUMBER() OVER (PARTITION BY wp.website_name ORDER BY j.title) as rn
  FROM website_patterns wp
  LEFT JOIN scraper.jobs_jobpost j ON  -- UPDATE THIS LINE
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