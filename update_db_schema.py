#!/usr/bin/env python3
"""
Update database schema for motorcycle telemetry system
"""

import sqlite3
from pathlib import Path

DATA_DIR = Path("/home/pi/motorcycle_data")
DB_PATH = DATA_DIR / "telemetry.db"

def update_schema():
    """Update database schema to current version"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check current schema
    cursor.execute("PRAGMA table_info(telemetry_data)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Current columns: {columns}")
    
    # Add missing columns if they don't exist
    required_columns = [
        ('vibration_level', 'REAL'),
        ('power_voltage', 'REAL'), 
        ('on_external_power', 'BOOLEAN'),
        ('latitude', 'REAL'),
        ('longitude', 'REAL'),
        ('speed_mph', 'REAL'),
        ('heading', 'REAL'),
        ('gps_fix', 'BOOLEAN')
    ]
    
    for column_name, column_type in required_columns:
        if column_name not in columns:
            try:
                cursor.execute(f'ALTER TABLE telemetry_data ADD COLUMN {column_name} {column_type}')
                print(f"Added column: {column_name}")
            except sqlite3.OperationalError as e:
                print(f"Column {column_name} already exists or error: {e}")
    
    # Remove old columns that might cause issues (altitude, speed)
    # SQLite doesn't support DROP COLUMN, so we'll recreate the table if needed
    cursor.execute("PRAGMA table_info(telemetry_data)")
    current_schema = cursor.fetchall()
    
    # Check if we have old columns that need to be removed
    old_columns = ['altitude', 'speed']
    has_old_columns = any(col[1] in old_columns for col in current_schema)
    
    if has_old_columns:
        print("Recreating table to remove old columns...")
        
        # Create new table with correct schema
        cursor.execute('''
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
                FOREIGN KEY (session_id) REFERENCES rides (session_id)
            )
        ''')
        
        # Copy data from old table, mapping columns appropriately
        cursor.execute('''
            INSERT INTO telemetry_data_new 
            (id, session_id, timestamp, ax, ay, az, gx, gy, gz, mx, my, mz, 
             temperature, vibration_level, power_voltage, on_external_power, 
             latitude, longitude, speed_mph, heading, gps_fix)
            SELECT 
                id, session_id, timestamp, ax, ay, az, gx, gy, gz, mx, my, mz,
                temperature, vibration_level, power_voltage, on_external_power,
                latitude, longitude, speed_mph, heading, gps_fix
            FROM telemetry_data
        ''')
        
        # Drop old table and rename new one
        cursor.execute('DROP TABLE telemetry_data')
        cursor.execute('ALTER TABLE telemetry_data_new RENAME TO telemetry_data')
        
        print("Table recreated with correct schema")
    
    conn.commit()
    conn.close()
    print("Database schema updated successfully!")

if __name__ == "__main__":
    update_schema() 