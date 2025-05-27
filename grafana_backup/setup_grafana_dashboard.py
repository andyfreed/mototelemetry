#!/usr/bin/env python3
"""
Setup Grafana Dashboard for Motorcycle Telemetry
Automatically configures InfluxDB data source and imports dashboard
"""

import requests
import json
import time
import sys

# Grafana configuration
GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin"

# InfluxDB configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_DB = "motorcycle_telemetry"

def wait_for_grafana():
    """Wait for Grafana to be ready"""
    print("Waiting for Grafana to be ready...")
    for i in range(30):
        try:
            response = requests.get(f"{GRAFANA_URL}/api/health")
            if response.status_code == 200:
                print("✅ Grafana is ready!")
                return True
        except:
            pass
        time.sleep(2)
    return False

def setup_data_source():
    """Setup InfluxDB data source in Grafana"""
    print("Setting up InfluxDB data source...")
    
    # Use basic authentication 
    import base64
    credentials = base64.b64encode(f"{GRAFANA_USER}:{GRAFANA_PASS}".encode()).decode()
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json'
    }
    
    # Test authentication
    response = requests.get(f"{GRAFANA_URL}/api/org", headers=headers)
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Check if data source already exists
    response = requests.get(f"{GRAFANA_URL}/api/datasources", headers=headers)
    if response.status_code == 200:
        datasources = response.json()
        for ds in datasources:
            if ds.get('name') == 'InfluxDB-Motorcycle':
                print("✅ InfluxDB data source already exists")
                return True
    
    # Create InfluxDB data source
    datasource_config = {
        "name": "InfluxDB-Motorcycle",
        "type": "influxdb",
        "url": INFLUXDB_URL,
        "access": "proxy",
        "database": INFLUXDB_DB,
        "isDefault": True,
        "jsonData": {
            "httpMode": "GET",
            "keepCookies": []
        },
        "secureJsonFields": {}
    }
    
    response = requests.post(f"{GRAFANA_URL}/api/datasources", 
                           json=datasource_config, headers=headers)
    
    if response.status_code in [200, 409]:  # 409 = already exists
        print("✅ InfluxDB data source created successfully")
        return True
    else:
        print(f"❌ Failed to create data source: {response.status_code} - {response.text}")
        return False

def create_dashboard():
    """Create motorcycle telemetry dashboard"""
    print("Creating motorcycle telemetry dashboard...")
    
    # Use same authentication headers
    import base64
    credentials = base64.b64encode(f"{GRAFANA_USER}:{GRAFANA_PASS}".encode()).decode()
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json'
    }
    
    # Simplified dashboard configuration
    dashboard_config = {
        "dashboard": {
            "title": "🏍️ Motorcycle Telemetry",
            "tags": ["motorcycle", "telemetry"],
            "timezone": "browser",
            "refresh": "5s",
            "time": {
                "from": "now-1h",
                "to": "now"
            },
            "panels": [
                {
                    "id": 1,
                    "title": "🏍️ Vibration Level (Engine Detection)",
                    "type": "timeseries",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "rawSql": "SELECT time, level FROM vibration WHERE $timeFilter ORDER BY time",
                            "format": "time_series",
                            "datasource": {"uid": "${DS_INFLUXDB-MOTORCYCLE}"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "custom": {"drawStyle": "line", "lineInterpolation": "linear"},
                            "thresholds": {
                                "steps": [
                                    {"color": "red", "value": 0},
                                    {"color": "green", "value": 500}
                                ]
                            }
                        }
                    }
                },
                {
                    "id": 2,
                    "title": "⚡ G-Forces (Acceleration)",
                    "type": "timeseries", 
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "rawSql": "SELECT time, x as \"X-Axis\", y as \"Y-Axis\", z as \"Z-Axis\" FROM imu WHERE sensor = 'accelerometer' AND $timeFilter ORDER BY time",
                            "format": "time_series",
                            "datasource": {"uid": "${DS_INFLUXDB-MOTORCYCLE}"}
                        }
                    ]
                },
                {
                    "id": 3,
                    "title": "🌀 Gyroscope (Lean Angles)",
                    "type": "timeseries",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    "targets": [
                        {
                            "refId": "A",
                            "rawSql": "SELECT time, x as \"Roll\", y as \"Pitch\", z as \"Yaw\" FROM imu WHERE sensor = 'gyroscope' AND $timeFilter ORDER BY time",
                            "format": "time_series",
                            "datasource": {"uid": "${DS_INFLUXDB-MOTORCYCLE}"}
                        }
                    ]
                },
                {
                    "id": 4,
                    "title": "🔋 Power Status",
                    "type": "timeseries",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    "targets": [
                        {
                            "refId": "A",
                            "rawSql": "SELECT time, voltage, external_power FROM power WHERE $timeFilter ORDER BY time",
                            "format": "time_series",
                            "datasource": {"uid": "${DS_INFLUXDB-MOTORCYCLE}"}
                        }
                    ]
                }
            ]
        },
        "overwrite": True
    }
    
    response = requests.post(f"{GRAFANA_URL}/api/dashboards/db", 
                           json=dashboard_config, headers=headers)
    
    if response.status_code in [200, 412]:  # 412 = already exists
        result = response.json()
        dashboard_url = result.get('url', '/d/motorcycle-telemetry')
        print(f"✅ Dashboard created successfully: {GRAFANA_URL}{dashboard_url}")
        return True
    else:
        print(f"❌ Failed to create dashboard: {response.status_code} - {response.text}")
        return False

def main():
    print("🏍️ Setting up Grafana Dashboard for Motorcycle Telemetry")
    print("=" * 60)
    
    # Wait for Grafana to be ready
    if not wait_for_grafana():
        print("❌ Grafana is not responding. Please check the service.")
        sys.exit(1)
    
    # Setup data source
    if not setup_data_source():
        print("❌ Failed to setup InfluxDB data source")
        sys.exit(1)
    
    # Create dashboard
    if not create_dashboard():
        print("❌ Failed to create dashboard")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Grafana setup complete!")
    print(f"📊 Access your dashboard at: http://10.0.0.155:3000")
    print(f"🔑 Username: {GRAFANA_USER}")
    print(f"🔑 Password: {GRAFANA_PASS}")
    print("💡 You'll be prompted to change the password on first login")

if __name__ == "__main__":
    main() 