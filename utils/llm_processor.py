import os
from typing import List, Dict, Any
import streamlit as st
import time
import json
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI

# Set Google API key from environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

def init_genai():
    """Initialize Google Generative AI API"""
    if not GOOGLE_API_KEY:
        st.error("Google API Key not found in environment variables")
        return False
    
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        return True
    except Exception as e:
        st.error(f"Error initializing Google Generative AI: {str(e)}")
        return False

def process_data_with_langchain(
    search_results: List[Dict[str, Any]],
    scraped_data: List[Dict[str, Any]],
    linkedin_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Process collected data using LangChain and Gemini
    
    Args:
        search_results: List of search results
        scraped_data: List of scraped website content
        linkedin_data: List of LinkedIn data
        
    Returns:
        Dictionary with processed data
    """
    # Initialize Gemini
    if not init_genai():
        st.error("Unable to process data due to API initialization failure")
        return {}
    
    st.info("Processing collected data with LangChain and Gemini...")
    
    # Combine all data into one structured dataset
    combined_data = {
        "search_results": search_results,
        "scraped_content": scraped_data,
        "social_media": linkedin_data
    }
    
    # Process each type of data
    processed_data = {}
    
    # Create a LangChain model instance
    llm = GoogleGenerativeAI(model="gemini-pro", google_api_key=GOOGLE_API_KEY)
    
    # Create a text splitter for chunking long texts
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=10000,
        chunk_overlap=1000
    )
    
    # Process scraped content (most valuable source)
    if scraped_data:
        st.info("Analyzing scraped website content...")
        
        # Extract and process the text content
        all_content = ""
        for item in scraped_data:
            all_content += f"Source: {item['title']} ({item['url']})\n\n"
            all_content += item['content']
            all_content += "\n\n---\n\n"
        
        # Split the content into chunks if it's very large
        docs = text_splitter.create_documents([all_content])
        
        # Create a summarization chain
        summary_template = """
        You are an expert in manufacturing industry and Industrial IoT (IIoT). 
        Analyze the following content from manufacturing and IIoT industry websites and extract key information:

        {text}

        Provide a structured analysis with the following sections:
        1. Main Industry Trends: Identify current trends in manufacturing and IIoT
        2. Industry Challenges: List major challenges facing manufacturers
        3. Emerging Solutions: Describe technological solutions addressing these challenges
        4. Market Insights: Summarize market dynamics and future outlook

        Focus specifically on manufacturing and industrial IoT applications, not consumer IoT.
        """
        
        summary_prompt = PromptTemplate(template=summary_template, input_variables=["text"])
        
        # Apply the chain
        try:
            chain = load_summarize_chain(
                llm, 
                chain_type="map_reduce",
                map_prompt=summary_prompt,
                combine_prompt=summary_prompt,
                verbose=True
            )
            
            summary_result = chain.run(docs)
            processed_data["website_analysis"] = summary_result
            
        except Exception as e:
            st.error(f"Error processing scraped content: {str(e)}")
            # Fallback to direct Gemini API if LangChain fails
            processed_data["website_analysis"] = analyze_with_gemini_direct(all_content[:100000])  # Limit size
    
    # Process LinkedIn data
    if linkedin_data:
        st.info("Analyzing social media content...")
        
        # Combine LinkedIn content
        linkedin_text = ""
        for item in linkedin_data:
            linkedin_text += f"Source: {item.get('company', 'LinkedIn')}\n"
            linkedin_text += item.get('text', '')
            linkedin_text += "\n\n---\n\n"
        
        # Direct analysis with Gemini API (simpler approach for social media)
        processed_data["social_media_analysis"] = analyze_social_media_with_gemini(linkedin_text)
    
    # Generate final insights
    st.info("Generating comprehensive insights...")
    processed_data["comprehensive_insights"] = generate_comprehensive_insights(processed_data)
    
    return processed_data

def analyze_with_gemini_direct(content: str) -> str:
    """
    Analyze content directly with Gemini API (fallback method)
    
    Args:
        content: Text content to analyze
        
    Returns:
        Analysis result
    """
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = """
        You are an expert in manufacturing industry and Industrial IoT (IIoT). 
        Analyze the following content from manufacturing and IIoT industry websites and extract key information:

        [CONTENT]
        {}
        [END CONTENT]

        Provide a structured analysis with the following sections:
        1. Main Industry Trends: Identify current trends in manufacturing and IIoT
        2. Industry Challenges: List major challenges facing manufacturers
        3. Emerging Solutions: Describe technological solutions addressing these challenges
        4. Market Insights: Summarize market dynamics and future outlook

        Focus specifically on manufacturing and industrial IoT applications, not consumer IoT.
        """.format(content)
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error using Gemini API directly: {str(e)}")
        return "Error analyzing content with Gemini API."

def analyze_social_media_with_gemini(content: str) -> str:
    """
    Analyze social media content with Gemini
    
    Args:
        content: Social media content text
        
    Returns:
        Analysis of social media content
    """
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = """
        You are a manufacturing industry expert focusing on Industrial IoT (IIoT).
        Analyze the following social media content from manufacturing companies and industry professionals:

        [CONTENT]
        {}
        [END CONTENT]

        Identify:
        1. Common topics and themes in industry discussions
        2. Current concerns or challenges mentioned by professionals
        3. Emerging technologies or solutions being discussed
        4. Sentiment towards digital transformation and IIoT adoption

        Provide your analysis in a clear, structured format.
        """.format(content)
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error analyzing social media with Gemini: {str(e)}")
        return "Error analyzing social media content."

def generate_comprehensive_insights(processed_data: Dict[str, Any]) -> str:
    """
    Generate comprehensive insights by combining all analyzed data
    
    Args:
        processed_data: Dictionary containing all processed data
        
    Returns:
        Comprehensive insights text
    """
    try:
        # Extract the analyses
        website_analysis = processed_data.get("website_analysis", "No website analysis available.")
        social_media_analysis = processed_data.get("social_media_analysis", "No social media analysis available.")
        
        # Combine them for a comprehensive analysis
        model = genai.GenerativeModel('gemini-pro')
        prompt = """
        You are an expert analyst in the Manufacturing and Industrial IoT (IIoT) sector. 
        You have analyzed various sources including industry websites and social media.
        
        Here is your analysis of industry websites:
        [WEBSITE ANALYSIS]
        {}
        [END WEBSITE ANALYSIS]
        
        Here is your analysis of social media content:
        [SOCIAL MEDIA ANALYSIS]
        {}
        [END SOCIAL MEDIA ANALYSIS]
        
        Based on all this information, provide a comprehensive analysis of the manufacturing and IIoT sector with these sections:
        
        1. **Executive Summary**: A brief overview of the current state of the manufacturing/IIoT industry
        
        2. **Key Industry Trends**: The most significant trends currently shaping the industry
        
        3. **Critical Challenges**: Major obstacles and pain points manufacturers are facing
        
        4. **Innovative Solutions**: How technology is addressing these challenges, particularly IIoT solutions
        
        5. **Market Outlook**: Predictions for the future of manufacturing and IIoT, including opportunities
        
        6. **Strategic Recommendations**: Suggested approaches for manufacturers to navigate the current landscape
        
        Your analysis should be detailed, insightful, and provide actionable information for industry professionals.
        Focus on the connection between challenges and IIoT solutions.
        """.format(website_analysis, social_media_analysis)
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating comprehensive insights: {str(e)}")
        return "Error generating comprehensive insights."
