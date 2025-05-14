import os
from typing import Dict, Any, List
import datetime
import streamlit as st
import google.generativeai as genai

# Set Google API key from environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

def generate_report(processed_data: Dict[str, Any], keywords: str) -> Dict[str, Any]:
    """
    Generate a comprehensive research report from processed data
    
    Args:
        processed_data: Dictionary containing all processed and analyzed data
        keywords: Keywords used for the research
        
    Returns:
        Dictionary containing the complete report
    """
    st.info("Generating final research report...")
    
    if not GOOGLE_API_KEY:
        st.error("Google API Key not found. Using simplified report generation...")
        return generate_simplified_report(processed_data, keywords)
    
    try:
        # Extract insights from processed data
        comprehensive_insights = processed_data.get("comprehensive_insights", "")
        website_analysis = processed_data.get("website_analysis", "")
        social_media_analysis = processed_data.get("social_media_analysis", "")
        
        # Initialize Gemini
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        # Generate report title
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        title_prompt = f"""
        Generate a professional and specific title for a Manufacturing/IIoT industry research report dated {today}.
        The research focused on these keywords: {keywords}.
        Provide only the title, no additional text or formatting.
        """
        title_response = model.generate_content(title_prompt)
        title = title_response.text.strip()
        
        # Generate report summary
        summary_prompt = f"""
        Create an executive summary for an Manufacturing/IIoT industry research report.
        
        The research focused on: {keywords}
        
        Based on the following comprehensive insights:
        {comprehensive_insights[:5000]}
        
        Write a concise but informative executive summary (around 300-400 words) that highlights the key findings,
        major trends, challenges, and solutions in the manufacturing and IIoT sector. The summary should be
        professionally written and provide value to industry executives and decision-makers.
        """
        summary_response = model.generate_content(summary_prompt)
        summary = summary_response.text
        
        # Generate trends section
        trends_prompt = f"""
        Based on the research data about the Manufacturing/IIoT industry:
        
        {website_analysis[:3000]}
        
        {comprehensive_insights[:3000]}
        
        Generate a detailed "Industry Trends" section for a research report. 
        Identify and analyze 5-7 major trends currently shaping the manufacturing and IIoT landscape.
        For each trend, provide:
        1. A clear description of the trend
        2. Evidence of its significance
        3. How it's impacting manufacturers
        4. Early adopters or notable examples
        
        Format this as a well-structured markdown section with proper headers, bullet points, and emphasis where appropriate.
        """
        trends_response = model.generate_content(trends_prompt)
        trends = trends_response.text
        
        # Generate challenges section
        challenges_prompt = f"""
        Based on the research data about the Manufacturing/IIoT industry:
        
        {website_analysis[:2500]}
        
        {social_media_analysis[:2500]}
        
        {comprehensive_insights[:2500]}
        
        Generate a detailed "Industry Challenges" section for a research report.
        Identify and analyze 5-7 critical challenges currently facing manufacturers in relation to digital transformation and IIoT.
        For each challenge, provide:
        1. A clear description of the challenge
        2. Why it's significant
        3. Which segments of manufacturing are most affected
        4. The potential impact if not addressed
        
        Format this as a well-structured markdown section with proper headers, bullet points, and emphasis where appropriate.
        """
        challenges_response = model.generate_content(challenges_prompt)
        challenges = challenges_response.text
        
        # Generate solutions section
        solutions_prompt = f"""
        Based on the research data about the Manufacturing/IIoT industry:
        
        {comprehensive_insights[:3000]}
        
        {website_analysis[:3000]}
        
        Generate a detailed "Solutions & Opportunities" section for a research report.
        Identify and analyze 5-7 promising technological solutions and opportunities that address the challenges in the manufacturing/IIoT space.
        For each solution/opportunity, provide:
        1. A clear description of the solution
        2. Which challenge(s) it addresses
        3. Benefits and potential ROI
        4. Implementation considerations
        5. Examples of successful implementations if available
        
        Format this as a well-structured markdown section with proper headers, bullet points, and emphasis where appropriate.
        """
        solutions_response = model.generate_content(solutions_prompt)
        solutions = solutions_response.text
        
        # Collect sources from processed data
        sources = []
        if "scraped_content" in processed_data:
            for item in processed_data.get("scraped_content", []):
                sources.append({
                    "title": item.get("title", "Unknown Source"),
                    "url": item.get("url", "#")
                })
        
        # Build the complete report
        report = {
            "title": title,
            "date": today,
            "summary": summary,
            "trends": trends,
            "challenges": challenges,
            "solutions": solutions,
            "sources": sources,
            "raw_data": {
                "keywords": keywords,
                "comprehensive_insights": comprehensive_insights
            }
        }
        
        return report
        
    except Exception as e:
        st.error(f"Error generating report: {str(e)}")
        return generate_simplified_report(processed_data, keywords)

def generate_simplified_report(processed_data: Dict[str, Any], keywords: str) -> Dict[str, Any]:
    """
    Generate a simplified report when API access fails
    
    Args:
        processed_data: Processed data
        keywords: Keywords used for research
        
    Returns:
        Simplified report dictionary
    """
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Extract whatever data we have
    comprehensive_insights = processed_data.get("comprehensive_insights", "")
    website_analysis = processed_data.get("website_analysis", "")
    
    # Create sections from available data
    if comprehensive_insights:
        # Try to split the comprehensive insights into sections
        parts = comprehensive_insights.split("\n## ")
        
        summary = parts[0] if parts else "No summary available."
        
        trends = ""
        challenges = ""
        solutions = ""
        
        for part in parts:
            if "trend" in part.lower():
                trends = "## " + part
            elif "challenge" in part.lower():
                challenges = "## " + part
            elif "solution" in part.lower() or "opportunity" in part.lower():
                solutions = "## " + part
    else:
        # Use website analysis if available
        summary = "Research summary not available due to API limitations."
        trends = website_analysis[:1000] if website_analysis else "Trend analysis not available."
        challenges = "Challenge analysis not available."
        solutions = "Solutions analysis not available."
    
    # Collect sources
    sources = []
    if "scraped_content" in processed_data:
        for item in processed_data.get("scraped_content", []):
            sources.append({
                "title": item.get("title", "Unknown Source"),
                "url": item.get("url", "#")
            })
    
    # Build the simplified report
    report = {
        "title": f"Manufacturing & IIoT Industry Research Report - {today}",
        "date": today,
        "summary": summary,
        "trends": trends,
        "challenges": challenges,
        "solutions": solutions,
        "sources": sources,
        "raw_data": {
            "keywords": keywords
        }
    }
    
    return report
