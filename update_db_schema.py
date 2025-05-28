#!/usr/bin/env python3
"""
Database Schema Update Script
Fixes issues with the motorcycle telemetry database schema
"""

import sqlite3
import os
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path("/home/pi/motorcycle_data/telemetry.db")
BACKUP_PATH = Path("/home/pi/motorcycle_data/telemetry_backup.db")

def backup_database():
    """Create a backup of the database before making changes"""
    if DB_PATH.exists():
        import shutil
        logger.info(f"Creating backup at {BACKUP_PATH}")
        shutil.copy2(DB_PATH, BACKUP_PATH)
        return True
    return False

def update_schema():
    """Update the database schema to fix issues"""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Start a transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Check if we need to update the rides table
        cursor.execute("PRAGMA table_info(rides)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "session_id" not in columns and "ride_id" in columns:
            logger.info("Updating rides table to include session_id")
            
            # Add session_id column if it doesn't exist
            cursor.execute("ALTER TABLE rides ADD COLUMN session_id TEXT")
            
            # Copy values from ride_id to session_id
            cursor.execute("UPDATE rides SET session_id = ride_id")
            
            logger.info("Rides table updated with session_id")
        else:
            logger.info("Rides table already has session_id or no ride_id column")
        
        # Fix the foreign key reference in telemetry_data if needed
        cursor.execute("PRAGMA foreign_key_list(telemetry_data)")
        foreign_keys = cursor.fetchall()
        
        if foreign_keys:
            for fk in foreign_keys:
                if fk[2] == "rides_old":  # If referencing the old table name
                    logger.info("Fixing foreign key reference in telemetry_data")
                    
                    # Create a temporary table with the correct foreign key
                    cursor.execute("""
                    CREATE TABLE telemetry_data_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        timestamp TIMESTAMP,
                        ax REAL, ay REAL, az REAL,
                        gx REAL, gy REAL, gz REAL,
                        mx REAL, my REAL, mz REAL,
                        temperature REAL,
                        vibration_level REAL, 
                        power_voltage REAL, 
                        on_external_power BOOLEAN, 
                        latitude REAL, 
                        longitude REAL, 
                        speed_mph REAL, 
                        heading REAL, 
                        gps_fix BOOLEAN, 
                        satellites_used INTEGER DEFAULT 0, 
                        hdop REAL DEFAULT 99.0, 
                        altitude REAL,
                        FOREIGN KEY (session_id) REFERENCES rides (session_id)
                    )
                    """)
                    
                    # Copy all data
                    cursor.execute("INSERT INTO telemetry_data_new SELECT * FROM telemetry_data")
                    
                    # Drop the old table and rename the new one
                    cursor.execute("DROP TABLE telemetry_data")
                    cursor.execute("ALTER TABLE telemetry_data_new RENAME TO telemetry_data")
                    
                    logger.info("Fixed foreign key reference in telemetry_data")
                    break
        
        # Commit the changes
        conn.commit()
        logger.info("Database schema update completed successfully")
        
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating schema: {e}")
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    logger.info("Starting database schema update")
    
    if not DB_PATH.exists():
        logger.error(f"Database not found at {DB_PATH}")
        exit(1)
    
    if backup_database():
        logger.info("Database backup created successfully")
    else:
        logger.warning("Could not create database backup")
        
    if update_schema():
        logger.info("Schema update completed successfully")
    else:
        logger.error("Schema update failed")
        exit(1)
    
    logger.info("Database schema update script completed") 