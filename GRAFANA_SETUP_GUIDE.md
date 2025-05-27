# 🏍️ Motorcycle Telemetry Grafana Setup Guide

## Pi 5 System Status
- **Pi IP Address**: `10.0.0.155` (WiFi), `192.168.225.27` (USB)
- **Grafana URL**: http://10.0.0.155:3000
- **InfluxDB URL**: http://localhost:8086
- **Database**: `motorcycle_telemetry`
- **Data Points Available**: 158,347 telemetry readings

## Step 1: Access Grafana

1. Open your web browser and go to: **http://10.0.0.155:3000**
2. If prompted for login credentials, try:
   - Username: `admin`
   - Password: `admin`
   - (You may be prompted to change the password on first login)

## Step 2: Add InfluxDB Data Source

1. Click the **⚙️ Configuration** (gear icon) in the left sidebar
2. Select **Data Sources**
3. Click **Add data source**
4. Select **InfluxDB**
5. Configure the data source with these settings:

   ```
   Name: InfluxDB-Motorcycle
   URL: http://localhost:8086
   Access: Server (default)
   Database: motorcycle_telemetry
   HTTP Method: GET
   ```

6. Click **Save & Test** to verify the connection

## Step 3: Import Dashboard

### Option A: Import JSON File (Recommended)

1. Click the **+** (plus icon) in the left sidebar
2. Select **Import**
3. Click **Upload JSON file**
4. Select the file: `motorcycle_dashboard_enhanced.json` (for rider-focused gauges) or `motorcycle_dashboard_influx.json` (basic version)
5. Configure the import:
   - **Name**: 🏍️ Motorcycle Telemetry
   - **Folder**: General (or create a new folder)
   - **UID**: motorcycle-telemetry
   - **Data source**: Select "InfluxDB-Motorcycle"
6. Click **Import**

### Option B: Manual Panel Creation

If the JSON import doesn't work, create panels manually:

#### Panel 1: Engine Vibration Level
- **Type**: Time series
- **Query**: `SELECT mean("level") FROM "vibration" WHERE $timeFilter GROUP BY time($__interval) fill(null)`
- **Alias**: Engine Vibration

#### Panel 2: G-Forces (Acceleration)
- **Type**: Time series  
- **Query**: `SELECT mean("x"), mean("y"), mean("z") FROM "imu" WHERE "sensor" = 'accelerometer' AND $timeFilter GROUP BY time($__interval) fill(null)`
- **Aliases**: X-Axis, Y-Axis, Z-Axis

#### Panel 3: Gyroscope (Lean Angles)
- **Type**: Time series
- **Query**: `SELECT mean("x"), mean("y"), mean("z") FROM "imu" WHERE "sensor" = 'gyroscope' AND $timeFilter GROUP BY time($__interval) fill(null)`
- **Aliases**: Roll, Pitch, Yaw

#### Panel 4: Engine Status Gauge
- **Type**: Gauge
- **Query**: `SELECT last("level") FROM "vibration" WHERE $timeFilter`
- **Thresholds**: Red (0), Green (500+)

## Step 4: Configure Dashboard Settings

1. Click the **⚙️ Settings** icon in the top right of the dashboard
2. Configure:
   - **Auto-refresh**: 5 seconds
   - **Time range**: Last 1 hour (or adjust as needed)
   - **Timezone**: Browser or your local timezone

## Step 5: Verify Data

Your dashboard should now show:
- ✅ **Live telemetry data** updating every 5 seconds
- ✅ **Engine vibration levels** with threshold indicators
- ✅ **3-axis acceleration data** (G-forces)
- ✅ **Gyroscope data** (lean angles)
- ✅ **Engine status gauge** (Red = off, Green = running)

## Data Overview

**Current Sessions in Database**:
- `20250527_014833`: 133,475 points (active session)
- `20250527_013124`: 1,860 points
- `20250527_005737`: 10,320 points
- `20250527_004402`: 4,544 points
- `20250527_004355`: 4,656 points
- `20250527_001006`: 3,344 points
- `20250526_233743`: 148 points

## Troubleshooting

### No Data Showing
1. Check data source connection: **Configuration → Data Sources → InfluxDB-Motorcycle → Save & Test**
2. Verify database name: `motorcycle_telemetry`
3. Check time range - ensure it covers periods when telemetry was running

### Authentication Issues
- If admin/admin doesn't work, check Grafana logs: `sudo journalctl -u grafana-server -f`
- Reset admin password: `sudo grafana-cli admin reset-admin-password admin`

### Performance Issues
- Reduce auto-refresh rate if needed (5s → 10s → 30s)
- Limit time range for large datasets
- Use aggregation functions (mean, max) for better performance

## Next Steps

1. **Real-time Data**: The telemetry system is running and collecting data continuously
2. **New Rides**: Every time the engine starts (vibration > 500), a new session begins
3. **Data Export**: Run `python3 data_exporter.py sync-all` to sync new sessions to InfluxDB
4. **Dashboard Customization**: Add more panels, alerts, or customize visualizations as needed

## Live Motorcycle Installation

When ready to install on the motorcycle:
1. The telemetry system will auto-start on boot
2. Engine detection works via vibration threshold
3. Data syncs to InfluxDB when connected to home WiFi
4. Dashboard provides real-time monitoring during rides (if connected to mobile hotspot)

---

**System Status**: ✅ Grafana + InfluxDB ready on Pi 5  
**Dashboard Files**: `motorcycle_dashboard_enhanced.json` (rider-focused), `motorcycle_dashboard_influx.json` (basic), `grafana_datasource.json`  
**Access URL**: http://10.0.0.155:3000 