#!/usr/bin/env python3
"""
Create a fixed real-time motorcycle dashboard
"""

import requests
import json

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "Emmy2016Isla2020!"

def create_realtime_dashboard():
    """Create real-time motorcycle dashboard with correct queries"""
    
    import base64
    credentials = base64.b64encode(f"{GRAFANA_USER}:{GRAFANA_PASS}".encode()).decode()
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json'
    }
    
    dashboard_config = {
        "dashboard": {
            "title": "🏍️ Real-Time Motorcycle Telemetry",
            "tags": ["motorcycle", "realtime"],
            "timezone": "browser",
            "refresh": "2s",
            "time": {
                "from": "now-5m",
                "to": "now"
            },
            "panels": [
                {
                    "id": 1,
                    "title": "⚡ Acceleration (G-Forces)",
                    "type": "timeseries",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT x, y, z FROM imu WHERE sensor = 'accelerometer' AND $timeFilter",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "custom": {"drawStyle": "line"},
                            "displayName": "Accel",
                            "unit": "none"
                        },
                        "overrides": [
                            {"matcher": {"id": "byName", "options": "x"}, "properties": [{"id": "displayName", "value": "X-Axis"}]},
                            {"matcher": {"id": "byName", "options": "y"}, "properties": [{"id": "displayName", "value": "Y-Axis"}]},
                            {"matcher": {"id": "byName", "options": "z"}, "properties": [{"id": "displayName", "value": "Z-Axis"}]}
                        ]
                    }
                },
                {
                    "id": 2,
                    "title": "🌀 Gyroscope (Rotation)",
                    "type": "timeseries",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT x, y, z FROM imu WHERE sensor = 'gyroscope' AND $timeFilter",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "custom": {"drawStyle": "line"},
                            "unit": "none"
                        },
                        "overrides": [
                            {"matcher": {"id": "byName", "options": "x"}, "properties": [{"id": "displayName", "value": "Roll"}]},
                            {"matcher": {"id": "byName", "options": "y"}, "properties": [{"id": "displayName", "value": "Pitch"}]},
                            {"matcher": {"id": "byName", "options": "z"}, "properties": [{"id": "displayName", "value": "Yaw"}]}
                        ]
                    }
                },
                {
                    "id": 3,
                    "title": "🔋 Power Status",
                    "type": "timeseries",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT external_power FROM power WHERE $timeFilter",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "red", "value": 0},
                                    {"color": "green", "value": 1}
                                ]
                            }
                        }
                    }
                },
                {
                    "id": 4,
                    "title": "📊 Data Rate (points/sec)",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 6, "x": 12, "y": 8},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT COUNT(x) FROM imu WHERE time > now() - 10s GROUP BY time(1s) fill(0)",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "red", "value": 0},
                                    {"color": "yellow", "value": 10},
                                    {"color": "green", "value": 20}
                                ]
                            },
                            "unit": "short"
                        }
                    }
                },
                {
                    "id": 5,
                    "title": "🌡️ Temperature",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 6, "x": 18, "y": 8},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT LAST(value) FROM temperature WHERE $timeFilter",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "blue", "value": 0},
                                    {"color": "green", "value": 20},
                                    {"color": "red", "value": 50}
                                ]
                            },
                            "unit": "celsius"
                        }
                    }
                }
            ]
        },
        "overwrite": True
    }
    
    response = requests.post(f"{GRAFANA_URL}/api/dashboards/db", 
                           json=dashboard_config, headers=headers)
    
    if response.status_code in [200, 412]:
        result = response.json()
        print("✅ Real-time dashboard created!")
        print(f"🔗 URL: {GRAFANA_URL}{result.get('url', '/d/realtime')}")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    create_realtime_dashboard() 