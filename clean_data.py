#!/usr/bin/env python3
"""
Data cleaner for startup_details.json
Removes unnecessary fields and keeps only essential startup data
"""

import json
import logging
import re
from typing import Dict, List, Any, Union

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataCleaner:
    """Clean startup data by removing unnecessary fields"""
    
    def __init__(self):
        # Fields to completely remove
        self.remove_fields = {
            # Meta and system fields
            'meta', 'options', 'slug', 'locale', 'type', 'seoTitle', 'searchDescription',
            'socialImage', 'socialText', 'showInMenus', 'numchild', 'urlPath', 
            'depth', 'path', 'pagePtr', 'contentType', 'live', 'hasUnpublishedChanges',
            'lastPublishedAt', 'latestRevisionCreatedAt', 'draftTitle', 'expired',
            'expireAt', 'locked', 'lockedAt', 'lockedBy', 'aliasOf', 'firstPublishedAt',
            
            # Image and media fields
            'previewImage', 'coverImage', 'logo', 'socialImage', 'bannerImage',
            'heroImage', 'galleryImages', 'attachments', 'media', 'images',
            'renditions', 'url', 'alt', 'title', 'originalFilename', 'fileSize',
            'focalPointX', 'focalPointY', 'focalPointWidth', 'focalPointHeight',
            
            # HTML and presentation
            'htmlUrl', 'pagePath', 'detailUrl', 'shareUrl', 'canonicalUrl',
            'forms', 'guestAccessCta', 'guestDownloadCta', 'registerCta', 'labels',
            'downloadBoxTitle', 'downloadButton', 'startupContactButton',
            'startupContactFormTitle', 'startupContactTitle', 'sidebarTitle',
            
            # Wagtail CMS specific
            'wagtailMetadata', 'searchBoost', 'contentJson', 'translationKey',
            'locale', 'aliasOf', 'draftTitle', 'hasUnpublishedChanges',
            
            # Form and UI elements
            'startupContactForm', 'startupContactFormText', 'startupContactFormSubmitButton',
            'startupContactFormOkMessage', 'startupContactFormKoMessage'
        }
        
        # Fields that are image objects (check by structure)
        self.image_indicators = {'url', 'renditions', 'alt', 'originalFilename', 'width', 'height'}
        
        # HTML tag patterns to remove
        self.html_patterns = [
            r'<p[^>]*>',           # Opening p tags with attributes
            r'</p>',               # Closing p tags
            r'<ul[^>]*>',          # Opening ul tags
            r'</ul>',              # Closing ul tags
            r'<li[^>]*>',          # Opening li tags
            r'</li>',              # Closing li tags
            r'<div[^>]*>',         # Opening div tags
            r'</div>',             # Closing div tags
            r'<span[^>]*>',        # Opening span tags
            r'</span>',            # Closing span tags
            r'<br\s*/?>', # BR tags
            r'<strong[^>]*>',      # Opening strong tags
            r'</strong>',          # Closing strong tags
            r'<em[^>]*>',          # Opening em tags
            r'</em>',              # Closing em tags
            r'<h[1-6][^>]*>',      # Opening heading tags
            r'</h[1-6]>',          # Closing heading tags
            r'<a[^>]*>',           # Opening a tags
            r'</a>',               # Closing a tags
            r'data-block-key="[^"]*"',  # Wagtail block keys
        ]
        
        # Keep only these essential fields (whitelist approach for top level)
        self.essential_fields = {
            'id', 'title', 'abstract', 'description', 'payoff',
            'categories', 'tags', 'enablingTechnologies', 
            'fundingStage', 'fundingStageDescription', 'trl',
            'targetCustomers', 'mainApplications', 'revenueModel',
            'competitiveScenario', 'competitiveAdvantages', 
            'businessTraction', 'lookingFor', 'partnerTypes',
            'owners', 'team', 'status', 'initiative',
            'yearEstablished', 'establishmentTimeframe', 'legalForm',
            'locality', 'fiscalId', 'website', 'linkedinPage',
            'employeesNumber', 'revenue', 'isInnovative', 'isAccredited',
            'resolutionStatus', 'scientificPublications', 'publicationLinks',
            'certifications'
        }
    
    def clean_html_text(self, text: str) -> str:
        """Remove HTML tags and clean up text"""
        if not isinstance(text, str):
            return text
        
        # Remove all HTML patterns
        for pattern in self.html_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Clean up whitespace and formatting
        text = re.sub(r'\s+', ' ', text)  # Replace multiple whitespace with single space
        text = text.strip()  # Remove leading/trailing whitespace
        
        # Convert list-like text to proper bullet points
        text = re.sub(r'\s*;\s*', '\n• ', text)  # Convert semicolons to bullet points
        text = re.sub(r'^\s*•\s*', '• ', text, flags=re.MULTILINE)  # Clean up bullet points
        
        return text
    
    def is_image_object(self, obj: Dict[str, Any]) -> bool:
        """Check if an object is an image by its structure"""
        if not isinstance(obj, dict):
            return False
        
        # If it has typical image fields, it's probably an image
        obj_keys = set(obj.keys())
        return len(obj_keys.intersection(self.image_indicators)) >= 2
    
    def clean_value(self, value: Any) -> Any:
        """Clean a single value recursively"""
        if isinstance(value, dict):
            return self.clean_dict(value)
        elif isinstance(value, list):
            return self.clean_list(value)
        elif isinstance(value, str):
            return self.clean_html_text(value)
        else:
            return value
    
    def clean_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a dictionary by removing unwanted fields"""
        if self.is_image_object(data):
            return None  # Remove entire image objects
        
        cleaned = {}
        for key, value in data.items():
            # Skip fields in removal list
            if key in self.remove_fields:
                continue
                
            # Skip if value is None or empty
            if value is None:
                continue
                
            # Clean the value
            cleaned_value = self.clean_value(value)
            
            # Only add if the cleaned value is not None/empty
            if cleaned_value is not None:
                if isinstance(cleaned_value, (list, dict)):
                    if cleaned_value:  # Only add non-empty collections
                        cleaned[key] = cleaned_value
                else:
                    cleaned[key] = cleaned_value
        
        return cleaned
    
    def clean_list(self, data: List[Any]) -> List[Any]:
        """Clean a list by removing unwanted items"""
        cleaned = []
        for item in data:
            cleaned_item = self.clean_value(item)
            if cleaned_item is not None:
                cleaned.append(cleaned_item)
        return cleaned
    
    def clean_startup(self, startup: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a single startup entry"""
        # First apply general cleaning
        cleaned = self.clean_dict(startup)
        
        # Then apply whitelist filtering for top-level fields
        final_cleaned = {}
        for key, value in cleaned.items():
            if key in self.essential_fields:
                final_cleaned[key] = value
        
        return final_cleaned
    
    def clean_all_startups(self, startups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean all startup entries"""
        cleaned_startups = []
        
        logger.info(f"Cleaning {len(startups)} startup entries...")
        
        for i, startup in enumerate(startups):
            try:
                cleaned = self.clean_startup(startup)
                if cleaned:  # Only add non-empty results
                    cleaned_startups.append(cleaned)
                
                if (i + 1) % 50 == 0:
                    logger.info(f"Cleaned {i + 1}/{len(startups)} startups")
                    
            except Exception as e:
                logger.error(f"Error cleaning startup {i}: {e}")
                continue
        
        logger.info(f"Cleaning completed. {len(cleaned_startups)} startups cleaned")
        return cleaned_startups
    
    def get_data_summary(self, startups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary statistics of the cleaned data"""
        if not startups:
            return {"total": 0}
        
        total_startups = len(startups)
        
        # Count field usage
        field_counts = {}
        for startup in startups:
            for field in startup.keys():
                field_counts[field] = field_counts.get(field, 0) + 1
        
        # Sample startup for structure
        sample = startups[0] if startups else {}
        
        return {
            "total_startups": total_startups,
            "fields_per_startup": len(sample.keys()),
            "common_fields": sorted(field_counts.keys()),
            "field_usage": field_counts,
            "sample_startup": {k: type(v).__name__ for k, v in sample.items()}
        }

def main():
    """Main function to clean the startup data"""
    input_file = "startup_details.json"
    output_file = "startup_details_clean.json"
    summary_file = "data_summary.json"
    
    try:
        # Load the raw data
        logger.info(f"Loading data from {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        if not raw_data:
            logger.error("No data found in input file")
            return
        
        logger.info(f"Loaded {len(raw_data)} startup records")
        
        # Clean the data
        cleaner = DataCleaner()
        cleaned_data = cleaner.clean_all_startups(raw_data)
        
        # Save cleaned data
        logger.info(f"Saving cleaned data to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Generate and save summary
        summary = cleaner.get_data_summary(cleaned_data)
        logger.info(f"Saving data summary to {summary_file}")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        
        # Print summary
        logger.info("=" * 50)
        logger.info("DATA CLEANING SUMMARY")
        logger.info("=" * 50)
        logger.info(f"✅ Original records: {len(raw_data)}")
        logger.info(f"✅ Cleaned records: {len(cleaned_data)}")
        logger.info(f"✅ Fields per startup: {summary['fields_per_startup']}")
        logger.info(f"✅ Output file: {output_file}")
        logger.info(f"✅ Summary file: {summary_file}")
        
        if cleaned_data:
            logger.info("\n📋 Sample cleaned startup fields:")
            for field in sorted(cleaned_data[0].keys()):
                logger.info(f"   - {field}")
        
        logger.info(f"\n🎉 Data cleaning completed successfully!")
        
    except FileNotFoundError:
        logger.error(f"Input file {input_file} not found. Run the scraper first.")
    except Exception as e:
        logger.error(f"Error during cleaning: {e}")
        raise

if __name__ == "__main__":
    main()