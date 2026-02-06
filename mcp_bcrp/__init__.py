"""
MCP BCRP - Model Context Protocol Server for BCRP Statistical API.

Run as MCP server:
    python -m mcp_bcrp

Use as library:
    from mcp_bcrp.client import AsyncBCRPClient, BCRPMetadata
"""

__version__ = "0.1.0"
__author__ = "Maykol Medrano"

from mcp_bcrp.client import AsyncBCRPClient, BCRPMetadata

__all__ = ["AsyncBCRPClient", "BCRPMetadata", "__version__"]
