#!/usr/bin/env python
"""
MCP BCRP Server Entry Point.
This script allows running the server directly from the source directory.
"""

from mcp_bcrp.server import mcp

if __name__ == "__main__":
    mcp.run()
