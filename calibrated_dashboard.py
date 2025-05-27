#!/usr/bin/env python3
"""
Create motorcycle dashboard with PROPER calibration conversion
Raw accelerometer values need to be converted to G-forces using:
- X-axis offset: 6200, scale: 16384 LSB/g  
- Y-axis offset: 100, scale: 16384 LSB/g
- Z-axis offset: 15400, scale: 16384 LSB/g
"""

import requests
import json

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "Emmy2016Isla2020!"

def create_calibrated_dashboard():
    """Create properly calibrated motorcycle dashboard"""
    
    import base64
    credentials = base64.b64encode(f"{GRAFANA_USER}:{GRAFANA_PASS}".encode()).decode()
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json'
    }
    
    dashboard_config = {
        "dashboard": {
            "title": "🏍️ CALIBRATED Motorcycle Dashboard",
            "tags": ["motorcycle", "calibrated", "gforce"],
            "timezone": "browser",
            "refresh": "2s",
            "time": {
                "from": "now-5m",
                "to": "now"
            },
            "panels": [
                {
                    "id": 1,
                    "title": "🏍️ Lean Angle",
                    "type": "gauge",
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT MEAN(y) FROM imu WHERE sensor = 'accelerometer' AND time > now() - 3s",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "transformations": [
                        {
                            "id": "calculateField",
                            "options": {
                                "mode": "reduceRow",
                                "reduce": {
                                    "reducer": "lastNotNull"
                                },
                                "replaceFields": True
                            }
                        },
                        {
                            "id": "calculateField",
                            "options": {
                                "alias": "lean_angle",
                                "mode": "binary",
                                "binary": {
                                    "left": "Last *",
                                    "operation": "-",
                                    "right": "100"
                                }
                            }
                        },
                        {
                            "id": "calculateField",
                            "options": {
                                "alias": "lean_g",
                                "mode": "binary",
                                "binary": {
                                    "left": "lean_angle",
                                    "operation": "/",
                                    "right": "16384"
                                }
                            }
                        },
                        {
                            "id": "calculateField",
                            "options": {
                                "alias": "lean_degrees",
                                "mode": "binary",
                                "binary": {
                                    "left": "lean_g",
                                    "operation": "*",
                                    "right": "57.3"
                                }
                            }
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": -20},
                                    {"color": "yellow", "value": -35},
                                    {"color": "red", "value": -50},
                                    {"color": "red", "value": 50},
                                    {"color": "yellow", "value": 35},
                                    {"color": "green", "value": 20}
                                ]
                            },
                            "unit": "degree",
                            "min": -60,
                            "max": 60,
                            "displayName": "Lean°"
                        }
                    }
                },
                {
                    "id": 2,
                    "title": "⚡ Forward G-Force",
                    "type": "gauge",
                    "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT MEAN(x) FROM imu WHERE sensor = 'accelerometer' AND time > now() - 3s",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "transformations": [
                        {
                            "id": "calculateField",
                            "options": {
                                "mode": "reduceRow",
                                "reduce": {
                                    "reducer": "lastNotNull"
                                },
                                "replaceFields": True
                            }
                        },
                        {
                            "id": "calculateField",
                            "options": {
                                "alias": "forward_raw",
                                "mode": "binary",
                                "binary": {
                                    "left": "Last *",
                                    "operation": "-",
                                    "right": "6200"
                                }
                            }
                        },
                        {
                            "id": "calculateField",
                            "options": {
                                "alias": "forward_g",
                                "mode": "binary",
                                "binary": {
                                    "left": "forward_raw",
                                    "operation": "/",
                                    "right": "16384"
                                }
                            }
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "red", "value": -1.0},
                                    {"color": "yellow", "value": -0.5},
                                    {"color": "green", "value": -0.1},
                                    {"color": "green", "value": 0.1},
                                    {"color": "yellow", "value": 0.5},
                                    {"color": "red", "value": 1.0}
                                ]
                            },
                            "unit": "none",
                            "min": -1.5,
                            "max": 1.5,
                            "displayName": "Forward G"
                        }
                    }
                },
                {
                    "id": 3,
                    "title": "🌀 Lateral G-Force",
                    "type": "gauge",
                    "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT MEAN(y) FROM imu WHERE sensor = 'accelerometer' AND time > now() - 3s",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "transformations": [
                        {
                            "id": "calculateField",
                            "options": {
                                "mode": "reduceRow",
                                "reduce": {
                                    "reducer": "lastNotNull"
                                },
                                "replaceFields": True
                            }
                        },
                        {
                            "id": "calculateField",
                            "options": {
                                "alias": "lateral_raw",
                                "mode": "binary",
                                "binary": {
                                    "left": "Last *",
                                    "operation": "-",
                                    "right": "100"
                                }
                            }
                        },
                        {
                            "id": "calculateField",
                            "options": {
                                "alias": "lateral_g",
                                "mode": "binary",
                                "binary": {
                                    "left": "lateral_raw",
                                    "operation": "/",
                                    "right": "16384"
                                }
                            }
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": -0.3},
                                    {"color": "yellow", "value": -0.6},
                                    {"color": "red", "value": -1.0},
                                    {"color": "red", "value": 1.0},
                                    {"color": "yellow", "value": 0.6},
                                    {"color": "green", "value": 0.3}
                                ]
                            },
                            "unit": "none",
                            "min": -1.2,
                            "max": 1.2,
                            "displayName": "Lateral G"
                        }
                    }
                },
                {
                    "id": 4,
                    "title": "📊 Raw Values (Debug)",
                    "type": "stat",
                    "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT MEAN(x) as \"X\", MEAN(y) as \"Y\", MEAN(z) as \"Z\" FROM imu WHERE sensor = 'accelerometer' AND time > now() - 3s",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "unit": "none",
                            "displayName": "Raw"
                        }
                    }
                },
                {
                    "id": 5,
                    "title": "📈 Calibrated G-Forces Over Time",
                    "type": "timeseries",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT mean(x) as \"X_raw\", mean(y) as \"Y_raw\", mean(z) as \"Z_raw\" FROM imu WHERE sensor = 'accelerometer' AND $timeFilter GROUP BY time(2s) fill(previous)",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "transformations": [
                        {
                            "id": "calculateField",
                            "options": {
                                "alias": "Forward_G",
                                "mode": "binary",
                                "binary": {
                                    "left": "X_raw",
                                    "operation": "-",
                                    "right": "6200"
                                }
                            }
                        },
                        {
                            "id": "calculateField",
                            "options": {
                                "alias": "Forward_G_Final",
                                "mode": "binary",
                                "binary": {
                                    "left": "Forward_G",
                                    "operation": "/",
                                    "right": "16384"
                                }
                            }
                        },
                        {
                            "id": "calculateField",
                            "options": {
                                "alias": "Lateral_G",
                                "mode": "binary",
                                "binary": {
                                    "left": "Y_raw",
                                    "operation": "-",
                                    "right": "100"
                                }
                            }
                        },
                        {
                            "id": "calculateField",
                            "options": {
                                "alias": "Lateral_G_Final",
                                "mode": "binary",
                                "binary": {
                                    "left": "Lateral_G",
                                    "operation": "/",
                                    "right": "16384"
                                }
                            }
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "custom": {
                                "drawStyle": "line",
                                "lineWidth": 2,
                                "fillOpacity": 0
                            },
                            "unit": "none"
                        },
                        "overrides": [
                            {"matcher": {"id": "byName", "options": "Forward_G_Final"}, "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "red"}}]},
                            {"matcher": {"id": "byName", "options": "Lateral_G_Final"}, "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "blue"}}]}
                        ]
                    }
                },
                {
                    "id": 6,
                    "title": "🛰️ GPS & System Status",
                    "type": "stat",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT COUNT(x) as \"Data_Rate_10s\" FROM imu WHERE time > now() - 10s",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        },
                        {
                            "refId": "B", 
                            "query": "SELECT COUNT(*) as \"GPS_Points\" FROM gps WHERE latitude != 0 AND longitude != 0 AND time > now() - 30s",
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
                            "unit": "none"
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
        print("✅ Calibrated dashboard created!")
        print(f"🔗 URL: {GRAFANA_URL}{result.get('url', '/d/calibrated')}")
        print("\nThis dashboard properly converts:")
        print("- Raw X (~6200) → Forward G-Force (should be ~0g when stationary)")
        print("- Raw Y (~100) → Lateral G-Force & Lean Angle (should be ~0° when stationary)")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    create_calibrated_dashboard() 