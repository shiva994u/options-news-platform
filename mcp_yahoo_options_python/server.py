from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from tools.options_tools import register_options_tools
from tools.news_tools import register_news_tools
from tools.multistocks_tools import register_multi_tools

# ---- Logging ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- MCP server ----
mcp = FastMCP("OptionsNewsMCP")

# Register tools from modules
register_options_tools(mcp)
register_news_tools(mcp)
register_multi_tools(mcp)


if __name__ == "__main__":
    logger.info("Starting OptionsNewsMCP server...")
    mcp.run()
