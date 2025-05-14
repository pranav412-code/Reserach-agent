import json
import os
import datetime
import streamlit as st
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, Table, MetaData
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize database objects
engine = None
metadata = None
reports = None

if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL)
        metadata = MetaData()
    except Exception as e:
        st.error(f"Error initializing database engine: {str(e)}")
        
# Only define reports table if metadata is available
if metadata is not None:
    try:
        reports = Table(
            'reports', 
            metadata,
            Column('id', Integer, primary_key=True),
            Column('date', String),
            Column('title', String),
            Column('summary', Text),
            Column('trends', Text),
            Column('challenges', Text),
            Column('solutions', Text),
            Column('sources', Text),
            Column('raw_data', Text),
            Column('created_at', TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
        )
    except Exception as e:
        st.error(f"Error defining database tables: {str(e)}")

def init_db() -> bool:
    """Initialize the database with necessary tables"""
    if not DATABASE_URL:
        st.error("Database URL not found in environment variables")
        return False
    
    if engine is None or metadata is None or reports is None:
        st.error("Database objects not properly initialized")
        return False
    
    try:
        # Create tables
        metadata.create_all(engine)
        return True
    except SQLAlchemyError as e:
        st.error(f"Database initialization error: {str(e)}")
        return False

def save_report(report: Dict[str, Any]) -> int:
    """
    Save a new report to the database
    
    Args:
        report: Dictionary containing the report data
        
    Returns:
        The ID of the newly inserted report
    """
    if engine is None or reports is None:
        st.error("Database not properly initialized")
        return -1
    
    try:
        # Prepare data for insertion
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Convert sources and raw_data to JSON strings
        sources_json = json.dumps(report.get("sources", []))
        raw_data_json = json.dumps(report.get("raw_data", {}))
        
        # Create connection
        conn = engine.connect()
        
        # Insert data
        result = conn.execute(
            reports.insert().values(
                date=today,
                title=report.get("title", f"Manufacturing/IIoT Research Report - {today}"),
                summary=report.get("summary", ""),
                trends=report.get("trends", ""),
                challenges=report.get("challenges", ""),
                solutions=report.get("solutions", ""),
                sources=sources_json,
                raw_data=raw_data_json
            )
        )
        
        # Get the generated ID
        if result.inserted_primary_key is not None:
            report_id = result.inserted_primary_key[0]
        else:
            report_id = -1
            
        # Close connection
        conn.close()
        
        return report_id
        
    except SQLAlchemyError as e:
        st.error(f"Error saving report to database: {str(e)}")
        return -1

def get_reports(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get reports from the database, ordered by date (newest first)
    
    Args:
        limit: Optional limit on the number of reports to return
        
    Returns:
        List of report dictionaries
    """
    if engine is None:
        st.error("Database not properly initialized")
        return []
    
    try:
        # Create connection
        conn = engine.connect()
        
        # Execute query
        query = "SELECT * FROM reports ORDER BY date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        result = conn.execute(text(query))
        
        # Process results
        reports_list = []
        for row in result:
            report_dict = {
                "id": row.id,
                "date": row.date,
                "title": row.title,
                "summary": row.summary,
                "trends": row.trends,
                "challenges": row.challenges,
                "solutions": row.solutions,
                "created_at": row.created_at
            }
            
            # Parse JSON fields
            try:
                report_dict["sources"] = json.loads(row.sources)
            except (json.JSONDecodeError, TypeError):
                report_dict["sources"] = []
            
            try:
                report_dict["raw_data"] = json.loads(row.raw_data)
            except (json.JSONDecodeError, TypeError):
                report_dict["raw_data"] = {}
            
            reports_list.append(report_dict)
        
        # Close connection
        conn.close()
        
        return reports_list
        
    except SQLAlchemyError as e:
        st.error(f"Error retrieving reports from database: {str(e)}")
        return []

def get_report_by_id(report_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific report by ID
    
    Args:
        report_id: The ID of the report to retrieve
        
    Returns:
        Report dictionary or None if not found
    """
    if engine is None:
        st.error("Database not properly initialized")
        return None
    
    try:
        # Create connection
        conn = engine.connect()
        
        # Execute query
        result = conn.execute(text("SELECT * FROM reports WHERE id = :id"), {"id": report_id})
        row = result.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # Convert row to dictionary
        report_dict = {
            "id": row.id,
            "date": row.date,
            "title": row.title,
            "summary": row.summary,
            "trends": row.trends,
            "challenges": row.challenges,
            "solutions": row.solutions,
            "created_at": row.created_at
        }
        
        # Parse JSON fields
        try:
            report_dict["sources"] = json.loads(row.sources)
        except (json.JSONDecodeError, TypeError):
            report_dict["sources"] = []
        
        try:
            report_dict["raw_data"] = json.loads(row.raw_data)
        except (json.JSONDecodeError, TypeError):
            report_dict["raw_data"] = {}
        
        # Close connection
        conn.close()
        
        return report_dict
        
    except SQLAlchemyError as e:
        st.error(f"Error retrieving report from database: {str(e)}")
        return None