# 🏍️ Manual Grafana Dashboard Setup Guide

Since JSON imports aren't working, here's how to manually create your motorcycle dashboard panels:

## Prerequisites
1. ✅ Grafana running at http://10.0.0.155:3000
2. ✅ InfluxDB data source configured as "InfluxDB-Motorcycle"
3. ✅ Telemetry data exported to InfluxDB (158,347+ data points)

---

## Step 1: Create New Dashboard

1. Go to http://10.0.0.155:3000
2. Click **"+"** in left sidebar → **Dashboard**
3. Click **"Add visualization"**

---

## Step 2: Create Lean Angle Gauge

### Panel Settings:
- **Panel Title**: `🏍️ Lean Angle (Left ← → Right)`
- **Visualization**: **Gauge**

### Query:
```sql
SELECT last("x") FROM "imu" WHERE "sensor" = 'gyroscope' AND $timeFilter
```

### Field Settings:
- **Min**: -45
- **Max**: 45  
- **Unit**: degree (°)
- **Thresholds**:
  - Green: Base (0)
  - Yellow: 30
  - Orange: 40
  - Red: 45

### Transform (Optional):
Add transformation to convert gyroscope data to degrees:
- **Transform**: Calculate field
- **Mode**: Binary operation
- **Operation**: Multiply by `0.017453` (converts to degrees)

**Save Panel**

---

## Step 3: Create Speed Gauge

### Panel Settings:
- **Panel Title**: `🚀 Speed (MPH)`
- **Visualization**: **Gauge**

### Query:
```sql
SELECT last("speed_mph") FROM "gps" WHERE $timeFilter
```

### Field Settings:
- **Min**: 0
- **Max**: 120
- **Unit**: mph
- **Thresholds**:
  - Green: Base (0)
  - Yellow: 35
  - Orange: 55
  - Red: 80

**Save Panel**

---

## Step 4: Create G-Force Gauge

### Panel Settings:
- **Panel Title**: `⚡ G-Force (Forward/Backward)`
- **Visualization**: **Gauge**

### Query:
```sql
SELECT last("x")/9806.65 FROM "imu" WHERE "sensor" = 'accelerometer' AND $timeFilter
```

### Field Settings:
- **Min**: -3
- **Max**: 3
- **Unit**: accG
- **Thresholds**:
  - Green: Base (0)
  - Yellow: 1.5
  - Red: 2.5

**Save Panel**

---

## Step 5: Create Engine Status Gauge

### Panel Settings:
- **Panel Title**: `🏍️ Engine Status (Vibration)`
- **Visualization**: **Gauge**

### Query:
```sql
SELECT last("level") FROM "vibration" WHERE $timeFilter
```

### Field Settings:
- **Min**: 0
- **Max**: 2000
- **Thresholds**:
  - Red: Base (0) - Engine Off
  - Green: 500 - Engine Running

**Save Panel**

---

## Step 6: Create Speed History Chart

### Panel Settings:
- **Panel Title**: `📊 Speed History`
- **Visualization**: **Time series**

### Query:
```sql
SELECT mean("speed_mph") FROM "gps" WHERE $timeFilter GROUP BY time($__interval) fill(null)
```

### Field Settings:
- **Unit**: mph

**Save Panel**

---

## Step 7: Create Lean Angle History

### Panel Settings:
- **Panel Title**: `🏍️ Lean Angle History`
- **Visualization**: **Time series**

### Queries:
**Query A (Roll/Lean):**
```sql
SELECT mean("x") FROM "imu" WHERE "sensor" = 'gyroscope' AND $timeFilter GROUP BY time($__interval) fill(null)
```
**Alias**: `Roll (Lean)`

**Query B (Pitch):**
```sql
SELECT mean("y") FROM "imu" WHERE "sensor" = 'gyroscope' AND $timeFilter GROUP BY time($__interval) fill(null)
```
**Alias**: `Pitch (Wheelie/Endo)`

### Field Settings:
- **Unit**: degree (°)

**Save Panel**

---

## Step 8: Dashboard Settings

### Configure Dashboard:
1. Click **Dashboard Settings** (gear icon)
2. **General**:
   - **Name**: `🏍️ Motorcycle Telemetry`
   - **Tags**: `motorcycle`, `telemetry`
3. **Time Options**:
   - **Refresh**: `2s` or `5s`
   - **Time Range**: `Last 30 minutes`
4. **Save Dashboard**

---

## Step 9: Panel Layout

Arrange panels in this layout:
```
┌─────────────────┬─────────────────┬─────────────────┐
│   Lean Angle    │     Speed       │    G-Force      │
│     Gauge       │     Gauge       │     Gauge       │
└─────────────────┼─────────────────┴─────────────────┤
│ Engine Status   │        Speed History              │
│     Gauge       │       Time Series                 │
├─────────────────┴───────────────────────────────────┤
│            Lean Angle History                       │
│               Time Series                           │
└─────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### No Data Showing:
1. **Check Data Source**: Go to Configuration → Data Sources → Test connection
2. **Verify Database**: Database name should be `motorcycle_telemetry`
3. **Check Time Range**: Ensure time range covers when telemetry was active
4. **Test Query**: Use Grafana's Query Inspector to test individual queries

### Query Examples for Testing:
```sql
-- Test if data exists
SHOW MEASUREMENTS

-- Check vibration data
SELECT * FROM "vibration" ORDER BY time DESC LIMIT 10

-- Check IMU data  
SELECT * FROM "imu" WHERE "sensor" = 'gyroscope' ORDER BY time DESC LIMIT 10

-- Check GPS data
SELECT * FROM "gps" ORDER BY time DESC LIMIT 10
```

### Data Source Connection:
- **URL**: `http://localhost:8086`
- **Database**: `motorcycle_telemetry`
- **HTTP Method**: `GET`

---

## Quick Panel Creation Tips

1. **Start Simple**: Create basic time series first, then convert to gauges
2. **Test Queries**: Use Grafana's query editor to verify data
3. **Copy Panels**: Duplicate working panels and modify queries
4. **Use Templates**: Save time by copying configurations between similar panels

---

## Expected Results

When working correctly, you should see:
- ✅ **Lean Angle**: Real-time left/right lean measurements  
- ✅ **Speed**: Live GPS speed in MPH
- ✅ **G-Force**: Acceleration/braking forces
- ✅ **Engine Status**: Green when vibration > 500 (engine running)
- ✅ **History Charts**: Time-based trends of all metrics

**Dashboard URL**: http://10.0.0.155:3000/d/your-dashboard-id 