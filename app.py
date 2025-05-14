import streamlit as st
import datetime
import os
from utils.database import init_db, get_reports, save_report
from utils.web_search import perform_web_search
from utils.web_scraper import scrape_industry_websites
from utils.social_media import collect_linkedin_data
from utils.llm_processor import process_data_with_langchain
from utils.report_generator import generate_report

st.set_page_config(
    page_title="Manufacturing/IIoT Research Agent",
    page_icon="🏭",
    layout="wide"
)

# Initialize the database
init_db()

def main():
    st.title("Manufacturing/IIoT Research Agent")
    
    # Initialize session state for navigation
    if "page" not in st.session_state:
        st.session_state["page"] = "Dashboard"
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Reports", "Run Research"], index=["Dashboard", "Reports", "Run Research"].index(st.session_state["page"]))
    
    # Update session state
    st.session_state["page"] = page
    
    if page == "Dashboard":
        display_dashboard()
    elif page == "Reports":
        display_reports()
    elif page == "Run Research":
        run_research()

def display_dashboard():
    st.header("Dashboard")
    
    # Get the last report date
    reports = get_reports()
    last_report_date = "No reports yet" if not reports else reports[0]["date"]
    
    # Display stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Reports", value=len(reports))
    with col2:
        st.metric(label="Last Report Date", value=last_report_date)
    with col3:
        next_report_date = "N/A" if not reports else calculate_next_report_date(reports[0]["date"])
        st.metric(label="Next Scheduled Report", value=next_report_date)
    
    # Display quick links
    st.subheader("Quick Links")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("View Latest Report", key="view_latest"):
            if reports:
                st.session_state["page"] = "Reports"
                st.session_state["selected_report"] = 0
                st.rerun()
            else:
                st.warning("No reports available yet. Please run your first research.")
    with col2:
        if st.button("Run New Research", key="run_new"):
            st.session_state["page"] = "Run Research"
            st.rerun()
    
    # Show a preview of the latest report
    if reports:
        st.subheader("Latest Report Preview")
        with st.expander("Preview", expanded=True):
            st.write(reports[0]["summary"])

def calculate_next_report_date(last_date_str):
    try:
        last_date = datetime.datetime.strptime(last_date_str, "%Y-%m-%d")
        next_date = last_date + datetime.timedelta(days=30)  # Approximately one month
        return next_date.strftime("%Y-%m-%d")
    except:
        return "N/A"

def display_reports():
    st.header("Research Reports")
    
    reports = get_reports()
    
    if not reports:
        st.info("No reports available yet. Run your first research using the 'Run Research' tab.")
        return
    
    # Allow selecting reports
    report_dates = [f"{r['date']} - {r['title']}" for r in reports]
    selected_report_index = st.selectbox(
        "Select a report to view",
        range(len(report_dates)),
        format_func=lambda x: report_dates[x]
    )
    
    if selected_report_index is not None:
        report = reports[selected_report_index]
        
        st.subheader(report["title"])
        st.write(f"Date: {report['date']}")
        
        # Display tabs for different report sections
        tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Industry Trends", "Challenges", "Solutions"])
        
        with tab1:
            st.markdown(report["summary"])
        
        with tab2:
            st.markdown(report["trends"])
        
        with tab3:
            st.markdown(report["challenges"])
        
        with tab4:
            st.markdown(report["solutions"])
        
        # Display sources used for the report
        with st.expander("Sources"):
            for source in report["sources"]:
                st.write(f"- [{source['title']}]({source['url']})")
        
        # Add download button for the report
        report_md = f"""# {report["title"]}
Date: {report["date"]}

## Executive Summary
{report["summary"]}

## Industry Trends
{report["trends"]}

## Challenges
{report["challenges"]}

## Solutions
{report["solutions"]}

## Sources
"""
        for source in report["sources"]:
            report_md += f"- [{source['title']}]({source['url']})\n"
            
        st.download_button(
            label="Download Report as Markdown",
            data=report_md,
            file_name=f"research_report_{report['date']}.md",
            mime="text/markdown"
        )

def run_research():
    st.header("Run New Research")
    
    # Calculate when the last report was generated
    reports = get_reports()
    days_since_last_report = 31  # Default to more than a month
    if reports:
        try:
            last_date = datetime.datetime.strptime(reports[0]["date"], "%Y-%m-%d")
            days_since_last_report = (datetime.datetime.now() - last_date).days
        except:
            pass
    
    # Show warning if it's been less than a month
    if days_since_last_report < 30:
        st.warning(f"The last report was generated only {days_since_last_report} days ago. It's recommended to run research monthly.")
    
    # Configuration options
    st.subheader("Research Configuration")
    
    focus_keywords = st.text_input(
        "Focus Keywords (comma-separated)",
        value="manufacturing, IIoT, industrial automation, smart factory, industry 4.0, predictive maintenance"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        num_search_results = st.slider("Number of search results to analyze", 5, 50, 20)
    with col2:
        num_websites_to_scrape = st.slider("Number of websites to scrape", 3, 20, 10)
    
    include_linkedin = st.checkbox("Include LinkedIn data", value=True)
    
    # Run research button
    if st.button("Start Research", type="primary"):
        with st.spinner("Running research..."):
            # Process starts here
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Web Search
            status_text.text("Step 1/5: Performing web search for relevant articles...")
            search_results = perform_web_search(focus_keywords, num_search_results)
            progress_bar.progress(20)
            
            # Step 2: Web Scraping
            status_text.text("Step 2/5: Scraping industry websites for detailed information...")
            scraped_data = scrape_industry_websites(search_results, num_websites_to_scrape)
            progress_bar.progress(40)
            
            # Step 3: Social Media Data (LinkedIn)
            linkedin_data = []
            if include_linkedin:
                status_text.text("Step 3/5: Collecting data from LinkedIn...")
                linkedin_data = collect_linkedin_data(focus_keywords)
            progress_bar.progress(60)
            
            # Step 4: Process data with LangChain
            status_text.text("Step 4/5: Processing and analyzing collected data...")
            processed_data = process_data_with_langchain(search_results, scraped_data, linkedin_data)
            progress_bar.progress(80)
            
            # Step 5: Generate report
            status_text.text("Step 5/5: Generating comprehensive research report...")
            report = generate_report(processed_data, focus_keywords)
            
            # Save the report to the database
            save_report(report)
            
            progress_bar.progress(100)
            status_text.text("Research completed successfully!")
            
        st.success("Research completed and report generated successfully!")
        st.balloons()
        
        # Display a preview of the generated report
        st.subheader("Report Preview")
        st.write(report["summary"])
        
        if st.button("View Full Report"):
            st.session_state["page"] = "Reports"
            st.rerun()

if __name__ == "__main__":
    main()
