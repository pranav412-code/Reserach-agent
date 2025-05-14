import requests
from bs4 import BeautifulSoup
import trafilatura
from typing import List, Dict, Any, Optional
import time
import random
import streamlit as st

def scrape_industry_websites(search_results: List[Dict[str, Any]], max_sites: int = 10) -> List[Dict[str, Any]]:
    """
    Scrape content from industry websites found in search results
    
    Args:
        search_results: List of search result dictionaries with urls
        max_sites: Maximum number of sites to scrape
        
    Returns:
        List of dictionaries containing scraped content
    """
    scraped_data = []
    
    # Process only up to max_sites
    sites_to_scrape = search_results[:max_sites]
    
    # Use Streamlit progress tracking
    scraping_progress = st.progress(0)
    scraping_status = st.empty()
    
    for i, result in enumerate(sites_to_scrape):
        url = result.get("url")
        title = result.get("title", "")
        
        if not url:
            continue
        
        # Update progress
        progress_pct = (i + 1) / len(sites_to_scrape)
        scraping_progress.progress(progress_pct)
        scraping_status.text(f"Scraping {i+1}/{len(sites_to_scrape)}: {title[:50]}...")
        
        try:
            # Get the main text content
            content = get_website_text_content(url)
            
            if content:
                scraped_data.append({
                    "title": title,
                    "url": url,
                    "content": content
                })
            
            # Add a small delay to be polite to the servers
            time.sleep(random.uniform(1.0, 2.0))
            
        except Exception as e:
            st.warning(f"Error scraping {url}: {str(e)}")
    
    scraping_status.text(f"Completed scraping {len(scraped_data)} websites")
    
    return scraped_data

def get_website_text_content(url: str) -> Optional[str]:
    """
    Extract the main text content from a website using trafilatura
    
    Args:
        url: URL of the website to scrape
        
    Returns:
        Extracted text content or None if extraction failed
    """
    try:
        # Send a request to the website
        downloaded = trafilatura.fetch_url(url)
        
        if not downloaded:
            # Fallback to requests + BeautifulSoup if trafilatura fetch fails
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Try to extract with trafilatura from the response content
                text = trafilatura.extract(response.text)
                
                # If trafilatura extraction fails, use BeautifulSoup
                if not text:
                    text = extract_with_beautifulsoup(response.text)
                
                return text
            else:
                return None
        
        # Extract the text from the downloaded content
        text = trafilatura.extract(downloaded)
        
        if not text:
            # If trafilatura extraction fails, parse with BeautifulSoup
            text = extract_with_beautifulsoup(downloaded)
        
        return text
    
    except Exception as e:
        st.warning(f"Error extracting content from {url}: {str(e)}")
        return None

def extract_with_beautifulsoup(html_content: str) -> str:
    """
    Extract main content from HTML using BeautifulSoup as a fallback
    
    Args:
        html_content: HTML content to parse
        
    Returns:
        Extracted text content
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.extract()
    
    # Extract text from paragraphs and headers
    paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
    
    # Join the paragraphs with newlines
    text = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
    
    return text
