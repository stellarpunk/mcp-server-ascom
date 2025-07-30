"""
Optional security features for ASCOM MCP Server.

Provides OAuth 2.0 authentication when enabled, with minimal configuration.
Security is OFF by default to encourage adoption and ease of use.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class SecurityConfig:
    """
    Security configuration for the MCP server.

    By default, security is disabled for ease of use.
    Enable by setting environment variables or config file.
    """

    def __init__(self):
        # Check if OAuth is enabled via environment
        self.oauth_enabled = (
            os.getenv("ASCOM_MCP_OAUTH_ENABLED", "false").lower() == "true"
        )

        # OAuth configuration (only used if enabled)
        self.oauth_issuer = os.getenv("ASCOM_MCP_OAUTH_ISSUER", "https://auth.example.com")
        self.oauth_audience = os.getenv("ASCOM_MCP_OAUTH_AUDIENCE", "ascom-mcp-server")
        self.oauth_client_id = os.getenv("ASCOM_MCP_OAUTH_CLIENT_ID", "")

        # Token validation settings
        self.require_https = (
            os.getenv("ASCOM_MCP_REQUIRE_HTTPS", "true").lower() == "true"
        )
        self.token_expiry_hours = int(os.getenv("ASCOM_MCP_TOKEN_EXPIRY_HOURS", "24"))

        # Access control
        self.allowed_origins = os.getenv("ASCOM_MCP_ALLOWED_ORIGINS", "*").split(",")
        self.rate_limit_enabled = (
            os.getenv("ASCOM_MCP_RATE_LIMIT", "false").lower() == "true"
        )

        if self.oauth_enabled:
            logger.info("OAuth 2.0 security is ENABLED")
            logger.info(f"OAuth issuer: {self.oauth_issuer}")
        else:
            logger.info(
                "Security is DISABLED (default) - "
                "Set ASCOM_MCP_OAUTH_ENABLED=true to enable"
            )

    def is_enabled(self) -> bool:
        """Check if security features are enabled."""
        return self.oauth_enabled

    async def validate_token(self, token: str | None) -> dict[str, Any]:
        """
        Validate an OAuth token if security is enabled.

        Args:
            token: Bearer token from request

        Returns:
            Token claims if valid, empty dict if security disabled

        Raises:
            SecurityError if token is invalid and security is enabled
        """
        if not self.oauth_enabled:
            # Security disabled, allow all requests
            return {"sub": "anonymous", "scope": "full_access"}

        if not token:
            raise SecurityError("No authentication token provided")

        # In production, validate with OAuth provider
        # This is a simplified example
        try:
            # TODO: Implement actual token validation with OAuth provider
            # For now, accept any non-empty token in demo mode
            logger.warning(
                "OAuth validation not fully implemented - "
                "accepting token for demo"
            )
            return {
                "sub": "demo_user",
                "scope": "read write",
                "exp": (
                    datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
                ).isoformat()
            }
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            raise SecurityError("Invalid authentication token") from e

    def check_origin(self, origin: str | None) -> bool:
        """
        Check if request origin is allowed.

        Args:
            origin: Origin header from request

        Returns:
            True if allowed, False otherwise
        """
        if "*" in self.allowed_origins:
            return True

        if not origin:
            return not self.require_https

        return origin in self.allowed_origins

    def get_security_headers(self) -> dict[str, str]:
        """
        Get security headers to include in responses.

        Returns:
            Dictionary of security headers
        """
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        }

        if self.require_https:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # CORS headers
        if "*" in self.allowed_origins:
            headers["Access-Control-Allow-Origin"] = "*"
        else:
            # In production, set specific origin based on request
            headers["Access-Control-Allow-Origin"] = (
                self.allowed_origins[0] if self.allowed_origins else "null"
            )

        return headers


class SecurityError(Exception):
    """Security-related errors."""
    pass


# Global security configuration instance
security_config = SecurityConfig()


def require_auth(func):
    """
    Decorator to require authentication for specific handlers.

    Only enforces authentication if OAuth is enabled.
    """
    async def wrapper(self, request, *args, **kwargs):
        if security_config.is_enabled():
            # Extract token from request (implementation depends on transport)
            token = getattr(request, 'auth_token', None)

            try:
                claims = await security_config.validate_token(token)
                # Add claims to request for use in handler
                request.auth_claims = claims
            except SecurityError as e:
                logger.warning(f"Authentication failed: {e}")
                # Return error response based on MCP protocol
                from mcp.types import ErrorData
                return ErrorData(
                    code=-32001,  # Custom error code for auth failure
                    message="Authentication required",
                    data={"detail": str(e)}
                )

        return await func(self, request, *args, **kwargs)

    return wrapper


# Example .env file content for enabling OAuth:
"""
# Save as .env in project root to enable OAuth security

# Enable OAuth 2.0 authentication
ASCOM_MCP_OAUTH_ENABLED=true

# OAuth provider configuration
ASCOM_MCP_OAUTH_ISSUER=https://auth.example.com
ASCOM_MCP_OAUTH_AUDIENCE=ascom-mcp-server
ASCOM_MCP_OAUTH_CLIENT_ID=your-client-id

# Security settings
ASCOM_MCP_REQUIRE_HTTPS=true
ASCOM_MCP_TOKEN_EXPIRY_HOURS=24

# CORS settings (comma-separated origins or * for all)
ASCOM_MCP_ALLOWED_ORIGINS=https://app.example.com,https://localhost:3000

# Rate limiting (optional)
ASCOM_MCP_RATE_LIMIT=true
"""
