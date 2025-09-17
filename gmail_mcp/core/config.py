"""Core configuration and settings for Gmail MCP server."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Server Configuration
    server_host: str = Field(default="0.0.0.0", description="Server host")
    server_port: int = Field(default=8001, description="Server port")
    server_url: str = Field(default="http://localhost:8001", description="This server's URL for resource validation")
    debug: bool = Field(default=True, description="Debug mode")

    # OAuth 2.0 Configuration (RFC 7662 Token Introspection)
    auth_server_url: str = Field(
        default="http://localhost:8000", description="OAuth Authorization Server URL"
    )
    auth_server_introspection_endpoint: str = Field(
        default="http://localhost:8000/oauth/introspect", description="OAuth Token Introspection endpoint (RFC 7662)"
    )
    oauth_strict: bool = Field(default=True, description="Enable RFC 8707 resource validation")
    mcp_scope: str = Field(default="gmail:read gmail:write", description="Required MCP scope for Gmail operations")

    # Gmail API Configuration
    gmail_api_base_url: str = Field(
        default="https://gmail.googleapis.com/gmail/v1", description="Gmail API base URL"
    )

    # MCP Configuration
    mcp_server_name: str = Field(default="gmail_mcp_server", description="MCP server name")

    # Required OAuth scopes for Gmail operations
    required_scopes: List[str] = Field(
        default=[
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/gmail.labels",
        ],
        description="Required Gmail OAuth scopes",
    )

    # Rate limiting
    rate_limit_requests: int = Field(default=100, description="Rate limit: requests per minute")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format"
    )


# Global settings instance
settings = Settings()
