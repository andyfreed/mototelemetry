# 🗺️ GPS Map Dashboard Panels for Motorcycle

## Prerequisites
✅ GPS working and collecting coordinates  
✅ InfluxDB with GPS data  
✅ Grafana with Geomap plugin enabled  

---

## Panel 1: 📍 Current Location Map

### Panel Settings:
- **Title**: `📍 Current Location`
- **Visualization**: **Geomap**
- **Size**: 12x8 (full width)

### Query:
```sql
SELECT last("latitude") as "lat", last("longitude") as "lon" 
FROM "gps" WHERE $timeFilter AND "latitude" IS NOT NULL
```

### Map Settings:
- **Base Map**: OpenStreetMap
- **Marker Style**: 
  - Color: Red
  - Size: 10
  - Symbol: Circle
- **Auto-zoom**: Enabled
- **Show current location**: Yes

---

## Panel 2: 🛣️ Route Tracking

### Panel Settings:
- **Title**: `🛣️ Ride Route`
- **Visualization**: **Geomap**
- **Size**: 24x12 (full width, tall)

### Query:
```sql
SELECT "latitude" as "lat", "longitude" as "lon", "speed_mph", time
FROM "gps" WHERE $timeFilter AND "latitude" IS NOT NULL 
ORDER BY time ASC
```

### Map Settings:
- **Base Map**: OpenStreetMap
- **Layer Type**: Route/Path
- **Line Style**:
  - Color: Blue
  - Width: 3
  - Opacity: 0.8
- **Speed Color Coding**:
  - Green: 0-35 mph
  - Yellow: 35-55 mph
  - Red: 55+ mph

---

## Panel 3: 🚀 Speed + Location Heatmap

### Panel Settings:
- **Title**: `🚀 Speed Heatmap`
- **Visualization**: **Geomap**

### Query:
```sql
SELECT "latitude" as "lat", "longitude" as "lon", 
       "speed_mph" as "value"
FROM "gps" WHERE $timeFilter AND "latitude" IS NOT NULL
```

### Map Settings:
- **Layer Type**: Heatmap
- **Value Field**: speed_mph
- **Color Scale**: 
  - Blue: Low speed
  - Green: Medium speed  
  - Red: High speed

---

## Panel 4: 📊 GPS Status Indicators

### Sub-Panel A: GPS Fix Status
```sql
SELECT last("gps_fix") FROM "gps" WHERE $timeFilter
```
- **Type**: Stat
- **Color**: Green (fix), Red (no fix)

### Sub-Panel B: Current Speed
```sql
SELECT last("speed_mph") FROM "gps" WHERE $timeFilter
```
- **Type**: Gauge
- **Range**: 0-120 mph

### Sub-Panel C: Current Heading
```sql
SELECT last("heading") FROM "gps" WHERE $timeFilter
```
- **Type**: Compass/Gauge
- **Range**: 0-360°

---

## Panel 5: 🏁 Ride Statistics

### Query:
```sql
SELECT 
  max("speed_mph") as "Max Speed",
  avg("speed_mph") as "Avg Speed",
  count(*) as "Data Points"
FROM "gps" WHERE $timeFilter AND "speed_mph" > 0
```

### Display:
- **Type**: Stat panel
- **Show**: Max speed, average speed, distance traveled

---

## Advanced Features

### 1. 🎯 Waypoint Markers
Add custom markers for:
- Start/End points
- Gas stations
- Interesting locations
- Speed traps

### 2. 📈 Elevation Profile
If GPS includes altitude:
```sql
SELECT "latitude", "longitude", "altitude", time
FROM "gps" WHERE $timeFilter
```

### 3. 🌡️ Weather Overlay
Combine with weather data for route conditions

---

## GPS Data Export for Maps

### Export Route as GPX:
```python
# Add to data_exporter.py
def export_gpx(session_id):
    """Export ride as GPX file for GPS devices"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT latitude, longitude, timestamp, speed_mph
        FROM telemetry_data 
        WHERE session_id = ? AND latitude IS NOT NULL
        ORDER BY timestamp
    ''', (session_id,))
    
    # Generate GPX XML format
    # (Implementation details...)
```

---

## Troubleshooting GPS Maps

### No Map Data:
1. Check GPS fix: `SELECT * FROM gps WHERE gps_fix = true`
2. Verify coordinates: `SELECT latitude, longitude FROM gps LIMIT 10`
3. Check time range covers GPS data collection

### Map Not Loading:
1. Ensure Geomap plugin is installed
2. Check internet connection for map tiles
3. Verify coordinate format (decimal degrees)

### Performance Issues:
1. Limit data points: Use time-based sampling
2. Aggregate data: `GROUP BY time(1m)` for large datasets
3. Use appropriate zoom levels

---

## Expected Results

When GPS is working, you'll see:
- ✅ **Real-time location** on map
- ✅ **Complete route tracking** of your rides  
- ✅ **Speed visualization** along the route
- ✅ **GPS status indicators** (fix, speed, heading)
- ✅ **Ride statistics** (max speed, distance, etc.)

Perfect for:
- 🏍️ **Track day analysis**
- 🗺️ **Route planning**
- 📊 **Performance monitoring**
- 🛣️ **Adventure documentation** 