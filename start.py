#!/usr/bin/env python
"""
Entry point script for Railway deployment
"""
import os
import sys
import uvicorn
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Ensure data directory exists for SQLite
os.makedirs('/app/data', exist_ok=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    
    # Configure uvicorn with proper settings for Railway
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        access_log=True,
        log_level="info",
        timeout_keep_alive=75,
        limit_max_requests=1000
    )