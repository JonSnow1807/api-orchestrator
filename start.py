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
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Ensure data directory exists for SQLite (handle both local and Railway)
try:
    if os.path.exists('/app'):
        os.makedirs('/app/data', exist_ok=True)
        logger.info("Created/verified /app/data directory for Railway")
    else:
        logger.info("Running in local mode")
except Exception as e:
    logger.warning(f"Could not create data directory: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    
    # Configure uvicorn with proper settings for Railway
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        access_log=True,
        log_level="info"
    )