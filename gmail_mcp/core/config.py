from enum import StrEnum
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class TransportType(StrEnum):
    """Transport types for MCP server."""

    SSE = "sse"
    STREAMABLE_HTTP = "streamble_http"


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server Configuration
    server_host: str = Field(default="0.0.0.0", description="Server host")
    server_port: int = Field(default=8001, description="Server port")
    server_url: str = Field(
        default="http://localhost:8001", description="This server's URL for resource validation"
    )
    debug: bool = Field(default=False, description="Debug mode")

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

    # Transport type for MCP server
    transport_type: TransportType = Field(
        default=TransportType.STREAMABLE_HTTP, description="Transport type for MCP server"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format"
    )


# Global settings instance
settings = Settings()
