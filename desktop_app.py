import sys
import os
import socket
import threading
import time
import uvicorn
import webview

def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def start_backend_server(port: int):
    # Runs FastAPI quietly bound to localhost only (never exposed externally)
    from aero_engine.api_server import app
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=port,
        log_level="error",
        access_log=False
    )
    server = uvicorn.Server(config)
    server.run()

def main():
    port = find_free_port()
    
    # Start internal engine on localhost
    server_thread = threading.Thread(target=start_backend_server, args=(port,), daemon=True)
    server_thread.start()

    # Wait briefly for server ready
    time.sleep(1.0)

    # Launch native desktop window (no terminal, no address bar, native borders)
    window = webview.create_window(
        title="AeroInfluencer Studio",
        url=f"http://127.0.0.1:{port}",
        width=1280,
        height=850,
        min_size=(980, 680),
        background_color='#0d0e14'
    )
    webview.start(debug=False)
    sys.exit(0)

if __name__ == "__main__":
    main()
