"""Gmail OAuth token validation for MCP Server."""

import logging
from typing import Optional, Dict, Any
import httpx
from pydantic import BaseModel

from mcp.server.auth.provider import AccessToken, TokenVerifier

logger = logging.getLogger(__name__)


class TokenInfo(BaseModel):
    """Token information from Gmail OAuth validation."""
    access_token: str
    email: str
    scope: str
    expires_in: Optional[int] = None
    token_type: str = "Bearer"


class TokenValidator:
    """Gmail OAuth token validator."""
    
    def __init__(self):
        self.validation_url = "https://www.googleapis.com/oauth2/v1/tokeninfo"
    
    async def validate_token(self, token: str) -> Optional[TokenInfo]:
        """Validate Gmail OAuth token.
        
        Args:
            token: OAuth access token
            
        Returns:
            TokenInfo if valid, None if invalid
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.validation_url,
                    params={"access_token": token},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    return None
                    
                data = response.json()
                
                # Ensure it's a Gmail token
                scope = data.get("scope", "")
                if "gmail" not in scope.lower():
                    return None
                
                return TokenInfo(
                    access_token=token,
                    email=data.get("email", ""),
                    scope=scope,
                    expires_in=data.get("expires_in")
                )
                
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None


class GmailTokenVerifier(TokenVerifier):
    """Gmail OAuth token verifier using Google's official token validation endpoint.
    
    This validates tokens directly with Google's OAuth 2.0 token info endpoint
    which is the proper way to validate Gmail API tokens.
    """

    def __init__(self, token_validator: TokenValidator):
        """Initialize Gmail token verifier.
        
        Args:
            token_validator: TokenValidator instance to use for validation
        """
        self.token_validator = token_validator
        
    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify Gmail OAuth token using the TokenValidator.
        
        Args:
            token: Gmail OAuth access token
            
        Returns:
            AccessToken if valid, None if invalid
        """
        try:
            # Use our existing TokenValidator to validate the token
            token_info = await self.token_validator.validate_token(token)
            
            if not token_info:
                return None
                
            return AccessToken(
                token=token,
                client_id="gmail_client",  # Could be extracted from token_info if needed
                scopes=token_info.scope.split() if token_info.scope else [],
                expires_at=token_info.expires_in,
                resource=token_info.email  # Use email as resource identifier
            )
                
        except Exception as e:
            logger.error(f"Gmail token verification error: {e}")
            return None


def extract_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    """Extract bearer token from Authorization header.
    
    Args:
        auth_header: Authorization header value
        
    Returns:
        Token if valid Bearer format, None otherwise
    """
    if not auth_header:
        return None
        
    if not auth_header.startswith("Bearer "):
        return None
        
    return auth_header[7:]  # Remove "Bearer " prefix


# Create global instances
token_validator = TokenValidator()
gmail_token_verifier = GmailTokenVerifier(token_validator)