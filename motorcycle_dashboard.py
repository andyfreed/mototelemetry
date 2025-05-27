#!/usr/bin/env python3
"""
Create a motorcycle-specific dashboard with lean angles and G-force meters
"""

import requests
import json

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "Emmy2016Isla2020!"

def create_motorcycle_dashboard():
    """Create motorcycle-specific dashboard with lean angles and performance metrics"""
    
    import base64
    credentials = base64.b64encode(f"{GRAFANA_USER}:{GRAFANA_PASS}".encode()).decode()
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json'
    }
    
    dashboard_config = {
        "dashboard": {
            "title": "🏍️ Motorcycle Performance Dashboard",
            "tags": ["motorcycle", "performance", "lean", "gforce"],
            "timezone": "browser",
            "refresh": "1s",
            "time": {
                "from": "now-3m",
                "to": "now"
            },
            "panels": [
                {
                    "id": 1,
                    "title": "🏍️ Lean Angle (Live)",
                    "type": "gauge",
                    "gridPos": {"h": 9, "w": 8, "x": 0, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT ATAN2((LAST(y) - 100) / 16384.0, (LAST(z) - 15400) / 16384.0) * 180 / 3.14159 as lean_angle FROM imu WHERE sensor = 'accelerometer' AND time > now() - 10s",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "mappings": [],
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": -20},
                                    {"color": "yellow", "value": -35},
                                    {"color": "red", "value": -45},
                                    {"color": "red", "value": 45},
                                    {"color": "yellow", "value": 35},
                                    {"color": "green", "value": 20}
                                ]
                            },
                            "unit": "degree",
                            "min": -60,
                            "max": 60,
                            "displayName": "Lean°"
                        }
                    },
                    "options": {
                        "orientation": "auto",
                        "reduceOptions": {
                            "values": False,
                            "calcs": ["lastNotNull"],
                            "fields": ""
                        },
                        "showThresholdLabels": True,
                        "showThresholdMarkers": True
                    }
                },
                {
                    "id": 2,
                    "title": "⚡ Forward G-Force (Accel/Brake)",
                    "type": "gauge",
                    "gridPos": {"h": 9, "w": 8, "x": 8, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT (LAST(x) - 6200) / 16384.0 as forward_g FROM imu WHERE sensor = 'accelerometer' AND time > now() - 5s",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "red", "value": -1.5},
                                    {"color": "yellow", "value": -0.8},
                                    {"color": "green", "value": -0.2},
                                    {"color": "green", "value": 0.2},
                                    {"color": "yellow", "value": 0.8},
                                    {"color": "red", "value": 1.2}
                                ]
                            },
                            "unit": "none",
                            "min": -2,
                            "max": 2,
                            "displayName": "G-Force",
                            "custom": {
                                "neutral": 0
                            }
                        }
                    },
                    "options": {
                        "orientation": "auto",
                        "reduceOptions": {
                            "values": False,
                            "calcs": ["lastNotNull"]
                        },
                        "showThresholdLabels": True,
                        "showThresholdMarkers": True
                    }
                },
                {
                    "id": 3,
                    "title": "🌀 Lateral G-Force (Cornering)",
                    "type": "gauge",
                    "gridPos": {"h": 9, "w": 8, "x": 16, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT (LAST(y) - 100) / 16384.0 as lateral_g FROM imu WHERE sensor = 'accelerometer' AND time > now() - 5s",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": -0.5},
                                    {"color": "yellow", "value": -0.8},
                                    {"color": "red", "value": -1.2},
                                    {"color": "red", "value": 1.2},
                                    {"color": "yellow", "value": 0.8},
                                    {"color": "green", "value": 0.5}
                                ]
                            },
                            "unit": "none",
                            "min": -1.5,
                            "max": 1.5,
                            "displayName": "Lateral G",
                            "custom": {
                                "neutral": 0
                            }
                        }
                    }
                },
                {
                    "id": 4,
                    "title": "📈 Lean Angle History",
                    "type": "timeseries",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 9},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT ATAN2(mean(y - 100) / 16384.0, mean(z - 15400) / 16384.0) * 180 / 3.14159 as lean FROM imu WHERE sensor = 'accelerometer' AND $timeFilter GROUP BY time(1s) fill(previous)",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "custom": {
                                "drawStyle": "line",
                                "lineInterpolation": "smooth",
                                "lineWidth": 2,
                                "fillOpacity": 20,
                                "spanNulls": False
                            },
                            "displayName": "Lean Angle",
                            "unit": "degree",
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": -30},
                                    {"color": "yellow", "value": -45},
                                    {"color": "red", "value": -55}
                                ]
                            }
                        }
                    },
                    "options": {
                        "tooltip": {"mode": "single"},
                        "legend": {"displayMode": "visible"}
                    }
                },
                {
                    "id": 5,
                    "title": "🚀 G-Force Vector",
                    "type": "timeseries",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 9},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT mean(x - 6200)/16384 as \"Forward\", mean(y - 100)/16384 as \"Lateral\", mean(z - 15400)/16384 as \"Vertical\" FROM imu WHERE sensor = 'accelerometer' AND $timeFilter GROUP BY time(1s) fill(previous)",
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
                            "unit": "none",
                            "displayName": "G-Force"
                        },
                        "overrides": [
                            {"matcher": {"id": "byName", "options": "Forward"}, "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "red"}}]},
                            {"matcher": {"id": "byName", "options": "Lateral"}, "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "blue"}}]},
                            {"matcher": {"id": "byName", "options": "Vertical"}, "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "green"}}]}
                        ]
                    }
                },
                {
                    "id": 6,
                    "title": "🏍️ Engine Status",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 6, "x": 0, "y": 17},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT LAST(external_power) FROM power WHERE time > now() - 10s",
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
                            },
                            "mappings": [
                                {"options": {"0": {"text": "🔴 OFF"}}, "type": "value"},
                                {"options": {"1": {"text": "🟢 RUNNING"}}, "type": "value"}
                            ],
                            "unit": "none",
                            "displayName": "Engine"
                        }
                    }
                },
                {
                    "id": 7,
                    "title": "📊 Data Rate",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 6, "x": 6, "y": 17},
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
                            "displayName": "Points/10s"
                        }
                    }
                },
                {
                    "id": 8,
                    "title": "🌡️ IMU Temp",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 6, "x": 12, "y": 17},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT LAST(value) FROM temperature WHERE time > now() - 30s",
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
                                    {"color": "yellow", "value": 40},
                                    {"color": "red", "value": 60}
                                ]
                            },
                            "unit": "celsius",
                            "displayName": "Temp"
                        }
                    }
                },
                {
                    "id": 9,
                    "title": "🔄 Max Lean This Session",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 6, "x": 18, "y": 17},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT MAX(ABS(ATAN2((y - 100) / 16384.0, (z - 15400) / 16384.0) * 180 / 3.14159)) as max_lean FROM imu WHERE sensor = 'accelerometer' AND time > now() - 1h",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": 0},
                                    {"color": "yellow", "value": 30},
                                    {"color": "orange", "value": 45},
                                    {"color": "red", "value": 55}
                                ]
                            },
                            "unit": "degree",
                            "displayName": "Max Lean°"
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
        print("✅ Motorcycle dashboard created!")
        print(f"🔗 URL: {GRAFANA_URL}{result.get('url', '/d/motorcycle')}")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    create_motorcycle_dashboard() 