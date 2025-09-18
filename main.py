"""Gmail MCP Server - Main application with OAuth 2.0 Token Introspection."""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from mcp.server import FastMCP
from mcp.server.auth.settings import AuthSettings

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gmail_mcp.core.config import settings
from gmail_mcp.auth import gmail_token_verifier
from gmail_mcp.tools import (
    register_reading_tools,
    register_management_tools,
    register_advanced_tools,
)


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format=settings.log_format,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


# Create Gmail OAuth token verifier
token_verifier = gmail_token_verifier

# Create FastMCP server with Gmail OAuth validation
mcp = FastMCP(
    name=settings.mcp_server_name,
    instructions="Production Gmail MCP Server with Google OAuth 2.0 token validation",
    host=settings.server_host,
    port=settings.server_port,
    debug=settings.debug,
    # Gmail OAuth configuration
    token_verifier=token_verifier,
    auth=AuthSettings(
        issuer_url="https://accounts.google.com",  # Google OAuth issuer
        required_scopes=settings.required_scopes,  # Require Gmail scope
        resource_server_url=settings.server_url,
    ),
)

# Register all tools
register_reading_tools(mcp)
register_management_tools(mcp)
register_advanced_tools(mcp)

# Create the MCP app
mcp_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Gmail MCP Server with Google OAuth 2.0 validation...")
    logger.info("Google OAuth issuer: https://accounts.google.com")
    logger.info("Token validation: Google tokeninfo endpoint")
    logger.info("Required scopes: gmail")

    # Use the session manager's run() context manager
    async with mcp.session_manager.run():
        yield

    logger.info("Gmail MCP Server stopped")


# Create FastAPI app
app = FastAPI(
    title="Gmail MCP Server",
    description="Production Gmail MCP Server with OAuth 2.0 support",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Gmail MCP Server",
        "description": "Production Gmail MCP Server with Google OAuth 2.0 token validation",
        "version": "0.1.0",
        "mcp_endpoint": "/mcp",
        "oauth_issuer": "https://accounts.google.com",
        "token_validation": "https://www.googleapis.com/oauth2/v1/tokeninfo",
        "required_scopes": ["gmail"],
        "message_formats": {
            "default": "COMPACT",
            "supported": ["MINIMAL", "COMPACT", "FULL", "RAW", "METADATA"],
            "description": "All reading tools support MessageFormat parameter. COMPACT gives you essential data + body text for optimal performance."
        },
        "tools": [
            # Reading tools (5/5) - Now support MessageFormat
            "get_emails",
            "get_email_by_id", 
            "search_emails",
            "get_labels",
            "get_profile",
            # Management tools (9/9)
            "send_email",
            "reply_to_email",
            "mark_as_read",
            "mark_as_unread",
            "archive_email",
            "delete_email",
            "add_label",
            "remove_label",
            "create_label",
            # Advanced tools (7/7)
            "forward_email",
            "move_to_folder",
            "get_threads",
            "create_draft",
            "get_drafts",
            "send_draft",
            "get_attachments",
        ],
        "authentication": {
            "type": "Bearer Token",
            "description": "Requires valid Gmail OAuth token from Google",
            "oauth_endpoint": "https://accounts.google.com/oauth/authorize",
            "scopes_required": [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.modify",
                "https://www.googleapis.com/auth/gmail.compose",
                "https://www.googleapis.com/auth/gmail.labels",
            ],
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "server": settings.mcp_server_name,
        "oauth_validation": "Google tokeninfo endpoint",
    }


# Mount MCP app
app.mount("", mcp_app)


if __name__ == "__main__":
    logger.info(f"Starting Gmail MCP Server on {settings.server_host}:{settings.server_port}")

    uvicorn.run(
        mcp_app,
        host=settings.server_host,
        port=settings.server_port,
        # reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
