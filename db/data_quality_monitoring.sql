-- COMPREHENSIVE DATA QUALITY MONITORING SCRIPT
-- Monitors null values, data integrity, and overall data quality

-- =============================================================================
-- 1. DATA QUALITY OVERVIEW DASHBOARD
-- =============================================================================

SELECT 
    'DATA QUALITY DASHBOARD' as "Report Section",
    COUNT(*) as "Total Records",
    MAX(created_at) as "Latest Scrape",
    COUNT(DISTINCT source) as "Active Sources",
    COUNT(DISTINCT DATE(created_at)) as "Scraping Days",
    ROUND(
        (COUNT(DISTINCT source)::decimal / 56) * 100, 1
    ) as "Source Coverage %"
FROM scraper.jobs_jobpost;

-- =============================================================================
-- 2. NULL VALUES ANALYSIS
-- =============================================================================

WITH null_analysis AS (
    SELECT 
        COUNT(*) as total_records,
        -- Title/Job Vacancy Analysis
        COUNT(CASE WHEN title IS NULL OR title = '' THEN 1 END) as title_null_count,
        COUNT(CASE WHEN title = 'n/a' OR title = 'N/A' OR title = 'null' THEN 1 END) as title_na_count,
        
        -- Company Analysis  
        COUNT(CASE WHEN company IS NULL OR company = '' THEN 1 END) as company_null_count,
        COUNT(CASE WHEN company = 'n/a' OR company = 'N/A' OR company = 'null' THEN 1 END) as company_na_count,
        
        -- Apply Link Analysis
        COUNT(CASE WHEN apply_link IS NULL OR apply_link = '' THEN 1 END) as link_null_count,
        COUNT(CASE WHEN apply_link = 'n/a' OR apply_link = 'N/A' THEN 1 END) as link_na_count,
        
        -- Source Analysis
        COUNT(CASE WHEN source IS NULL OR source = '' THEN 1 END) as source_null_count,
        COUNT(CASE WHEN source = 'Unknown' OR source = 'Other' THEN 1 END) as source_unknown_count
    FROM scraper.jobs_jobpost
    WHERE created_at = (SELECT MAX(created_at) FROM scraper.jobs_jobpost)
)
SELECT 
    'NULL VALUES ANALYSIS' as "Report Section",
    total_records as "Total Records",
    
    -- Title Quality
    title_null_count as "Title: NULL/Empty",
    title_na_count as "Title: N/A Values", 
    ROUND((title_null_count + title_na_count)::decimal / total_records * 100, 2) as "Title: Bad Data %",
    
    -- Company Quality
    company_null_count as "Company: NULL/Empty",
    company_na_count as "Company: N/A Values",
    ROUND((company_null_count + company_na_count)::decimal / total_records * 100, 2) as "Company: Bad Data %",
    
    -- Link Quality  
    link_null_count as "Link: NULL/Empty",
    link_na_count as "Link: N/A Values",
    ROUND((link_null_count + link_na_count)::decimal / total_records * 100, 2) as "Link: Bad Data %",
    
    -- Source Quality
    source_null_count as "Source: NULL/Empty", 
    source_unknown_count as "Source: Unknown/Other",
    ROUND((source_null_count + source_unknown_count)::decimal / total_records * 100, 2) as "Source: Poor Detection %"
    
FROM null_analysis;

-- =============================================================================
-- 3. DATA INTEGRITY CHECKS
-- =============================================================================

-- Duplicate Detection
WITH duplicate_analysis AS (
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT (title, company, apply_link)) as unique_combinations,
        COUNT(*) - COUNT(DISTINCT (title, company, apply_link)) as duplicate_count
    FROM scraper.jobs_jobpost 
    WHERE created_at = (SELECT MAX(created_at) FROM scraper.jobs_jobpost)
),
-- URL Validation
url_validation AS (
    SELECT 
        COUNT(*) as total_records,
        COUNT(CASE WHEN apply_link LIKE 'http%' THEN 1 END) as valid_urls,
        COUNT(CASE WHEN LENGTH(apply_link) < 10 THEN 1 END) as suspiciously_short_urls,
        COUNT(CASE WHEN apply_link LIKE '%.%' THEN 1 END) as urls_with_domain
    FROM scraper.jobs_jobpost 
    WHERE created_at = (SELECT MAX(created_at) FROM scraper.jobs_jobpost)
        AND apply_link IS NOT NULL 
        AND apply_link != ''
        AND apply_link != 'n/a'
),
-- Text Quality Analysis
text_quality AS (
    SELECT 
        COUNT(*) as total_records,
        COUNT(CASE WHEN LENGTH(title) > 5 THEN 1 END) as meaningful_titles,
        COUNT(CASE WHEN LENGTH(company) > 2 THEN 1 END) as meaningful_companies,
        COUNT(CASE WHEN title LIKE '%developer%' OR title LIKE '%engineer%' OR title LIKE '%manager%' OR title LIKE '%analyst%' THEN 1 END) as job_related_titles
    FROM scraper.jobs_jobpost 
    WHERE created_at = (SELECT MAX(created_at) FROM scraper.jobs_jobpost)
        AND title IS NOT NULL 
        AND title != '' 
        AND title != 'n/a'
)
SELECT 
    'DATA INTEGRITY ANALYSIS' as "Report Section",
    
    -- Duplicate Analysis
    d.total_records as "Total Records",
    d.unique_combinations as "Unique Job Combinations", 
    d.duplicate_count as "Duplicate Records",
    ROUND(d.duplicate_count::decimal / d.total_records * 100, 2) as "Duplication Rate %",
    
    -- URL Quality
    ROUND(u.valid_urls::decimal / u.total_records * 100, 2) as "Valid URLs %",
    ROUND(u.urls_with_domain::decimal / u.total_records * 100, 2) as "URLs with Domain %",
    u.suspiciously_short_urls as "Suspicious URLs",
    
    -- Text Quality
    ROUND(t.meaningful_titles::decimal / t.total_records * 100, 2) as "Meaningful Titles %",
    ROUND(t.meaningful_companies::decimal / t.total_records * 100, 2) as "Meaningful Companies %",
    ROUND(t.job_related_titles::decimal / t.total_records * 100, 2) as "Job-Related Titles %"
    
FROM duplicate_analysis d, url_validation u, text_quality t;

-- =============================================================================
-- 4. SOURCE-WISE DATA QUALITY 
-- =============================================================================

SELECT 
    'SOURCE QUALITY BREAKDOWN' as "Report Section",
    source as "Source",
    COUNT(*) as "Job Count",
    
    -- Null/Empty Analysis
    COUNT(CASE WHEN title IS NULL OR title = '' OR title = 'n/a' THEN 1 END) as "Bad Titles",
    COUNT(CASE WHEN company IS NULL OR company = '' OR company = 'n/a' THEN 1 END) as "Bad Companies", 
    COUNT(CASE WHEN apply_link IS NULL OR apply_link = '' OR apply_link = 'n/a' THEN 1 END) as "Bad Links",
    
    -- Quality Percentages
    ROUND(
        (COUNT(*) - COUNT(CASE WHEN title IS NULL OR title = '' OR title = 'n/a' THEN 1 END))::decimal 
        / COUNT(*) * 100, 1
    ) as "Title Quality %",
    
    ROUND(
        (COUNT(*) - COUNT(CASE WHEN company IS NULL OR company = '' OR company = 'n/a' THEN 1 END))::decimal 
        / COUNT(*) * 100, 1  
    ) as "Company Quality %",
    
    ROUND(
        (COUNT(*) - COUNT(CASE WHEN apply_link IS NULL OR apply_link = '' OR apply_link = 'n/a' THEN 1 END))::decimal 
        / COUNT(*) * 100, 1
    ) as "Link Quality %",
    
    -- Overall Quality Score
    ROUND(
        ((COUNT(*) - COUNT(CASE WHEN title IS NULL OR title = '' OR title = 'n/a' THEN 1 END)) +
         (COUNT(*) - COUNT(CASE WHEN company IS NULL OR company = '' OR company = 'n/a' THEN 1 END)) +
         (COUNT(*) - COUNT(CASE WHEN apply_link IS NULL OR apply_link = '' OR apply_link = 'n/a' THEN 1 END)))::decimal 
        / (COUNT(*) * 3) * 100, 1
    ) as "Overall Quality Score %"
    
FROM scraper.jobs_jobpost 
WHERE created_at = (SELECT MAX(created_at) FROM scraper.jobs_jobpost)
GROUP BY source
ORDER BY "Overall Quality Score %" DESC, "Job Count" DESC;

-- =============================================================================
-- 5. FIELD LENGTH ANALYSIS
-- =============================================================================

WITH field_lengths AS (
    SELECT 
        source,
        LENGTH(title) as title_length,
        LENGTH(company) as company_length, 
        LENGTH(apply_link) as link_length
    FROM scraper.jobs_jobpost 
    WHERE created_at = (SELECT MAX(created_at) FROM scraper.jobs_jobpost)
        AND title IS NOT NULL 
        AND company IS NOT NULL 
        AND apply_link IS NOT NULL
)
SELECT 
    'FIELD LENGTH ANALYSIS' as "Report Section",
    
    -- Title Length Stats
    ROUND(AVG(title_length), 1) as "Avg Title Length",
    MIN(title_length) as "Min Title Length",
    MAX(title_length) as "Max Title Length",
    COUNT(CASE WHEN title_length > 500 THEN 1 END) as "Titles > 500 chars",
    
    -- Company Length Stats  
    ROUND(AVG(company_length), 1) as "Avg Company Length",
    MIN(company_length) as "Min Company Length", 
    MAX(company_length) as "Max Company Length",
    COUNT(CASE WHEN company_length > 500 THEN 1 END) as "Companies > 500 chars",
    
    -- Link Length Stats
    ROUND(AVG(link_length), 1) as "Avg Link Length",
    MIN(link_length) as "Min Link Length",
    MAX(link_length) as "Max Link Length", 
    COUNT(CASE WHEN link_length > 1000 THEN 1 END) as "Links > 1000 chars"
    
FROM field_lengths;

-- =============================================================================
-- 6. RECENT TRENDS ANALYSIS (Last 7 Days)
-- =============================================================================

SELECT 
    'RECENT TRENDS (7 DAYS)' as "Report Section",
    DATE(created_at) as "Date",
    COUNT(*) as "Jobs Scraped",
    COUNT(DISTINCT source) as "Active Sources",
    
    -- Quality Metrics
    ROUND(
        (COUNT(*) - COUNT(CASE WHEN title IS NULL OR title = '' OR title = 'n/a' THEN 1 END))::decimal 
        / COUNT(*) * 100, 1
    ) as "Title Quality %",
    
    ROUND(
        (COUNT(*) - COUNT(CASE WHEN company IS NULL OR company = '' OR company = 'n/a' THEN 1 END))::decimal 
        / COUNT(*) * 100, 1
    ) as "Company Quality %",
    
    COUNT(*) - COUNT(DISTINCT (title, company, apply_link)) as "Duplicates",
    
    -- Source Detection
    ROUND(
        COUNT(CASE WHEN source NOT IN ('Unknown', 'Other') THEN 1 END)::decimal 
        / COUNT(*) * 100, 1
    ) as "Source Detection %"
    
FROM scraper.jobs_jobpost 
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY DATE(created_at) DESC;

-- =============================================================================
-- 7. PROBLEM RECORDS SAMPLE
-- =============================================================================

SELECT 
    'PROBLEM RECORDS SAMPLE' as "Report Section",
    id,
    CASE 
        WHEN title IS NULL OR title = '' THEN 'NULL/Empty Title'
        WHEN title = 'n/a' THEN 'N/A Title'
        WHEN company IS NULL OR company = '' THEN 'NULL/Empty Company'  
        WHEN company = 'n/a' THEN 'N/A Company'
        WHEN apply_link IS NULL OR apply_link = '' THEN 'NULL/Empty Link'
        WHEN apply_link = 'n/a' THEN 'N/A Link'
        WHEN source IN ('Unknown', 'Other') THEN 'Poor Source Detection'
        ELSE 'Other Issue'
    END as "Issue Type",
    LEFT(title, 50) as "Title Sample",
    LEFT(company, 30) as "Company Sample", 
    LEFT(apply_link, 60) as "Link Sample",
    source
FROM scraper.jobs_jobpost 
WHERE created_at = (SELECT MAX(created_at) FROM scraper.jobs_jobpost)
    AND (
        title IS NULL OR title = '' OR title = 'n/a' OR
        company IS NULL OR company = '' OR company = 'n/a' OR  
        apply_link IS NULL OR apply_link = '' OR apply_link = 'n/a' OR
        source IN ('Unknown', 'Other')
    )
ORDER BY 
    CASE 
        WHEN title IS NULL OR title = '' OR title = 'n/a' THEN 1
        WHEN company IS NULL OR company = '' OR company = 'n/a' THEN 2
        WHEN apply_link IS NULL OR apply_link = '' OR apply_link = 'n/a' THEN 3
        ELSE 4
    END
LIMIT 20;

-- =============================================================================
-- 8. DATA QUALITY SCORE SUMMARY  
-- =============================================================================

WITH quality_metrics AS (
    SELECT 
        COUNT(*) as total_records,
        -- Calculate individual quality scores
        ROUND(
            (COUNT(*) - COUNT(CASE WHEN title IS NULL OR title = '' OR title = 'n/a' THEN 1 END))::decimal 
            / COUNT(*) * 100, 2
        ) as title_quality,
        ROUND(
            (COUNT(*) - COUNT(CASE WHEN company IS NULL OR company = '' OR company = 'n/a' THEN 1 END))::decimal 
            / COUNT(*) * 100, 2
        ) as company_quality,
        ROUND(
            (COUNT(*) - COUNT(CASE WHEN apply_link IS NULL OR apply_link = '' OR apply_link = 'n/a' THEN 1 END))::decimal 
            / COUNT(*) * 100, 2
        ) as link_quality,
        ROUND(
            COUNT(CASE WHEN source NOT IN ('Unknown', 'Other') THEN 1 END)::decimal 
            / COUNT(*) * 100, 2
        ) as source_quality,
        ROUND(
            COUNT(DISTINCT (title, company, apply_link))::decimal / COUNT(*) * 100, 2
        ) as uniqueness_score
    FROM scraper.jobs_jobpost 
    WHERE created_at = (SELECT MAX(created_at) FROM scraper.jobs_jobpost)
)
SELECT 
    'OVERALL DATA QUALITY SCORE' as "Report Section",
    total_records as "Total Records Analyzed",
    title_quality as "Title Quality Score",
    company_quality as "Company Quality Score", 
    link_quality as "Link Quality Score",
    source_quality as "Source Detection Score",
    uniqueness_score as "Data Uniqueness Score",
    ROUND(
        (title_quality + company_quality + link_quality + source_quality + uniqueness_score) / 5, 1
    ) as "OVERALL QUALITY SCORE",
    CASE 
        WHEN (title_quality + company_quality + link_quality + source_quality + uniqueness_score) / 5 >= 90 THEN 'EXCELLENT'
        WHEN (title_quality + company_quality + link_quality + source_quality + uniqueness_score) / 5 >= 80 THEN 'GOOD' 
        WHEN (title_quality + company_quality + link_quality + source_quality + uniqueness_score) / 5 >= 70 THEN 'FAIR'
        ELSE 'NEEDS IMPROVEMENT'
    END as "Quality Rating"
FROM quality_metrics;