from mcp.server.fastmcp import FastMCP
import math

mcp = FastMCP("Bugzilla MCP Server")
# api_url = Config

@mcp.tool()
def read_config():
    pass