"""
MCP BCRP - Model Context Protocol Server for BCRP Statistical API.

Run as MCP server:
    python -m mcp_bcrp

Use as library:
    from mcp_bcrp.client import AsyncBCRPClient, BCRPMetadata
"""

try:
    # setuptools-scm writes this module during a build.  Importing it here
    # keeps the library version aligned with the wheel/sdist metadata.
    from mcp_bcrp._version import version as __version__
except (ImportError, AttributeError):
    # Source checkouts created before the first build remain importable.
    __version__ = "0+unknown"
__author__ = "Maykol Medrano"

from mcp_bcrp.client import AsyncBCRPClient, BCRPMetadata

__all__ = ["AsyncBCRPClient", "BCRPMetadata", "__version__"]
