#!/usr/bin/env python3
"""
Motorcycle Telemetry Data Exporter
Exports ride data for Grafana visualization
"""

import sqlite3
import json
import csv
import argparse
import sys
from datetime import datetime
from pathlib import Path
from influxdb import InfluxDBClient

DATA_DIR = Path("/home/pi/motorcycle_data")
DB_PATH = DATA_DIR / "telemetry.db"

class DataExporter:
    def __init__(self):
        self.db_path = DB_PATH
        
    def get_rides(self):
        """Get list of all rides"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.session_id, r.start_time, r.end_time, 
                   COUNT(td.id) as data_points
            FROM rides r
            LEFT JOIN telemetry_data td ON r.session_id = td.session_id
            GROUP BY r.session_id, r.start_time, r.end_time
            ORDER BY r.start_time DESC
        ''')
        
        rides = cursor.fetchall()
        conn.close()
        return rides
        
    def export_ride_json(self, session_id, output_file=None):
        """Export ride data as JSON"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get ride info
        cursor.execute('SELECT * FROM rides WHERE session_id = ?', (session_id,))
        ride_info = cursor.fetchone()
        
        if not ride_info:
            print(f"Ride {session_id} not found")
            return
            
        # Get telemetry data with correct schema
        cursor.execute('''
            SELECT timestamp, latitude, longitude, speed_mph, heading,
                   ax, ay, az, gx, gy, gz, mx, my, mz, temperature,
                   vibration_level, power_voltage, on_external_power, gps_fix
            FROM telemetry_data 
            WHERE session_id = ? 
            ORDER BY timestamp
        ''', (session_id,))
        
        telemetry = cursor.fetchall()
        conn.close()
        
        # Format data
        ride_data = {
            'session_id': session_id,
            'start_time': ride_info[2],
            'end_time': ride_info[3],
            'data_points': len(telemetry),
            'telemetry': []
        }
        
        for row in telemetry:
            ride_data['telemetry'].append({
                'timestamp': row[0],
                'gps': {
                    'latitude': row[1],
                    'longitude': row[2],
                    'speed_mph': row[3],
                    'heading': row[4],
                    'gps_fix': row[18]
                },
                'imu': {
                    'acceleration': {'x': row[5], 'y': row[6], 'z': row[7]},
                    'gyroscope': {'x': row[8], 'y': row[9], 'z': row[10]},
                    'magnetometer': {'x': row[11], 'y': row[12], 'z': row[13]},
                    'temperature': row[14]
                },
                'power': {
                    'vibration_level': row[15],
                    'power_voltage': row[16],
                    'on_external_power': row[17]
                }
            })
            
        # Output
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(ride_data, f, indent=2)
            print(f"Exported to {output_file}")
        else:
            print(json.dumps(ride_data, indent=2))
            
    def export_ride_csv(self, session_id, output_file=None):
        """Export ride data as CSV for Grafana CSV datasource"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, latitude, longitude, speed_mph, heading,
                   ax, ay, az, gx, gy, gz, mx, my, mz, temperature,
                   vibration_level, power_voltage, on_external_power, gps_fix
            FROM telemetry_data 
            WHERE session_id = ? 
            ORDER BY timestamp
        ''', (session_id,))
        
        data = cursor.fetchall()
        conn.close()
        
        if not data:
            print(f"No data found for ride {session_id}")
            return
            
        headers = [
            'timestamp', 'latitude', 'longitude', 'speed_mph', 'heading',
            'accel_x', 'accel_y', 'accel_z',
            'gyro_x', 'gyro_y', 'gyro_z',
            'mag_x', 'mag_y', 'mag_z', 'temperature',
            'vibration_level', 'power_voltage', 'on_external_power', 'gps_fix'
        ]
        
        if output_file:
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(data)
            print(f"Exported to {output_file}")
        else:
            writer = csv.writer(sys.stdout)
            writer.writerow(headers)
            writer.writerows(data)
            
    def export_to_influxdb(self, session_id, influx_host='localhost', influx_port=8086, influx_db='motorcycle_telemetry'):
        """Export ride data directly to InfluxDB"""
        try:
            client = InfluxDBClient(host=influx_host, port=influx_port, database=influx_db)
            
            # Ensure database exists
            client.create_database(influx_db)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, latitude, longitude, speed_mph, heading,
                       ax, ay, az, gx, gy, gz, mx, my, mz, temperature,
                       vibration_level, power_voltage, on_external_power, gps_fix
                FROM telemetry_data 
                WHERE session_id = ? 
                ORDER BY timestamp
            ''', (session_id,))
            
            data = cursor.fetchall()
            conn.close()
            
            if not data:
                print(f"No data found for ride {session_id}")
                return
                
            points = []
            for row in data:
                timestamp = datetime.fromisoformat(row[0].replace('Z', '+00:00'))
                
                # GPS data point
                if row[1] is not None and row[18]:  # latitude and gps_fix
                    gps_point = {
                        "measurement": "gps",
                        "tags": {
                            "session": session_id
                        },
                        "time": timestamp,
                        "fields": {
                            "latitude": float(row[1]),
                            "longitude": float(row[2])
                        }
                    }
                    if row[3] is not None:
                        gps_point["fields"]["speed_mph"] = float(row[3])
                    if row[4] is not None:
                        gps_point["fields"]["heading"] = float(row[4])
                    points.append(gps_point)
                
                # IMU data points
                if row[5] is not None:  # accelerometer
                    points.append({
                        "measurement": "imu",
                        "tags": {
                            "session": session_id,
                            "sensor": "accelerometer"
                        },
                        "time": timestamp,
                        "fields": {
                            "x": float(row[5]),
                            "y": float(row[6]),
                            "z": float(row[7])
                        }
                    })
                    
                if row[8] is not None:  # gyroscope
                    points.append({
                        "measurement": "imu",
                        "tags": {
                            "session": session_id,
                            "sensor": "gyroscope"
                        },
                        "time": timestamp,
                        "fields": {
                            "x": float(row[8]),
                            "y": float(row[9]),
                            "z": float(row[10])
                        }
                    })
                    
                if row[11] is not None:  # magnetometer
                    points.append({
                        "measurement": "imu",
                        "tags": {
                            "session": session_id,
                            "sensor": "magnetometer"
                        },
                        "time": timestamp,
                        "fields": {
                            "x": float(row[11]),
                            "y": float(row[12]),
                            "z": float(row[13])
                        }
                    })
                    
                if row[14] is not None:  # temperature
                    points.append({
                        "measurement": "temperature",
                        "tags": {
                            "session": session_id
                        },
                        "time": timestamp,
                        "fields": {
                            "value": float(row[14])
                        }
                    })
                
                # Power data (vibration data collection disabled)
                if row[16] is not None:  # power_voltage
                    points.append({
                        "measurement": "power",
                        "tags": {
                            "session": session_id
                        },
                        "time": timestamp,
                        "fields": {
                            "voltage": float(row[16]),
                            "external_power": bool(row[17])
                        }
                    })
            
            # Write points to InfluxDB
            client.write_points(points)
            print(f"Successfully exported {len(points)} data points to InfluxDB for session {session_id}")
            
        except Exception as e:
            print(f"Error exporting to InfluxDB: {e}")
            
    def export_all_rides_to_influxdb(self, influx_host='localhost', influx_port=8086, influx_db='motorcycle_telemetry'):
        """Export all rides to InfluxDB"""
        rides = self.get_rides()
        for ride in rides:
            session_id = ride[0]
            print(f"Exporting ride {session_id}...")
            self.export_to_influxdb(session_id, influx_host, influx_port, influx_db)

def main():
    parser = argparse.ArgumentParser(description='Export motorcycle telemetry data')
    parser.add_argument('command', choices=['list', 'export', 'influxdb', 'sync-all'], help='Command to run')
    parser.add_argument('--session', help='Session ID to export')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    parser.add_argument('--output', help='Output file (default: stdout)')
    parser.add_argument('--influx-host', default='localhost', help='InfluxDB host (default: localhost)')
    parser.add_argument('--influx-port', type=int, default=8086, help='InfluxDB port (default: 8086)')
    parser.add_argument('--influx-db', default='motorcycle_telemetry', help='InfluxDB database (default: motorcycle_telemetry)')
    
    args = parser.parse_args()
    
    exporter = DataExporter()
    
    if args.command == 'list':
        print("Available rides:")
        print("Session ID          | Start Time           | End Time             | Data Points")
        print("-" * 80)
        for ride in exporter.get_rides():
            session_id, start_time, end_time, data_points = ride
            end_str = end_time if end_time else "In Progress"
            print(f"{session_id:<18} | {start_time:<19} | {end_str:<19} | {data_points}")
            
    elif args.command == 'export':
        if not args.session:
            print("Please specify --session for export")
            return
            
        if args.format == 'json':
            exporter.export_ride_json(args.session, args.output)
        elif args.format == 'csv':
            exporter.export_ride_csv(args.session, args.output)
            
    elif args.command == 'influxdb':
        if not args.session:
            print("Please specify --session for InfluxDB export")
            return
        exporter.export_to_influxdb(args.session, args.influx_host, args.influx_port, args.influx_db)
        
    elif args.command == 'sync-all':
        print("Syncing all rides to InfluxDB...")
        exporter.export_all_rides_to_influxdb(args.influx_host, args.influx_port, args.influx_db)

if __name__ == "__main__":
    main() 