#!/usr/bin/env python3
"""
Create a fixed motorcycle dashboard with corrected InfluxDB queries
"""

import requests
import json

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "Emmy2016Isla2020!"

def create_fixed_motorcycle_dashboard():
    """Create fixed motorcycle dashboard with working queries"""
    
    import base64
    credentials = base64.b64encode(f"{GRAFANA_USER}:{GRAFANA_PASS}".encode()).decode()
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json'
    }
    
    dashboard_config = {
        "dashboard": {
            "title": "🏍️ Motorcycle Performance Dashboard (Working)",
            "tags": ["motorcycle", "performance", "lean", "gforce", "gps"],
            "timezone": "browser",
            "refresh": "2s",
            "time": {
                "from": "now-5m",
                "to": "now"
            },
            "panels": [
                {
                    "id": 1,
                    "title": "🏍️ Lean Angle (Smoothed)",
                    "type": "gauge",
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT MEAN(y) FROM imu WHERE sensor = 'accelerometer' AND time > now() - 5s",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "transformations": [
                        {
                            "id": "calculateField",
                            "options": {
                                "alias": "lean_angle",
                                "mode": "binary",
                                "binary": {
                                    "left": "mean",
                                    "operation": "-",
                                    "right": "100"
                                }
                            }
                        },
                        {
                            "id": "calculateField",
                            "options": {
                                "alias": "lean_degrees",
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
                                "alias": "lean_final",
                                "mode": "binary",
                                "binary": {
                                    "left": "lean_degrees",
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
                                    {"color": "green", "value": -25},
                                    {"color": "yellow", "value": -40},
                                    {"color": "red", "value": -50},
                                    {"color": "red", "value": 50},
                                    {"color": "yellow", "value": 40},
                                    {"color": "green", "value": 25}
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
                                "alias": "forward_g_raw",
                                "mode": "binary",
                                "binary": {
                                    "left": "mean",
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
                                    "left": "forward_g_raw",
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
                                "alias": "lateral_g_raw",
                                "mode": "binary",
                                "binary": {
                                    "left": "mean",
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
                                    "left": "lateral_g_raw",
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
                    "title": "🚀 Speed (GPS)",
                    "type": "stat",
                    "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT latitude, longitude FROM gps WHERE latitude != 0 AND longitude != 0 ORDER BY time DESC LIMIT 1",
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
                                {"options": {"0": {"text": "❌ NO GPS FIX"}}, "type": "value"},
                                {"options": {"from": 0.1, "to": 999}, "result": {"text": "🛰️ GPS READY"}, "type": "range"}
                            ],
                            "unit": "none",
                            "displayName": "GPS Status",
                            "noValue": "❌ NO GPS FIX"
                        }
                    }
                },
                {
                    "id": 5,
                    "title": "🗺️ GPS Location",
                    "type": "geomap",
                    "gridPos": {"h": 10, "w": 12, "x": 0, "y": 8},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT latitude, longitude FROM gps WHERE latitude != 0 AND longitude != 0 AND time > now() - 1h ORDER BY time DESC LIMIT 100",
                            "rawQuery": True,
                            "datasource": {"type": "influxdb"}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "custom": {
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "vis": False
                                }
                            }
                        }
                    },
                    "options": {
                        "view": {
                            "id": "coords",
                            "lat": 0,
                            "lon": 0,
                            "zoom": 15
                        },
                        "controls": {
                            "showZoom": True,
                            "mouseWheelZoom": True,
                            "showAttribution": True,
                            "showScale": False,
                            "showMeasure": False,
                            "showDebug": False
                        },
                        "basemap": {
                            "type": "default",
                            "name": "OpenStreetMap"
                        },
                        "layers": [
                            {
                                "type": "markers",
                                "name": "Current Position",
                                "config": {
                                    "style": {
                                        "color": {
                                            "mode": "fixed",
                                            "fixedColor": "red"
                                        },
                                        "size": {
                                            "mode": "fixed",
                                            "fixedSize": 8
                                        },
                                        "symbol": {
                                            "mode": "fixed",
                                            "fixedSymbol": "circle"
                                        }
                                    }
                                }
                            }
                        ]
                    }
                },
                {
                    "id": 6,
                    "title": "📈 Performance History",
                    "type": "timeseries",
                    "gridPos": {"h": 10, "w": 12, "x": 12, "y": 8},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT mean(x) as \"Forward\", mean(y) as \"Lateral\" FROM imu WHERE sensor = 'accelerometer' AND $timeFilter GROUP BY time(2s) fill(previous)",
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
                            {"matcher": {"id": "byName", "options": "Forward"}, "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "red"}}]},
                            {"matcher": {"id": "byName", "options": "Lateral"}, "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "blue"}}]}
                        ]
                    }
                },
                {
                    "id": 7,
                    "title": "📊 Data Rate",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 4, "x": 0, "y": 18},
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
                    "title": "🌡️ System Temp",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 4, "x": 4, "y": 18},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT LAST(temperature) FROM power WHERE time > now() - 30s",
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
                                    {"color": "green", "value": 30},
                                    {"color": "yellow", "value": 50},
                                    {"color": "red", "value": 70}
                                ]
                            },
                            "unit": "celsius",
                            "displayName": "Temp",
                            "noValue": "No Data"
                        }
                    }
                },
                {
                    "id": 9,
                    "title": "📍 GPS Status",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 4, "x": 8, "y": 18},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT COUNT(*) FROM gps WHERE latitude != 0 AND longitude != 0 AND time > now() - 30s",
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
                                {"options": {"0": {"text": "❌ NO FIX"}}, "type": "value"},
                                {"options": {"from": 1, "to": 999}, "result": {"text": "✅ GPS OK"}, "type": "range"}
                            ],
                            "unit": "none",
                            "displayName": "GPS"
                        }
                    }
                },
                {
                    "id": 10,
                    "title": "🔄 Session Stats",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 12, "x": 12, "y": 18},
                    "targets": [
                        {
                            "refId": "A",
                            "query": "SELECT COUNT(*) FROM imu WHERE sensor = 'accelerometer' AND time > now() - 1h",
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
                                    {"color": "yellow", "value": 1000},
                                    {"color": "red", "value": 10000}
                                ]
                            },
                            "unit": "none",
                            "displayName": "Data Points (1h)"
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
        print("✅ Working motorcycle dashboard created!")
        print(f"🔗 URL: {GRAFANA_URL}{result.get('url', '/d/motorcycle-working')}")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    create_fixed_motorcycle_dashboard() 