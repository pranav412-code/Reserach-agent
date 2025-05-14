import os
import requests
import time
import random
from typing import List, Dict, Any, Optional
import json
import streamlit as st
from utils.web_scraper import get_website_text_content  # Reusing web scraper functionality

# LinkedIn API credentials from environment variables
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")

def collect_linkedin_data(keywords: str) -> List[Dict[str, Any]]:
    """
    Collect data from LinkedIn related to the manufacturing/IIoT industry
    
    Args:
        keywords: Keywords to search for on LinkedIn
        
    Returns:
        List of dictionaries containing LinkedIn data (posts, articles, etc.)
    """
    # Check if LinkedIn API credentials are available
    if not all([LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_ACCESS_TOKEN]):
        st.warning("LinkedIn API credentials not found. Using alternative approach...")
        return collect_linkedin_alternative(keywords)
    
    try:
        # Build the LinkedIn API request
        linkedin_data = []
        
        # Format keywords for search
        search_terms = [k.strip() for k in keywords.split(",")]
        
        for term in search_terms[:3]:  # Limit to 3 keywords to avoid rate limiting
            # LinkedIn Marketing API (Posts Search) - requires Marketing Developer Platform access
            headers = {
                "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # Note: Actual endpoint would depend on the specific LinkedIn API access level
            # This is a simplified example and may need to be adjusted based on available permissions
            response = requests.get(
                "https://api.linkedin.com/v2/posts",
                headers=headers,
                params={
                    "q": f"search?keywords={term}",
                    "count": 10
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get("elements", [])
                
                for post in posts:
                    linkedin_data.append({
                        "type": "post",
                        "text": post.get("text", {}).get("text", ""),
                        "author": post.get("author", ""),
                        "published": post.get("published", {}).get("date", ""),
                        "url": f"https://www.linkedin.com/feed/update/{post.get('id', '')}"
                    })
            
            # Add delay to avoid rate limiting
            time.sleep(2)
        
        return linkedin_data
        
    except Exception as e:
        st.error(f"Error collecting LinkedIn data: {str(e)}")
        return collect_linkedin_alternative(keywords)

def collect_linkedin_alternative(keywords: str) -> List[Dict[str, Any]]:
    """
    Alternative approach to collect LinkedIn content when API is not available
    Scrapes public LinkedIn content from company pages and hashtag searches
    
    Args:
        keywords: Keywords to search for
        
    Returns:
        List of LinkedIn content
    """
    linkedin_data = []
    
    # List of manufacturing/IIoT companies and hashtags to check
    companies = [
        {"name": "Siemens Digital Industries", "url": "https://www.linkedin.com/company/siemens-digital-industries-software/posts/"},
        {"name": "Rockwell Automation", "url": "https://www.linkedin.com/company/rockwell-automation/posts/"},
        {"name": "GE Digital", "url": "https://www.linkedin.com/company/ge-digital/posts/"},
        {"name": "ABB", "url": "https://www.linkedin.com/company/abb/posts/"},
        {"name": "Schneider Electric", "url": "https://www.linkedin.com/company/schneider-electric/posts/"},
        {"name": "Honeywell", "url": "https://www.linkedin.com/company/honeywell/posts/"},
        {"name": "Bosch", "url": "https://www.linkedin.com/company/bosch/posts/"},
        {"name": "PTC", "url": "https://www.linkedin.com/company/ptc/posts/"}
    ]
    
    # Use streamlit progress tracking
    linkedin_progress = st.progress(0)
    linkedin_status = st.empty()
    
    for i, company in enumerate(companies):
        # Update progress
        progress_pct = (i + 1) / len(companies)
        linkedin_progress.progress(progress_pct)
        linkedin_status.text(f"Checking LinkedIn content from: {company['name']}")
        
        try:
            # Get the public company page
            content = get_website_text_content(company["url"])
            
            if content:
                # Process the content
                lines = content.split('\n')
                # Filter out very short lines and keep relevant content
                filtered_lines = [line for line in lines if len(line) > 50]
                
                # Extract what appears to be posts
                for line in filtered_lines[:5]:  # Limit to 5 potential posts per company
                    linkedin_data.append({
                        "type": "company_post",
                        "company": company["name"],
                        "text": line,
                        "url": company["url"]
                    })
            
            # Be polite to LinkedIn servers
            time.sleep(random.uniform(2.0, 3.0))
            
        except Exception as e:
            st.warning(f"Error scraping LinkedIn data from {company['name']}: {str(e)}")
    
    linkedin_status.text(f"Completed collecting data from {len(linkedin_data)} LinkedIn sources")
    
    return linkedin_data
