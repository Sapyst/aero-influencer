import uvicorn
import webbrowser
import os
import sys

if __name__ == "__main__":
    host = os.environ.get("AERO_HOST", "0.0.0.0")
    port = int(os.environ.get("AERO_PORT", 8080))
    print(f"\n==========================================")
    print(f"🚀 AeroInfluencer Engine v2.0 Starting...")
    print(f"🌐 Local Web UI: http://localhost:{port}")
    print(f"📱 Cross-Platform: Windows | Linux | Android")
    print(f"==========================================\n")
    
    # Try opening browser on desktop environments
    try:
        if os.environ.get("DISPLAY"):
            webbrowser.open(f"http://localhost:{port}")
    except Exception:
        pass

    uvicorn.run("aero_engine.api_server:app", host=host, port=port, reload=False)
