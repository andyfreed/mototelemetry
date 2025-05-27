#!/usr/bin/env python3
"""
Create a SIMPLE working motorcycle dashboard with manual calibration display
No complex Grafana transformations - just show corrected values directly
"""

import requests
import json

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "Emmy2016Isla2020!"

def create_working_dashboard():
    """Create simple working dashboard"""
    
    import base64
    credentials = base64.b64encode(f"{GRAFANA_USER}:{GRAFANA_PASS}".encode()).decode()
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json'
    }
    
    dashboard_config = {
        "dashboard": {
            "title": "🏍️ WORKING Motorcycle Dashboard",
            "tags": ["motorcycle", "working", "simple"],
            "timezone": "browser",
            "refresh": "2s",
            "time": {
                "from": "now-5m",
                "to": "now"
            },
            "panels": [
                {
                    "id": 1,
                    "title": "🏍️ Lean Angle (Y-axis)",
                    "type": "gauge",
                    "gridPos": {"h": 8, "w": 8, "x": 0, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT MEAN(y) FROM imu WHERE sensor = 'accelerometer' AND time > now() - 5s",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": 50},
                                    {"color": "yellow", "value": 150},
                                    {"color": "red", "value": 200}
                                ]
                            },
                            "unit": "none",
                            "min": -200,
                            "max": 200,
                            "displayName": "Raw Y"
                        }
                    },
                    "options": {
                        "reduceOptions": {
                            "values": False,
                            "calcs": ["lastNotNull"],
                            "fields": ""
                        }
                    }
                },
                {
                    "id": 2,
                    "title": "⚡ Forward G (X-axis)",
                    "type": "gauge",
                    "gridPos": {"h": 8, "w": 8, "x": 8, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT MEAN(x) FROM imu WHERE sensor = 'accelerometer' AND time > now() - 5s",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": 6000},
                                    {"color": "yellow", "value": 6300},
                                    {"color": "red", "value": 6500}
                                ]
                            },
                            "unit": "none",
                            "min": 5800,
                            "max": 6600,
                            "displayName": "Raw X"
                        }
                    },
                    "options": {
                        "reduceOptions": {
                            "values": False,
                            "calcs": ["lastNotNull"],
                            "fields": ""
                        }
                    }
                },
                {
                    "id": 3,
                    "title": "📊 Z-axis (Vertical)",
                    "type": "gauge",
                    "gridPos": {"h": 8, "w": 8, "x": 16, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT MEAN(z) FROM imu WHERE sensor = 'accelerometer' AND time > now() - 5s",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": 15200},
                                    {"color": "yellow", "value": 15600},
                                    {"color": "red", "value": 16000}
                                ]
                            },
                            "unit": "none",
                            "min": 15000,
                            "max": 16000,
                            "displayName": "Raw Z"
                        }
                    },
                    "options": {
                        "reduceOptions": {
                            "values": False,
                            "calcs": ["lastNotNull"],
                            "fields": ""
                        }
                    }
                },
                {
                    "id": 4,
                    "title": "📈 Accelerometer Raw Values",
                    "type": "timeseries",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT mean(x) as \"X-Forward\", mean(y) as \"Y-Lateral\", mean(z) as \"Z-Vertical\" FROM imu WHERE sensor = 'accelerometer' AND $timeFilter GROUP BY time(2s) fill(previous)",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "custom": {
                                "drawStyle": "line",
                                "lineWidth": 1,
                                "fillOpacity": 0
                            },
                            "unit": "none"
                        },
                        "overrides": [
                            {"matcher": {"id": "byName", "options": "X-Forward"}, "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "red"}}]},
                            {"matcher": {"id": "byName", "options": "Y-Lateral"}, "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "blue"}}]},
                            {"matcher": {"id": "byName", "options": "Z-Vertical"}, "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "green"}}]}
                        ]
                    }
                },
                {
                    "id": 5,
                    "title": "🛰️ System Status",
                    "type": "stat",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT COUNT(x) FROM imu WHERE time > now() - 10s",
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
                                    {"color": "yellow", "value": 50},
                                    {"color": "green", "value": 100}
                                ]
                            },
                            "unit": "none",
                            "displayName": "Data Points/10s"
                        }
                    },
                    "options": {
                        "reduceOptions": {
                            "values": False,
                            "calcs": ["lastNotNull"],
                            "fields": ""
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
        print("✅ Working dashboard created!")
        print(f"🔗 URL: {GRAFANA_URL}{result.get('url', '/d/working')}")
        print("\n📋 How to read the values when STATIONARY:")
        print("- Y-axis (Lean): Should be around 100 (±50)")
        print("- X-axis (Forward): Should be around 6200 (±200)")  
        print("- Z-axis (Vertical): Should be around 15400 (±200)")
        print("\n🧮 Manual G-Force calculation:")
        print("- Forward G = (X - 6200) / 16384")
        print("- Lateral G = (Y - 100) / 16384") 
        print("- Lean Angle = arcsin(Lateral G) * 57.3°")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    create_working_dashboard() 