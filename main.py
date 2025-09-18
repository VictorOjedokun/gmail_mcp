"""Gmail MCP Server - Main application with OAuth 2.0 Token Introspection."""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from mcp.server import FastMCP
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions, RevocationOptions

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gmail_mcp.core.config import TransportType, settings
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
        service_documentation_url="https://developers.google.com/gmail/api",  # Gmail API documentation
        required_scopes=settings.required_scopes,  # Require Gmail scope
        resource_server_url=settings.server_url,
        client_registration_options=ClientRegistrationOptions(
            enabled=False,  # Not supporting dynamic client registration
            valid_scopes=settings.required_scopes,  # Valid Gmail scopes
            default_scopes=[
                "https://www.googleapis.com/auth/gmail.readonly"
            ],  # Default to read-only
        ),
        revocation_options=RevocationOptions(enabled=True),  # Support token revocation for security
    ),
)

# Register all tools
register_reading_tools(mcp)
register_management_tools(mcp)
register_advanced_tools(mcp)

# Create the MCP app
if settings.transport_type == TransportType.SSE:
    mcp_app = mcp.sse_app()
else:
    mcp_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Gmail MCP Server with Google OAuth 2.0 validation...")
    logger.info("Google OAuth issuer: https://accounts.google.com")
    logger.info("Token validation: Google tokeninfo endpoint")
    logger.info("Required scopes: gmail")   

    if settings.transport_type == TransportType.STREAMABLE_HTTP:
        # Use the session manager's run() context manager
        async with mcp.session_manager.run():
            yield

    else:
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
            "description": "All reading tools support MessageFormat parameter. COMPACT gives you essential data + body text for optimal performance.",
        },
        "tools": [
            # Reading tools (5/5) - Now support MessageFormat
            "gmail_get_emails",
            "gmail_get_email_by_id",
            "gmail_search_emails",
            "gmail_get_labels",
            "gmail_get_profile",
            # Management tools (11/11)
            "gmail_send_email",
            "gmail_reply_to_email",
            "gmail_mark_as_read",
            "gmail_mark_as_unread",
            "gmail_archive_email",
            "gmail_unarchive_email",
            "gmail_delete_email",
            "gmail_add_label",
            "gmail_remove_label",
            "gmail_create_label",
            "gmail_forward_email",
            # Advanced tools (9/9)
            "gmail_move_to_folder",
            "gmail_get_threads",
            "gmail_get_thread_by_id",
            "gmail_create_draft",
            "gmail_get_drafts",
            "gmail_get_draft_by_id",
            "gmail_send_draft",
            "gmail_get_attachments",
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
