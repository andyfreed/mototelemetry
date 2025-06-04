#!/usr/bin/env python3
"""
GPS Proxy Service
Forwards GPS data from localhost:2947 to all interfaces on port 2948
for remote access via Tailscale
"""

import socket
import threading
import time
import sys

def handle_client(client_socket, gps_host='127.0.0.1', gps_port=2947):
    """Handle a client connection by forwarding data to/from GPS daemon"""
    try:
        # Connect to local GPS daemon
        gps_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        gps_socket.connect((gps_host, gps_port))
        
        print(f"Connected client to GPS daemon at {gps_host}:{gps_port}")
        
        # Forward data in both directions
        def forward_data(source, destination, direction):
            try:
                while True:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.send(data)
            except Exception as e:
                print(f"Error forwarding {direction}: {e}")
            finally:
                source.close()
                destination.close()
        
        # Start forwarding threads
        client_to_gps = threading.Thread(
            target=forward_data, 
            args=(client_socket, gps_socket, "client->GPS")
        )
        gps_to_client = threading.Thread(
            target=forward_data, 
            args=(gps_socket, client_socket, "GPS->client")
        )
        
        client_to_gps.daemon = True
        gps_to_client.daemon = True
        
        client_to_gps.start()
        gps_to_client.start()
        
        # Wait for threads to complete
        client_to_gps.join()
        gps_to_client.join()
        
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass

def main():
    """Main proxy server"""
    proxy_host = '0.0.0.0'  # Listen on all interfaces
    proxy_port = 2948       # Different port to avoid conflicts
    
    print(f"🛰️ Starting GPS Proxy Server on {proxy_host}:{proxy_port}")
    print(f"   Forwarding to localhost:2947")
    print(f"   Remote access: http://TAILSCALE_IP:{proxy_port}")
    
    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((proxy_host, proxy_port))
        server_socket.listen(5)
        print(f"✅ GPS Proxy listening on port {proxy_port}")
        
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                print(f"📡 New GPS client connected from {client_address}")
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=handle_client, 
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except KeyboardInterrupt:
                print("\n🛑 Shutting down GPS proxy...")
                break
            except Exception as e:
                print(f"❌ Error accepting connection: {e}")
                time.sleep(1)
                
    except Exception as e:
        print(f"❌ Failed to start GPS proxy: {e}")
        sys.exit(1)
    finally:
        server_socket.close()

if __name__ == "__main__":
    main() 