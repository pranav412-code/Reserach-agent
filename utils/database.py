import sqlite3
import json
import os
import datetime
from typing import List, Dict, Any, Optional

# Database file path
DB_FILE = "research_reports.db"

def init_db():
    """Initialize the database with necessary tables"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create reports table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        title TEXT,
        summary TEXT,
        trends TEXT,
        challenges TEXT,
        solutions TEXT,
        sources TEXT,
        raw_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def save_report(report: Dict[str, Any]) -> int:
    """
    Save a new report to the database
    
    Args:
        report: Dictionary containing the report data
        
    Returns:
        The ID of the newly inserted report
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Prepare data for insertion
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Convert sources and raw_data to JSON strings
    sources_json = json.dumps(report.get("sources", []))
    raw_data_json = json.dumps(report.get("raw_data", {}))
    
    cursor.execute('''
    INSERT INTO reports (date, title, summary, trends, challenges, solutions, sources, raw_data)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        today,
        report.get("title", f"Manufacturing/IIoT Research Report - {today}"),
        report.get("summary", ""),
        report.get("trends", ""),
        report.get("challenges", ""),
        report.get("solutions", ""),
        sources_json,
        raw_data_json
    ))
    
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return report_id

def get_reports(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get reports from the database, ordered by date (newest first)
    
    Args:
        limit: Optional limit on the number of reports to return
        
    Returns:
        List of report dictionaries
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if limit:
        cursor.execute('SELECT * FROM reports ORDER BY date DESC LIMIT ?', (limit,))
    else:
        cursor.execute('SELECT * FROM reports ORDER BY date DESC')
    
    rows = cursor.fetchall()
    
    reports = []
    for row in rows:
        # Convert row to dictionary
        report_dict = dict(row)
        
        # Parse JSON fields
        try:
            report_dict["sources"] = json.loads(report_dict["sources"])
        except (json.JSONDecodeError, TypeError):
            report_dict["sources"] = []
        
        try:
            report_dict["raw_data"] = json.loads(report_dict["raw_data"])
        except (json.JSONDecodeError, TypeError):
            report_dict["raw_data"] = {}
        
        reports.append(report_dict)
    
    conn.close()
    return reports

def get_report_by_id(report_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific report by ID
    
    Args:
        report_id: The ID of the report to retrieve
        
    Returns:
        Report dictionary or None if not found
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
    
    # Convert row to dictionary
    report_dict = dict(row)
    
    # Parse JSON fields
    try:
        report_dict["sources"] = json.loads(report_dict["sources"])
    except (json.JSONDecodeError, TypeError):
        report_dict["sources"] = []
    
    try:
        report_dict["raw_data"] = json.loads(report_dict["raw_data"])
    except (json.JSONDecodeError, TypeError):
        report_dict["raw_data"] = {}
    
    conn.close()
    return report_dict
