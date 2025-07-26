"""Custom exceptions for MCP client."""


class MCPConnectionError(Exception):
    """Raised when MCP connection fails."""
    pass


class MCPAuthenticationError(Exception):
    """Raised when MCP authentication fails."""
    pass


class MCPTimeoutError(Exception):
    """Raised when MCP operation times out."""
    pass


class MCPConfigurationError(Exception):
    """Raised when MCP configuration is invalid."""
    pass


class MCPNotFoundError(Exception):
    """Raised when MCP server or resource is not found."""
    pass
