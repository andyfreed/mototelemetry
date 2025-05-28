#!/usr/bin/env python3
"""
Route Tracker for Motorcycle Telemetry System
Handles tracking and visualization of ride routes
"""

import os
import time
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_file, abort
from flask_cors import CORS
import threading
import math

# Setup logging
logging.basicConfig(
    filename='/home/pi/motorcycle_data/route_tracker.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Create data directory if it doesn't exist
DATA_DIR = Path('/home/pi/motorcycle_data')
DB_PATH = DATA_DIR / 'telemetry.db'

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests

# Database connection parameters
DB_TIMEOUT = 30.0  # Seconds to wait for database lock
DB_RETRIES = 3     # Number of retries for database operations
DB_RETRY_DELAY = 1 # Seconds between retries

def get_db_connection():
    """Get a database connection with timeout settings"""
    return sqlite3.connect(str(DB_PATH), timeout=DB_TIMEOUT)

def execute_with_retry(func, *args, **kwargs):
    """Execute a database function with retry logic"""
    last_error = None
    for attempt in range(DB_RETRIES):
        try:
            return func(*args, **kwargs)
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                logging.warning(f"Database locked, retrying ({attempt+1}/{DB_RETRIES})...")
                last_error = e
                time.sleep(DB_RETRY_DELAY)
            else:
                # Re-raise if it's not a locking error
                raise
    
    # If we got here, all retries failed
    logging.error(f"All database retries failed: {last_error}")
    raise last_error

def setup_database():
    """Initialize or update database with needed tables for route tracking"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create tracks table for storing ride routes if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ride_id TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            latitude REAL,
            longitude REAL,
            altitude REAL,
            speed_mph REAL
        )
        ''')
        
        # Create ride sessions table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rides (
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
        
        # Create status table for storing system state if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS status (
            id INTEGER PRIMARY KEY,
            current_ride_id TEXT,
            tracking_active INTEGER DEFAULT 0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Insert default status row if it doesn't exist
        cursor.execute("INSERT OR IGNORE INTO status (id, tracking_active) VALUES (1, 0)")
        
        conn.commit()
        conn.close()
        logging.info("Route tracker database setup complete")
        return True
    except Exception as e:
        logging.error(f"Route tracker database setup failed: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

def calculate_distance(points):
    """Calculate distance in miles from a list of GPS coordinates"""
    if len(points) < 2:
        return 0
        
    # Haversine formula for calculating distance between coordinates
    distance = 0
    for i in range(1, len(points)):
        # Approximate radius of earth in miles
        R = 3958.8
        
        lat1 = math.radians(points[i-1][0])
        lon1 = math.radians(points[i-1][1])
        lat2 = math.radians(points[i][0])
        lon2 = math.radians(points[i][1])
        
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance += R * c
        
    return distance

def start_ride_db_operations(ride_id, ride_name):
    """Database operations for starting a ride with retry logic"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # End any active rides first
        cursor.execute("UPDATE rides SET active=0, end_time=CURRENT_TIMESTAMP WHERE active=1")
        
        # Create new ride record
        cursor.execute(
            "INSERT INTO rides (ride_id, name, start_time, active) VALUES (?, ?, CURRENT_TIMESTAMP, 1)",
            (ride_id, ride_name)
        )
        
        # Update status table
        cursor.execute(
            "UPDATE status SET current_ride_id=?, tracking_active=1, last_updated=CURRENT_TIMESTAMP WHERE id=1",
            (ride_id,)
        )
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@app.route('/api/start_ride', methods=['POST'])
def start_ride():
    """API endpoint to start a new ride tracking session"""
    try:
        ride_name = request.json.get('name', f"Ride on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Generate a unique ride ID
        ride_id = f"ride_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Execute database operations with retry
        def db_operations():
            return start_ride_db_operations(ride_id, ride_name)
            
        execute_with_retry(db_operations)
        
        logging.info(f"Started new ride: {ride_id}")
        return jsonify({
            'success': True,
            'ride_id': ride_id,
            'message': f"Started tracking ride: {ride_name}"
        })
    except Exception as e:
        logging.error(f"Error starting ride: {e}")
        return jsonify({
            'success': False,
            'message': f"Failed to start ride: {str(e)}"
        }), 500

def end_ride_db_operations(ride_id):
    """Database operations for ending a ride with retry logic"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Calculate ride statistics
        cursor.execute(
            """
            SELECT 
                MAX(speed_mph) as max_speed,
                AVG(speed_mph) as avg_speed,
                COUNT(*) as points
            FROM tracks 
            WHERE ride_id=?
            """, 
            (ride_id,)
        )
        
        stats = cursor.fetchone()
        max_speed = stats[0] if stats[0] else 0
        avg_speed = stats[1] if stats[1] else 0
        
        # Get all track points to calculate distance
        cursor.execute(
            "SELECT latitude, longitude FROM tracks WHERE ride_id=? ORDER BY timestamp",
            (ride_id,)
        )
        
        points = cursor.fetchall()
        distance = calculate_distance(points)
        
        # Update the ride record
        cursor.execute(
            """
            UPDATE rides SET 
                end_time=CURRENT_TIMESTAMP,
                max_speed_mph=?,
                avg_speed_mph=?,
                distance_miles=?,
                active=0
            WHERE ride_id=?
            """,
            (max_speed, avg_speed, distance, ride_id)
        )
        
        # Update status table
        cursor.execute(
            "UPDATE status SET current_ride_id=NULL, tracking_active=0, last_updated=CURRENT_TIMESTAMP WHERE id=1"
        )
        
        conn.commit()
        
        # Get ride details for response
        cursor.execute(
            "SELECT name, start_time, end_time, distance_miles, max_speed_mph, avg_speed_mph FROM rides WHERE ride_id=?",
            (ride_id,)
        )
        
        ride_info = cursor.fetchone()
        return ride_info
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@app.route('/api/end_ride', methods=['POST'])
def end_ride():
    """API endpoint to end the current ride tracking session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the current active ride
        cursor.execute("SELECT current_ride_id FROM status WHERE id=1")
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return jsonify({
                'success': False,
                'message': "No active ride to end"
            }), 400
            
        ride_id = result[0]
        
        # Execute database operations with retry
        def db_operations():
            return end_ride_db_operations(ride_id)
            
        ride_info = execute_with_retry(db_operations)
        
        if ride_info:
            logging.info(f"Ended ride: {ride_id}")
            return jsonify({
                'success': True,
                'ride_id': ride_id,
                'name': ride_info[0],
                'start_time': ride_info[1],
                'end_time': ride_info[2],
                'distance_miles': ride_info[3],
                'max_speed_mph': ride_info[4],
                'avg_speed_mph': ride_info[5],
                'message': f"Ride ended successfully"
            })
        else:
            return jsonify({
                'success': True,
                'message': "Ride ended but details unavailable"
            })
    except Exception as e:
        logging.error(f"Error ending ride: {e}")
        return jsonify({
            'success': False,
            'message': f"Failed to end ride: {str(e)}"
        }), 500

@app.route('/api/tracking_status', methods=['GET'])
def tracking_status():
    """API endpoint to get current ride tracking status"""
    try:
        def get_status():
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT s.tracking_active, s.current_ride_id, r.name, r.start_time
                FROM status s
                LEFT JOIN rides r ON s.current_ride_id = r.ride_id
                WHERE s.id=1
            """)
            
            result = cursor.fetchone()
            conn.close()
            return result
            
        result = execute_with_retry(get_status)
        
        if result:
            is_tracking = bool(result[0])
            ride_id = result[1]
            
            response = {
                'tracking_active': is_tracking
            }
            
            if is_tracking and ride_id:
                response.update({
                    'ride_id': ride_id,
                    'name': result[2],
                    'start_time': result[3]
                })
                
            return jsonify(response)
        else:
            return jsonify({
                'tracking_active': False,
                'message': "Status information not available"
            })
    except Exception as e:
        logging.error(f"Error getting tracking status: {e}")
        return jsonify({
            'success': False,
            'message': f"Failed to get tracking status: {str(e)}"
        }), 500

@app.route('/api/current_ride_track', methods=['GET'])
def current_ride_track():
    """API endpoint to get track points for the current ride"""
    try:
        def get_track_points():
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get current ride ID
            cursor.execute("SELECT current_ride_id FROM status WHERE id=1 AND tracking_active=1")
            result = cursor.fetchone()
            
            if not result or not result[0]:
                conn.close()
                return None, None
                
            ride_id = result[0]
            
            # Get track points for this ride
            cursor.execute(
                """
                SELECT latitude, longitude, altitude, speed_mph, timestamp
                FROM tracks
                WHERE ride_id=?
                ORDER BY timestamp
                """,
                (ride_id,)
            )
            
            points = cursor.fetchall()
            conn.close()
            return ride_id, points
            
        ride_id, points = execute_with_retry(get_track_points)
        
        if ride_id is None:
            return jsonify({
                'success': False,
                'message': "No active ride found"
            }), 404
        
        # Format points for GeoJSON LineString
        if points:
            track_points = []
            for point in points:
                track_points.append({
                    'lat': point[0],
                    'lon': point[1],
                    'alt': point[2],
                    'speed': point[3],
                    'time': point[4]
                })
                
            return jsonify({
                'success': True,
                'ride_id': ride_id,
                'points': track_points,
                'point_count': len(track_points)
            })
        else:
            return jsonify({
                'success': True,
                'ride_id': ride_id,
                'points': [],
                'point_count': 0,
                'message': "No track points recorded yet"
            })
    except Exception as e:
        logging.error(f"Error getting current ride track: {e}")
        return jsonify({
            'success': False,
            'message': f"Failed to get track: {str(e)}"
        }), 500

@app.route('/api/rides', methods=['GET'])
def get_rides():
    """API endpoint to get list of recorded rides"""
    try:
        def get_ride_list():
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT 
                    ride_id, name, start_time, end_time, 
                    distance_miles, max_speed_mph, avg_speed_mph, active
                FROM rides
                ORDER BY start_time DESC
                LIMIT 50
                """
            )
            
            rides = cursor.fetchall()
            conn.close()
            return rides
            
        rides = execute_with_retry(get_ride_list)
        
        ride_list = []
        for ride in rides:
            ride_list.append({
                'ride_id': ride[0],
                'name': ride[1],
                'start_time': ride[2],
                'end_time': ride[3],
                'distance_miles': ride[4],
                'max_speed_mph': ride[5],
                'avg_speed_mph': ride[6],
                'active': bool(ride[7])
            })
            
        return jsonify({
            'success': True,
            'rides': ride_list,
            'count': len(ride_list)
        })
    except Exception as e:
        logging.error(f"Error getting rides: {e}")
        return jsonify({
            'success': False,
            'message': f"Failed to get rides: {str(e)}"
        }), 500

@app.route('/api/ride/<ride_id>/track', methods=['GET'])
def get_ride_track(ride_id):
    """API endpoint to get track points for a specific ride"""
    try:
        def get_track_data():
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verify ride exists
            cursor.execute("SELECT name FROM rides WHERE ride_id=?", (ride_id,))
            ride = cursor.fetchone()
            
            if not ride:
                conn.close()
                return None, None
                
            # Get track points for this ride
            cursor.execute(
                """
                SELECT latitude, longitude, altitude, speed_mph, timestamp
                FROM tracks
                WHERE ride_id=?
                ORDER BY timestamp
                """,
                (ride_id,)
            )
            
            points = cursor.fetchall()
            conn.close()
            return ride, points
            
        ride, points = execute_with_retry(get_track_data)
        
        if ride is None:
            return jsonify({
                'success': False,
                'message': "Ride not found"
            }), 404
            
        # Format points for GeoJSON LineString
        if points:
            track_points = []
            for point in points:
                track_points.append({
                    'lat': point[0],
                    'lon': point[1],
                    'alt': point[2],
                    'speed': point[3],
                    'time': point[4]
                })
                
            return jsonify({
                'success': True,
                'ride_id': ride_id,
                'ride_name': ride[0],
                'points': track_points,
                'point_count': len(track_points)
            })
        else:
            return jsonify({
                'success': True,
                'ride_id': ride_id,
                'ride_name': ride[0],
                'points': [],
                'point_count': 0,
                'message': "No track points recorded for this ride"
            })
    except Exception as e:
        logging.error(f"Error getting ride track: {e}")
        return jsonify({
            'success': False,
            'message': f"Failed to get track: {str(e)}"
        }), 500

@app.route('/api/ride/<ride_id>/geojson', methods=['GET'])
def get_ride_geojson(ride_id):
    """API endpoint to get track points as GeoJSON for a specific ride"""
    try:
        def get_geojson_data():
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verify ride exists
            cursor.execute("SELECT name FROM rides WHERE ride_id=?", (ride_id,))
            ride = cursor.fetchone()
            
            if not ride:
                conn.close()
                return None, None
                
            # Get track points for this ride
            cursor.execute(
                """
                SELECT latitude, longitude, altitude, speed_mph, timestamp
                FROM tracks
                WHERE ride_id=?
                ORDER BY timestamp
                """,
                (ride_id,)
            )
            
            points = cursor.fetchall()
            conn.close()
            return ride, points
            
        ride, points = execute_with_retry(get_geojson_data)
        
        if ride is None:
            return jsonify({
                'success': False,
                'message': "Ride not found"
            }), 404
            
        # Format as GeoJSON
        if not points:
            return jsonify({
                'success': False,
                'message': "No track points for this ride"
            }), 404
            
        # Create GeoJSON LineString
        coordinates = [[point[1], point[0]] for point in points]  # GeoJSON uses [lon, lat]
        
        geojson = {
            "type": "Feature",
            "properties": {
                "name": ride[0],
                "ride_id": ride_id
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            }
        }
        
        return jsonify(geojson)
    except Exception as e:
        logging.error(f"Error getting ride GeoJSON: {e}")
        return jsonify({
            'success': False,
            'message': f"Failed to get GeoJSON: {str(e)}"
        }), 500

def run_api_server():
    """Run the Flask API server"""
    try:
        app.run(host='0.0.0.0', port=5001)
    except Exception as e:
        logging.error(f"API server error: {e}")

if __name__ == "__main__":
    # Setup database
    setup_database()
    
    # Start API server
    logging.info("Starting Route Tracker API server")
    run_api_server() 