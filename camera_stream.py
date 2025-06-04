#!/usr/bin/env python3
"""
Motorcycle Camera Stream
Captures video from the connected camera and provides a video stream for Node-RED dashboard
"""

import cv2
import time
import logging
import threading
import socketserver
from http import server
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

# Configuration
PORT = 8090
RESOLUTION = (640, 480)
FRAMERATE = 15
DATA_DIR = Path("/home/pi/motorcycle_data")
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
LOG_PATH = DATA_DIR / "camera.log"

# Global variables
frame_buffer = None
frame_lock = threading.Lock()
running = True

class StreamingHandler(server.BaseHTTPRequestHandler):
    """HTTP handler for streaming video"""
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_index_html().encode('utf-8'))
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while running:
                    with frame_lock:
                        if frame_buffer is None:
                            time.sleep(0.1)
                            continue
                        frame_data = frame_buffer
                    
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame_data))
                    self.end_headers()
                    self.wfile.write(frame_data)
                    self.wfile.write(b'\r\n')
                    time.sleep(1/FRAMERATE)
            except Exception as e:
                logging.warning(f'Streaming client disconnected: {str(e)}')
        elif self.path == '/snapshot':
            # Take a snapshot and save it
            with frame_lock:
                if frame_buffer is None:
                    self.send_response(503)
                    self.end_headers()
                    return
                frame_data = frame_buffer
                
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"snapshot_{timestamp}.jpg"
            filepath = SNAPSHOTS_DIR / filename
            
            try:
                with open(filepath, 'wb') as f:
                    f.write(frame_data)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(f'{{"status": "success", "filename": "{filename}"}}'.encode('utf-8'))
            except Exception as e:
                logging.error(f"Error saving snapshot: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_error(404)
            self.end_headers()
    
    def get_index_html(self):
        """Return the HTML page for direct browser viewing"""
        return f'''
        <html>
        <head>
            <title>Motorcycle Camera</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; text-align: center; background-color: #f0f0f0; }}
                h1 {{ color: #333; }}
                img {{ max-width: 100%; border: 2px solid #333; border-radius: 5px; }}
                .controls {{ margin: 20px 0; }}
                button {{ background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
                button:hover {{ background-color: #45a049; }}
            </style>
        </head>
        <body>
            <h1>🏍️ Motorcycle Camera Feed</h1>
            <img src="/stream.mjpg" />
            <div class="controls">
                <button onclick="takeSnapshot()">📸 Take Snapshot</button>
            </div>
            <div id="status"></div>
            
            <script>
                function takeSnapshot() {{
                    document.getElementById('status').innerHTML = 'Taking snapshot...';
                    fetch('/snapshot')
                        .then(response => response.json())
                        .then(data => {{
                            document.getElementById('status').innerHTML = 
                                `Snapshot saved: ${{data.filename}}`;
                        }})
                        .catch(error => {{
                            document.getElementById('status').innerHTML = 
                                `Error: ${{error}}`;
                        }});
                }}
            </script>
        </body>
        </html>
        '''

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    """HTTP server for streaming video"""
    allow_reuse_address = True
    daemon_threads = True

def camera_capture_thread():
    """Thread to capture frames from the camera"""
    global frame_buffer, running
    
    logging.info("Starting camera capture thread")
    
    # Initialize camera
    camera = None
    try:
        # Try USB camera first, then fallback to default
        camera = cv2.VideoCapture(0)  # USB camera should be device 0
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])
        camera.set(cv2.CAP_PROP_FPS, FRAMERATE)
        
        logging.info(f"Camera initialized at {RESOLUTION[0]}x{RESOLUTION[1]} @ {FRAMERATE}fps")
        
        # Camera capture loop
        while running:
            success, frame = camera.read()
            if not success:
                logging.error("Failed to capture frame from camera")
                time.sleep(1)
                continue
                
            # Add timestamp to frame
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cv2.putText(frame, timestamp, (10, frame.shape[0] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Convert to JPEG
            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                continue
                
            # Update frame buffer with thread safety
            with frame_lock:
                frame_buffer = jpeg.tobytes()
                
            time.sleep(1/FRAMERATE)
    
    except Exception as e:
        logging.error(f"Camera capture error: {e}")
    finally:
        if camera:
            camera.release()
        logging.info("Camera capture thread stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global running
    logging.info("Received shutdown signal")
    running = False
    
def setup_logging():
    """Setup logging configuration"""
    DATA_DIR.mkdir(exist_ok=True)
    SNAPSHOTS_DIR.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_PATH),
            logging.StreamHandler()
        ]
    )

def main():
    """Main function"""
    setup_logging()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logging.info(f"Starting motorcycle camera stream on port {PORT}")
    
    # Start camera capture thread
    capture_thread = threading.Thread(target=camera_capture_thread, daemon=True)
    capture_thread.start()
    
    # Start HTTP server
    try:
        server = StreamingServer(('0.0.0.0', PORT), StreamingHandler)
        logging.info(f"📹 Camera stream available at http://localhost:{PORT}/")
        server.serve_forever()
    except Exception as e:
        logging.error(f"Server error: {e}")
    finally:
        global running
        running = False
        capture_thread.join(timeout=2)
        logging.info("Camera stream server stopped")

if __name__ == '__main__':
    main() 