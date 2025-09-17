#!/usr/bin/env python3
"""Startup script for Gmail MCP Server."""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from main import app, settings, logger
    import uvicorn
    
    def main():
        """Start the Gmail MCP Server."""
        logger.info("🚀 Starting Gmail MCP Server...")
        logger.info(f"📍 Server: {settings.server_host}:{settings.server_port}")
        logger.info(f"🔗 OAuth Server: {settings.oauth_server_url}")
        logger.info(f"📧 Required Scopes: {len(settings.required_scopes)} scopes")
        logger.info(f"🔧 Debug Mode: {settings.debug}")
        
        uvicorn.run(
            app,
            host=settings.server_host,
            port=settings.server_port,
            # reload=settings.debug,
            log_level=settings.log_level.lower(),
        )

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all dependencies are installed: uv sync")
    sys.exit(1)
except Exception as e:
    print(f"❌ Startup error: {e}")
    sys.exit(1)