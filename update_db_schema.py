#!/usr/bin/env python3
"""
Update Database Schema for Motorcycle Telemetry
Adds route tracking tables if they don't exist
"""

import sqlite3
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database path
DB_PATH = Path('/home/pi/motorcycle_data/telemetry.db')

def update_schema():
    """Add necessary tables for route tracking if they don't exist"""
    if not DB_PATH.exists():
        logging.error(f"Database not found at {DB_PATH}")
        return False
        
    try:
        logging.info(f"Updating schema for database at {DB_PATH}")
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Check if tracks table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tracks'")
        tracks_exists = cursor.fetchone() is not None
        
        # Check if rides table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rides'")
        rides_exists = cursor.fetchone() is not None
        
        # Check if status table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='status'")
        status_exists = cursor.fetchone() is not None
        
        # Create tracks table if it doesn't exist
        if not tracks_exists:
            logging.info("Creating tracks table")
            cursor.execute('''
            CREATE TABLE tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ride_id TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                latitude REAL,
                longitude REAL,
                altitude REAL,
                speed_mph REAL
            )
            ''')
        
        # Create rides table if it doesn't exist
        if not rides_exists:
            logging.info("Creating rides table")
            cursor.execute('''
            CREATE TABLE rides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ride_id TEXT UNIQUE,
                start_time TEXT,
                end_time TEXT,
                name TEXT,
                distance_miles REAL,
                max_speed_mph REAL,
                avg_speed_mph REAL,
                active INTEGER DEFAULT 1
            )
            ''')
        
        # Create status table if it doesn't exist
        if not status_exists:
            logging.info("Creating status table")
            cursor.execute('''
            CREATE TABLE status (
                id INTEGER PRIMARY KEY,
                current_ride_id TEXT,
                tracking_active INTEGER DEFAULT 0,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Insert default status record
            cursor.execute("INSERT INTO status (id, tracking_active) VALUES (1, 0)")
        
        # Check if we need to add any columns to the telemetry_data table
        cursor.execute("PRAGMA table_info(telemetry_data)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'altitude' not in columns:
            logging.info("Adding altitude column to telemetry_data")
            cursor.execute("ALTER TABLE telemetry_data ADD COLUMN altitude REAL")
        
        if 'satellites_used' not in columns:
            logging.info("Adding satellites_used column to telemetry_data")
            cursor.execute("ALTER TABLE telemetry_data ADD COLUMN satellites_used INTEGER")
        
        conn.commit()
        conn.close()
        
        logging.info("Database schema update complete")
        return True
    except Exception as e:
        logging.error(f"Error updating database schema: {e}")
        return False

if __name__ == "__main__":
    if update_schema():
        print("✅ Database schema updated successfully")
    else:
        print("❌ Failed to update database schema") 