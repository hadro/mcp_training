# server.py

from mcp.server.fastmcp import FastMCP

# This is the shared MCP server instance
mcp = FastMCP("mcp_server", port=8001)

