-- Create the scraper schema
CREATE SCHEMA IF NOT EXISTS scraper;

-- Create jobs table in scraper schema
CREATE TABLE scraper.jobs_jobpost (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500),
    company VARCHAR(500),
    apply_link VARCHAR(1000),
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create errors table in scraper schema
CREATE TABLE scraper.scraper_errors (
    id SERIAL PRIMARY KEY,
    source VARCHAR(255) NOT NULL,
    error TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Migrate existing data (if you want to preserve it)
INSERT INTO scraper.jobs_jobpost (title, company, apply_link, source, created_at)
SELECT title, company, apply_link, source, created_at FROM public.jobs_jobpost;

INSERT INTO scraper.scraper_errors (source, error, timestamp)
SELECT source, error, timestamp FROM public.scraper_errors;

-- Drop old tables (after confirming migration worked)
-- DROP TABLE public.jobs_jobpost;
-- DROP TABLE public.scraper_errors;