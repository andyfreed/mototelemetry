# 🗺️ GPS Map Dashboard Setup for Motorcycle Telemetry

## Current Status
✅ **GPS Hardware**: Connected and initialized  
✅ **GPS Daemon**: Running on `/dev/ttyACM0`  
✅ **GPS Library**: gps3 installed and working  
⏳ **GPS Fix**: Waiting for satellite lock (normal - can take 2-15 minutes)  

---

## 📍 What You'll Get Once GPS Has Fix

### **Real-Time Location Tracking**
- 🗺️ **Live map** showing your current position
- 🛣️ **Route tracking** of your complete ride
- 🚀 **Speed visualization** on the map
- 📊 **GPS status indicators**

---

## 🛠️ Setting Up GPS Map Panels in Grafana

### Step 1: Enable Geomap Plugin
1. Go to **Grafana** → **Administration** → **Plugins**
2. Search for **"Geomap"**
3. Install if not already enabled

### Step 2: Create GPS Data Source
Your InfluxDB already has GPS data structure:
```sql
-- GPS data fields in InfluxDB:
latitude, longitude, speed_mph, heading, gps_fix
```

---

## 📍 Panel 1: Current Location Map

### Create Panel:
1. **Add Panel** → **Geomap**
2. **Title**: `📍 Current Location`

### Query:
```sql
SELECT last("latitude") as "lat", last("longitude") as "lon" 
FROM "gps" WHERE $timeFilter AND "latitude" IS NOT NULL
```

### Map Configuration:
- **Base Layer**: OpenStreetMap
- **Marker**: 
  - Color: Red
  - Size: 12
  - Symbol: Circle
- **Auto Zoom**: Enabled

---

## 🛣️ Panel 2: Route Tracking

### Create Panel:
1. **Add Panel** → **Geomap**  
2. **Title**: `🛣️ Ride Route`
3. **Size**: Full width (24 units)

### Query:
```sql
SELECT "latitude" as "lat", "longitude" as "lon", "speed_mph", time
FROM "gps" WHERE $timeFilter AND "latitude" IS NOT NULL 
ORDER BY time ASC
```

### Map Configuration:
- **Layer Type**: Route/Path
- **Line Style**:
  - Color: Blue
  - Width: 4
  - Opacity: 0.8
- **Speed Color Coding**:
  - 🟢 Green: 0-35 mph (city)
  - 🟡 Yellow: 35-55 mph (highway)  
  - 🔴 Red: 55+ mph (fast)

---

## 🚀 Panel 3: Speed Heatmap

### Create Panel:
1. **Add Panel** → **Geomap**
2. **Title**: `🚀 Speed Heatmap`

### Query:
```sql
SELECT "latitude" as "lat", "longitude" as "lon", 
       "speed_mph" as "value"
FROM "gps" WHERE $timeFilter AND "latitude" IS NOT NULL
```

### Configuration:
- **Layer Type**: Heatmap
- **Value Field**: speed_mph
- **Intensity**: Based on speed
- **Color Scale**: Blue → Green → Yellow → Red

---

## 📊 Panel 4: GPS Status Dashboard

### Sub-Panel A: GPS Fix Status
```sql
SELECT last("gps_fix") FROM "gps" WHERE $timeFilter
```
- **Type**: Stat
- **Display**: 
  - ✅ Green "GPS LOCKED" when true
  - ❌ Red "NO GPS FIX" when false

### Sub-Panel B: Current Speed (GPS)
```sql
SELECT last("speed_mph") FROM "gps" WHERE $timeFilter
```
- **Type**: Gauge
- **Range**: 0-120 mph
- **Thresholds**:
  - Green: 0-35 mph
  - Yellow: 35-65 mph  
  - Red: 65+ mph

### Sub-Panel C: Current Heading
```sql
SELECT last("heading") FROM "gps" WHERE $timeFilter
```
- **Type**: Compass Gauge
- **Range**: 0-360°
- **Display**: Cardinal directions (N, S, E, W)

---

## 🏁 Panel 5: Ride Statistics

### Query:
```sql
SELECT 
  max("speed_mph") as "Max Speed",
  avg("speed_mph") as "Avg Speed",
  count(*) as "GPS Points"
FROM "gps" WHERE $timeFilter AND "speed_mph" > 0
```

### Display:
- **Type**: Stat Panel
- **Show**: 
  - 🏎️ Max Speed
  - ⚡ Average Speed  
  - 📍 GPS Data Points

---

## 🔧 Testing GPS Data Collection

### Check GPS Status:
```bash
# Check if GPS is getting data
python3 -c "
import sqlite3
conn = sqlite3.connect('motorcycle_data/telemetry.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM telemetry_data WHERE latitude IS NOT NULL')
gps_count = cursor.fetchone()[0]
print(f'GPS records with coordinates: {gps_count}')

if gps_count > 0:
    cursor.execute('SELECT latitude, longitude, speed_mph, timestamp FROM telemetry_data WHERE latitude IS NOT NULL ORDER BY timestamp DESC LIMIT 3')
    recent = cursor.fetchall()
    print('Recent GPS data:')
    for row in recent:
        print(f'  Lat: {row[0]:.6f}, Lon: {row[1]:.6f}, Speed: {row[2]} mph, Time: {row[3]}')
else:
    print('No GPS coordinates yet - GPS may need more time to get satellite fix')
conn.close()
"
```

### Force GPS Fix (if outdoors):
```bash
# Check GPS daemon status
sudo systemctl status gpsd

# Check raw GPS data
sudo cat /dev/ttyACM0 | head -10
```

---

## 🌍 Advanced GPS Features

### 1. **GPX Export** for GPS Devices
Export your rides as GPX files:
```python
def export_ride_gpx(session_id):
    """Export ride as GPX file"""
    # Query GPS data for session
    # Generate GPX XML format
    # Save to file for GPS device import
```

### 2. **Geofencing** 
Set up alerts for:
- Home/work locations
- Speed zones
- Favorite riding areas

### 3. **Route Analysis**
- Cornering analysis (GPS + lean angle)
- Speed vs location correlation
- Elevation profiles (if GPS has altitude)

---

## 🚨 Troubleshooting GPS

### No GPS Data:
1. **Check GPS Fix**: GPS needs clear sky view
2. **Wait Time**: Initial fix can take 2-15 minutes
3. **Check Daemon**: `sudo systemctl status gpsd`
4. **Check Device**: `ls -la /dev/ttyACM*`

### Map Not Loading:
1. **Internet**: Maps need internet for tiles
2. **Plugin**: Ensure Geomap plugin installed
3. **Data Format**: Verify lat/lon are decimal degrees

### Performance:
1. **Limit Data**: Use time windows for large datasets
2. **Sampling**: Aggregate GPS points for better performance
3. **Zoom**: Appropriate zoom levels for data density

---

## 🎯 Expected Results

Once GPS gets satellite fix, you'll see:

### **Real-Time Dashboard**:
- 📍 **Current position** on live map
- 🛣️ **Route tracking** as you ride
- 🚀 **Speed visualization** with color coding
- 📊 **GPS status** (fix, speed, heading)

### **Post-Ride Analysis**:
- 🗺️ **Complete route map** of your ride
- 📈 **Speed analysis** along the route
- 🏁 **Ride statistics** (max speed, distance, time)
- 📱 **GPX export** for other GPS devices

Perfect for:
- 🏍️ **Track day analysis**
- 🗺️ **Adventure touring**
- 📊 **Performance monitoring**  
- 🛣️ **Route documentation**

---

## ⏳ Next Steps

1. **Wait for GPS Fix** (2-15 minutes outdoors)
2. **Test with short ride** to verify data collection
3. **Create map panels** in Grafana using queries above
4. **Customize** colors, thresholds, and layouts
5. **Export/share** your favorite routes!

Your GPS is ready - just needs satellite lock! 🛰️ 