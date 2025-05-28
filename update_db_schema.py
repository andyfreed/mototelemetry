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
        
        # Clean up any leftover temporary tables
        cursor.execute("DROP TABLE IF EXISTS rides_old")
        cursor.execute("DROP TABLE IF EXISTS rides_new")
        
        # Get the exact schema of the rides table
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='rides'")
        rides_schema = cursor.fetchone()
        if rides_schema:
            logging.info(f"Current rides table schema: {rides_schema[0]}")
        
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
        
        # Fix or create rides table
        if rides_exists:
            # Get existing columns in rides table
            cursor.execute("PRAGMA table_info(rides)")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            
            logging.info(f"Existing columns in rides table: {columns}")
            
            # Check if ride_id exists - if it does, we're already migrated
            if 'ride_id' in columns:
                logging.info("rides table already has ride_id column, skipping migration")
                
                # Just ensure all necessary columns exist
                for column_name, column_type in [
                    ('name', 'TEXT'), 
                    ('distance_miles', 'REAL'), 
                    ('max_speed_mph', 'REAL'), 
                    ('avg_speed_mph', 'REAL'),
                    ('active', 'INTEGER'),
                    ('uploaded', 'INTEGER')
                ]:
                    if column_name not in columns:
                        logging.info(f"Adding {column_name} column to rides table")
                        cursor.execute(f"ALTER TABLE rides ADD COLUMN {column_name} {column_type}")
                
            # Check if we need to rename session_id to ride_id
            elif 'session_id' in columns and 'ride_id' not in columns:
                logging.info("Need to rename session_id to ride_id")
                
                # We need to create a new table with our desired schema
                cursor.execute("ALTER TABLE rides RENAME TO rides_old")
                
                # Create the new table with correct schema
                cursor.execute('''
                CREATE TABLE rides (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ride_id TEXT UNIQUE,
                    start_time TEXT,
                    end_time TEXT,
                    name TEXT DEFAULT NULL,
                    distance_miles REAL DEFAULT NULL,
                    max_speed_mph REAL DEFAULT NULL,
                    avg_speed_mph REAL DEFAULT NULL,
                    active INTEGER DEFAULT 1,
                    uploaded INTEGER DEFAULT 0
                )
                ''')
                
                # Copy data from old table to new table
                logging.info("Migrating data from old rides table to new schema")
                cursor.execute('''
                INSERT INTO rides (ride_id, start_time, end_time, active, uploaded) 
                SELECT session_id, start_time, end_time, 
                       COALESCE(active, 0), 
                       COALESCE(uploaded, 0) 
                FROM rides_old
                ''')
                
                # Update names for existing rides
                cursor.execute('''
                UPDATE rides SET name = 'Ride on ' || datetime(start_time) 
                WHERE name IS NULL AND start_time IS NOT NULL
                ''')
                
                logging.info("Data migration complete")
                
                # Drop the old table
                cursor.execute("DROP TABLE IF EXISTS rides_old")
            else:
                logging.warning("rides table exists but doesn't have session_id or ride_id, this is unexpected")
        else:
            # Create rides table with all necessary columns
            logging.info("Creating rides table from scratch")
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
                active INTEGER DEFAULT 1,
                uploaded INTEGER DEFAULT 0
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
        if 'conn' in locals():
            try:
                conn.close()
            except:
                pass
        return False

if __name__ == "__main__":
    if update_schema():
        print("✅ Database schema updated successfully")
    else:
        print("❌ Failed to update database schema") 