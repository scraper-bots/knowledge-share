-- UPDATED MONITORING QUERY FOR MODULAR SCRAPER
-- Synchronized with base_scraper.py source patterns

WITH latest_scrape AS (
  SELECT MAX(created_at) as latest_date
  FROM scraper.jobs_jobpost
),
website_patterns AS (
  SELECT *
  FROM (VALUES
    ('1is.az', '%1is.az%'),
    ('ABB', '%abb-bank%'),
    ('ADA', '%ada.edu%'),
    ('Airswift', '%airswift%'),
    ('ARTI', '%arti.edu%'),
    ('ASCO', '%asco%'),
    ('Azercell', '%azercell%'),
    ('Azerconnect', '%oraclecloud%'),
    ('Azercosmos', '%azercosmos%'),
    ('AzerGold', '%azergold%'),
    ('Baku Electronics', '%bakuelectronics.az%'),
    ('Bank of Baku', '%bankofbaku%'),
    ('Banker.az', '%banker%'),
    ('BFB', '%bfb.az%'),
    ('Boss.az', '%boss.az%'),
    ('Bravo', '%bravosupermarket%'),
    ('Busy', '%busy%'),
    ('CanScreen', '%canscreen%'),
    ('CBAR', '%cbar%'),
    ('DEJobs', '%dejobs%'),
    ('Djinni', '%djinni%'),
    ('eJob', '%ejob%'),
    ('eKaryera', '%ekaryera%'),
    ('Fintech Farm', '%fintech-farm%'),
    ('Glorri', '%glorri%'),
    ('Guavalab', '%guavalab%'),
    ('HCB', '%hcb.az%'),
    ('HelloJob', '%hellojob%'),
    ('HRC Baku', '%hrcbaku%'),
    ('HRIN', '%hrin.az%'),
    ('Is-elanlari', '%is-elanlari%'),
    ('Ishelanlari', '%ishelanlari%'),
    ('Isqur', '%isqur%'),
    ('Isveren', '%isveren%'),
    ('ITS Gov', '%its.gov%'),
    ('Jobbox', '%jobbox%'),
    ('JobFinder', '%jobfinder%'),
    ('JobSearch', '%jobsearch%'),
    ('Kapital Bank', '%kapitalbank%'),
    ('Konsis', '%konsis%'),
    ('MDM', '%mdm.gov%'),
    ('Offer.az', '%offer.az%'),
    ('Oil Fund', '%oilfund%'),
    ('Orion', '%orionjobs%'),
    ('Position.az', '%position.az%'),
    ('ProJobs', '%projobs%'),
    ('Regulator', '%regulator%'),
    ('Revolut', '%revolut%'),
    ('Smartjob', '%smartjob%'),
    ('Staffy', '%staffy%'),
    ('TABIB', '%tabib%'),
    ('The Muse', '%themuse%'),
    ('UN Jobs', '%un.org%'),
    ('Vakansiya.az', '%vakansiya.az%'),
    ('Vakansiya.biz', '%vakansiya.biz%'),
    ('Ziraat', '%ziraat%'),
    ('Andersen', '%andersenlab%')
  ) AS t(website_name, url_pattern)
),
jobs_with_row_numbers AS (
  SELECT 
    j.*,
    ROW_NUMBER() OVER (PARTITION BY wp.website_name ORDER BY j.title) as rn
  FROM website_patterns wp
  LEFT JOIN scraper.jobs_jobpost j ON 
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

-- SUMMARY QUERY: Overall scraping performance
SELECT 
    COUNT(*) as "Total Jobs",
    COUNT(DISTINCT source) as "Active Sources", 
    MAX(created_at) as "Latest Scrape",
    MIN(created_at) as "Earliest Job",
    (SELECT COUNT(*) FROM (VALUES 
        ('1is.az'),('ABB'),('ADA'),('Airswift'),('ARTI'),('ASCO'),('Azercell'),
        ('Azerconnect'),('Azercosmos'),('AzerGold'),('Baku Electronics'),
        ('Bank of Baku'),('Banker.az'),('BFB'),('Boss.az'),('Bravo'),('Busy'),
        ('CanScreen'),('CBAR'),('DEJobs'),('Djinni'),('eJob'),('eKaryera'),
        ('Fintech Farm'),('Glorri'),('Guavalab'),('HCB'),('HelloJob'),
        ('HRC Baku'),('HRIN'),('Is-elanlari'),('Ishelanlari'),('Isqur'),
        ('Isveren'),('ITS Gov'),('Jobbox'),('JobFinder'),('JobSearch'),
        ('Kapital Bank'),('Konsis'),('MDM'),('Offer.az'),('Oil Fund'),
        ('Orion'),('Position.az'),('ProJobs'),('Regulator'),('Revolut'),
        ('Smartjob'),('Staffy'),('TABIB'),('The Muse'),('UN Jobs'),
        ('Vakansiya.az'),('Vakansiya.biz'),('Ziraat'),('Andersen')
    ) AS expected_sources(name)) as "Expected Sources",
    ROUND(
        (COUNT(DISTINCT source)::decimal / 57) * 100, 1
    ) as "Source Coverage %"
FROM scraper.jobs_jobpost 
WHERE created_at = (SELECT MAX(created_at) FROM scraper.jobs_jobpost);

-- TOP PERFORMING SOURCES
SELECT 
    source as "Source",
    COUNT(*) as "Jobs",
    ROUND((COUNT(*)::decimal / (SELECT COUNT(*) FROM scraper.jobs_jobpost WHERE created_at = (SELECT MAX(created_at) FROM scraper.jobs_jobpost))) * 100, 1) as "Share %"
FROM scraper.jobs_jobpost 
WHERE created_at = (SELECT MAX(created_at) FROM scraper.jobs_jobpost)
GROUP BY source
ORDER BY COUNT(*) desc;