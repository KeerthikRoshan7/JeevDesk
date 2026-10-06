"""
JEEVDESK Server Launcher
Launches the FastAPI backend and serves the frontend on http://127.0.0.1:8000
"""
import sys
import os
import uvicorn

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, "backend"))

if __name__ == "__main__":
    print("=" * 70)
    print("JEEVDESK: PM-AJAY AI-Driven Voice Assistant & NSQF Livelihood Mapping")
    print("MoSJE Problem Statement ID: 26097")
    print("Serving on: http://127.0.0.1:8000")
    print("API Documentation: http://127.0.0.1:8000/docs")
    print("=" * 70)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
