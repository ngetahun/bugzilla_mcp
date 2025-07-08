import os
from typing import Optional
from pydantic import BaseSettings, Field, validator
from pydantic_settings import BaseSettings as PydanticBaseSettings


class BugzillaConfig(PydanticBaseSettings):
    """Configuration for Bugzilla MCP Server that reads from environment variables."""
    
    # Bugzilla connection settings
    bugzilla_url: str = Field(
        ...,
        description="Bugzilla instance URL (e.g., https://bugzilla.mozilla.org)",
        env="BUGZILLA_URL"
    )
    
    bugzilla_api_key: Optional[str] = Field(
        None,
        description="Bugzilla API key for authentication",
        env="BUGZILLA_API_KEY"
    )
    
    bugzilla_username: Optional[str] = Field(
        None,
        description="Bugzilla username for authentication",
        env="BUGZILLA_USERNAME"
    )
    
    bugzilla_password: Optional[str] = Field(
        None,
        description="Bugzilla password for authentication",
        env="BUGZILLA_PASSWORD"
    )
    
    # Server settings
    server_host: str = Field(
        "localhost",
        description="Host to bind the MCP server to",
        env="SERVER_HOST"
    )
    
    server_port: int = Field(
        8080,
        description="Port to bind the MCP server to",
        env="SERVER_PORT"
    )
    
    # Request settings
    request_timeout: int = Field(
        30,
        description="Request timeout in seconds",
        env="REQUEST_TIMEOUT"
    )
    
    max_retries: int = Field(
        3,
        description="Maximum number of retries for failed requests",
        env="MAX_RETRIES"
    )
    
    # Logging settings
    log_level: str = Field(
        "INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        env="LOG_LEVEL"
    )
    
    debug_mode: bool = Field(
        False,
        description="Enable debug mode",
        env="DEBUG_MODE"
    )
    
    @validator('bugzilla_url')
    def validate_url(cls, v):
        """Ensure the URL is properly formatted."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Bugzilla URL must start with http:// or https://')
        return v.rstrip('/')
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Ensure log level is valid."""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {", ".join(valid_levels)}')
        return v.upper()
    
    @validator('server_port')
    def validate_port(cls, v):
        """Ensure port is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    def has_api_key_auth(self) -> bool:
        """Check if API key authentication is configured."""
        return self.bugzilla_api_key is not None
    
    def has_username_password_auth(self) -> bool:
        """Check if username/password authentication is configured."""
        return self.bugzilla_username is not None and self.bugzilla_password is not None
    
    def has_auth(self) -> bool:
        """Check if any authentication method is configured."""
        return self.has_api_key_auth() or self.has_username_password_auth()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global config instance
config = BugzillaConfig()