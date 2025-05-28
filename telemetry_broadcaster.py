#!/usr/bin/env python3
"""
Telemetry Data Broadcaster
Sends motorcycle telemetry data to a remote server via cellular connection
"""

import sqlite3
import json
import time
import requests
import threading
import queue
import logging
from datetime import datetime
import socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TelemetryBroadcaster:
    def __init__(self, db_path='/home/pi/motorcycle_data/telemetry.db'):
        self.db_path = db_path
        self.data_queue = queue.Queue(maxsize=1000)
        self.running = False
        self.last_row_id = self.get_last_row_id()
        
        # Server configuration - can be changed to your server
        self.server_url = "http://your-server.com/api/telemetry"  # Change this
        self.use_tcp = True  # Alternative to HTTP
        self.tcp_host = "your-server.com"  # Change this
        self.tcp_port = 8080  # Change this
        
    def get_last_row_id(self):
        """Get the last row ID from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(rowid) FROM telemetry_data")
            result = cursor.fetchone()
            conn.close()
            return result[0] if result[0] else 0
        except Exception as e:
            logging.error(f"Error getting last row ID: {e}")
            return 0
    
    def collect_data(self):
        """Continuously collect new data from database"""
        logging.info("📊 Starting data collection...")
        
        while self.running:
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get new rows since last check
                cursor.execute("""
                    SELECT rowid, * FROM telemetry_data 
                    WHERE rowid > ? 
                    ORDER BY rowid 
                    LIMIT 100
                """, (self.last_row_id,))
                
                rows = cursor.fetchall()
                
                for row in rows:
                    # Convert row to dict
                    data = dict(row)
                    self.last_row_id = data['rowid']
                    
                    # Add to queue if not full
                    if not self.data_queue.full():
                        self.data_queue.put(data)
                    
                conn.close()
                
                # Sleep if no new data
                if not rows:
                    time.sleep(1)
                    
            except Exception as e:
                logging.error(f"Error collecting data: {e}")
                time.sleep(5)
    
    def send_http(self, data_batch):
        """Send data via HTTP POST"""
        try:
            response = requests.post(
                self.server_url,
                json=data_batch,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logging.info(f"✅ Sent {len(data_batch)} records via HTTP")
                return True
            else:
                logging.error(f"HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"HTTP send error: {e}")
            return False
    
    def send_tcp(self, data_batch):
        """Send data via TCP socket"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.tcp_host, self.tcp_port))
            
            # Send data as JSON
            message = json.dumps(data_batch) + '\n'
            sock.sendall(message.encode())
            
            sock.close()
            logging.info(f"✅ Sent {len(data_batch)} records via TCP")
            return True
            
        except Exception as e:
            logging.error(f"TCP send error: {e}")
            return False
    
    def broadcast_data(self):
        """Continuously broadcast collected data"""
        logging.info("📡 Starting data broadcast...")
        
        batch = []
        batch_size = 10
        last_send = time.time()
        
        while self.running:
            try:
                # Get data from queue (timeout after 1 second)
                try:
                    data = self.data_queue.get(timeout=1)
                    batch.append(data)
                except queue.Empty:
                    pass
                
                # Send batch if full or timeout
                if len(batch) >= batch_size or (time.time() - last_send > 5 and batch):
                    if self.use_tcp:
                        success = self.send_tcp(batch)
                    else:
                        success = self.send_http(batch)
                    
                    if success:
                        batch = []
                    else:
                        # Put data back in queue if send failed
                        for item in batch:
                            if not self.data_queue.full():
                                self.data_queue.put(item)
                        batch = []
                    
                    last_send = time.time()
                    
            except Exception as e:
                logging.error(f"Broadcast error: {e}")
                time.sleep(5)
    
    def check_connectivity(self):
        """Check if we have internet connectivity"""
        try:
            # Try to resolve DNS
            socket.gethostbyname('google.com')
            return True
        except:
            return False
    
    def start(self):
        """Start the broadcaster"""
        logging.info("🚀 Starting Telemetry Broadcaster")
        
        # Check connectivity
        if not self.check_connectivity():
            logging.warning("⚠️  No internet connectivity detected!")
            logging.info("Waiting for cellular connection...")
            
            while not self.check_connectivity():
                time.sleep(5)
                
            logging.info("✅ Internet connectivity established!")
        
        self.running = True
        
        # Start collector thread
        collector_thread = threading.Thread(target=self.collect_data)
        collector_thread.daemon = True
        collector_thread.start()
        
        # Start broadcaster thread
        broadcaster_thread = threading.Thread(target=self.broadcast_data)
        broadcaster_thread.daemon = True
        broadcaster_thread.start()
        
        logging.info("✅ Broadcaster started!")
        logging.info(f"📊 Queue status: {self.data_queue.qsize()} items")
        
        # Keep running
        try:
            while True:
                time.sleep(10)
                logging.info(f"📊 Status - Queue: {self.data_queue.qsize()} items, Last ID: {self.last_row_id}")
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the broadcaster"""
        logging.info("🛑 Stopping broadcaster...")
        self.running = False
        time.sleep(2)

def create_simple_server():
    """Create a simple Python server script for testing"""
    server_code = '''#!/usr/bin/env python3
"""
Simple Telemetry Server
Receives and displays telemetry data
"""

from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/api/telemetry', methods=['POST'])
def receive_telemetry():
    try:
        data = request.json
        print(f"\\n📡 Received {len(data)} telemetry records at {datetime.now()}")
        
        # Process each record
        for record in data:
            if record.get('latitude') and record.get('longitude'):
                print(f"  📍 GPS: {record['latitude']:.6f}, {record['longitude']:.6f}")
                print(f"  🏃 Speed: {record.get('speed_mph', 0):.1f} mph")
                print(f"  📊 G-Force: {record.get('gforce_x', 0):.2f}g")
                
        return jsonify({"status": "success", "received": len(data)})
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    print("🚀 Simple Telemetry Server")
    print("Listening on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
'''
    
    with open('/home/pi/telemetry_server.py', 'w') as f:
        f.write(server_code)
    
    print("✅ Created telemetry_server.py - run this on your server")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--create-server':
        create_simple_server()
    else:
        # Start broadcaster
        broadcaster = TelemetryBroadcaster()
        
        # Configure your server here
        print("⚠️  Please configure your server settings in the script:")
        print("   - server_url: HTTP endpoint to send data")
        print("   - tcp_host/tcp_port: TCP server for socket connection")
        print("\nOr run with --create-server to create a simple test server")
        
        # Uncomment and configure these lines:
        # broadcaster.server_url = "http://your-server.com:5000/api/telemetry"
        # broadcaster.tcp_host = "your-server.com"
        # broadcaster.tcp_port = 8080
        
        # broadcaster.start() 