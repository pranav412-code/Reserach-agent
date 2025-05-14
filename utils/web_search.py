import os
import json
import requests
from typing import List, Dict, Any
import time
import streamlit as st

# Get Tavily API key from environment variable
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

def perform_web_search(keywords: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """
    Perform a web search using Tavily API for industry-specific information
    
    Args:
        keywords: Comma-separated keywords to search for
        max_results: Maximum number of search results to return
        
    Returns:
        List of dictionaries containing search results with title, url, and snippet
    """
    if not TAVILY_API_KEY:
        st.warning("Tavily API key not found. Using fallback search approach...")
        return perform_fallback_search(keywords, max_results)
    
    # Format keywords for search query
    search_query = " ".join([kw.strip() for kw in keywords.split(",")])
    search_query += " manufacturing industry IIoT trends challenges solutions"
    
    try:
        # Call Tavily API
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": TAVILY_API_KEY
        }
        
        payload = {
            "query": search_query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_domains": [
                "industryweek.com", "iiot-world.com", "iotworldtoday.com", 
                "manufacturingtomorrow.com", "machinedesign.com", "automationworld.com",
                "manufacturing.net", "forbes.com", "mckinsey.com", "gartner.com",
                "pwc.com", "deloitte.com", "idc.com", "forrester.com", "capgemini.com"
            ]
        }
        
        response = requests.post(
            "https://api.tavily.com/search",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])
        else:
            st.error(f"Tavily API error: {response.status_code} - {response.text}")
            return perform_fallback_search(keywords, max_results)
            
    except Exception as e:
        st.error(f"Error performing web search: {str(e)}")
        return perform_fallback_search(keywords, max_results)

def perform_fallback_search(keywords: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """
    Fallback search function when Tavily API is not available
    Uses a free search API or structured manual search
    
    Args:
        keywords: Comma-separated keywords to search for
        max_results: Maximum number of search results to return
        
    Returns:
        List of dictionaries containing search results
    """
    # Try using SerpAPI if available
    serpapi_key = os.getenv("SERPAPI_KEY", "")
    if serpapi_key:
        return serpapi_search(keywords, max_results, serpapi_key)
    
    # If no API keys are available, return a list of well-known industry resources
    # that can be scraped directly
    return [
        {
            "title": "IIoT World - Industrial IoT News & Articles",
            "url": "https://iiot-world.com/",
            "snippet": "Latest news and insights about Industrial IoT, smart manufacturing, and industry 4.0 technologies."
        },
        {
            "title": "Manufacturing Tomorrow - Smart Manufacturing and Industry 4.0",
            "url": "https://www.manufacturingtomorrow.com/",
            "snippet": "Articles and insights about the future of manufacturing, IIoT adoption, and digital transformation."
        },
        {
            "title": "Automation World - Factory Automation",
            "url": "https://www.automationworld.com/",
            "snippet": "Coverage of automation technologies in manufacturing and production environments."
        },
        {
            "title": "McKinsey & Company - Manufacturing",
            "url": "https://www.mckinsey.com/industries/advanced-electronics/our-insights",
            "snippet": "Research and insights on manufacturing industry trends and digital transformation."
        },
        {
            "title": "Deloitte Insights - Industry 4.0",
            "url": "https://www2.deloitte.com/us/en/insights/focus/industry-4-0.html",
            "snippet": "Research and analysis on the fourth industrial revolution and smart manufacturing."
        },
        {
            "title": "PwC - Industrial Manufacturing Trends",
            "url": "https://www.pwc.com/us/en/industries/industrial-products/industrial-manufacturing.html",
            "snippet": "Analysis of trends and challenges in the industrial manufacturing sector."
        },
        {
            "title": "Industry Week - Technology and IIoT",
            "url": "https://www.industryweek.com/technology-and-iiot",
            "snippet": "News and analysis covering IIoT implementation in manufacturing environments."
        },
        {
            "title": "Manufacturing.net - Industry 4.0",
            "url": "https://www.manufacturing.net/industry40",
            "snippet": "Coverage of Industry 4.0 technologies and their impact on manufacturing."
        },
        {
            "title": "IoT World Today - Industrial IoT",
            "url": "https://www.iotworldtoday.com/industrial/",
            "snippet": "News and insights about industrial IoT implementations and technologies."
        },
        {
            "title": "Gartner - Manufacturing Industry Insights",
            "url": "https://www.gartner.com/en/industries/manufacturing",
            "snippet": "Research and analysis on digital transformation in manufacturing."
        }
    ][:max_results]

def serpapi_search(keywords: str, max_results: int, api_key: str) -> List[Dict[str, Any]]:
    """
    Perform a search using SerpAPI as a fallback
    
    Args:
        keywords: Keywords to search for
        max_results: Maximum number of results to return
        api_key: SerpAPI API key
        
    Returns:
        List of search results
    """
    search_query = " ".join([kw.strip() for kw in keywords.split(",")])
    search_query += " manufacturing industry IIoT trends challenges solutions"
    
    try:
        response = requests.get(
            "https://serpapi.com/search",
            params={
                "q": search_query,
                "api_key": api_key,
                "num": max_results
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            organic_results = data.get("organic_results", [])
            
            return [
                {
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                }
                for result in organic_results[:max_results]
            ]
        else:
            st.error(f"SerpAPI error: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        st.error(f"Error with SerpAPI search: {str(e)}")
        return []
