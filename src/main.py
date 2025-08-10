import asyncio
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from tools.text_vibe_checker import TextVibeChecker
from tools.dm_risk_meter import DMRiskMeter
from tools.best_restaurants_near_me import BestRestaurantsNearMe
from tools.outfit_rater import OutfitRater
from tools.safety_tools import SafetyTools
from tools.best_date_idea import BestDateIdea
from tools.rate_my_date import RateMyDate
from tools.date_analyzer import DateAnalyzer
from tools.trendy_date_spotter import TrendyDateSpotter
from tools.date_meme_generator import DateMemeGenerator

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")
MY_NUMBER = os.getenv("MY_NUMBER")

assert all([
    GROQ_API_KEY,
    GOOGLE_API_KEY,
    TAVILY_API_KEY,
    GIPHY_API_KEY,
    MY_NUMBER,
]), "Missing required environment variables (ensure .env is populated)"

# Initialize FastMCP server
mcp = FastMCP(name="SafeDate MCP Server")

# Required validate tool (kept for compatibility with your client expectations)
@mcp.tool(name="validate", description="Return validation number for handshake")
async def validate() -> str:  # type: ignore
    return MY_NUMBER  # type: ignore

# Idempotent registration guard
_tools_registered = False

def register_tool_objects():
    global _tools_registered
    if _tools_registered:
        return
    tool_objs = [
        TextVibeChecker(GROQ_API_KEY, GIPHY_API_KEY),
        DMRiskMeter(GROQ_API_KEY),
        BestRestaurantsNearMe(GOOGLE_API_KEY, GROQ_API_KEY),
        OutfitRater(GROQ_API_KEY),
        SafetyTools(GOOGLE_API_KEY),
        BestDateIdea(GROQ_API_KEY),
        RateMyDate(GROQ_API_KEY),
        DateAnalyzer(GROQ_API_KEY),
        TrendyDateSpotter(TAVILY_API_KEY),
        DateMemeGenerator(GROQ_API_KEY),
    ]

    def make_wrapper(o):
        async def wrapper(**tool_args):  # type: ignore
            # Inspector sometimes wraps real args inside a single 'tool_args' key.
            if "tool_args" in tool_args and isinstance(tool_args["tool_args"], dict):
                flat_args = tool_args["tool_args"]
            else:
                flat_args = tool_args
            return await o.run(flat_args)
        return wrapper

    for obj in tool_objs:
        mcp.add_tool(make_wrapper(obj), name=obj.name, description=obj.description)
    _tools_registered = True

# Ensure tools are registered at import time so `mcp dev main.py` (Inspector) sees them.
register_tool_objects()

def main_stdio():
    print("🚀 SafeDate MCP (stdio) ready")
    mcp.run("stdio")

async def main_sse():
    print("🚀 SafeDate MCP (SSE) starting on http://0.0.0.0:8086")
    await mcp.run_sse_async()  # FastMCP provides this async helper

if __name__ == "__main__":
    transport = os.getenv("TRANSPORT", "stdio").lower()
    if transport == "sse":
        asyncio.run(main_sse())
    else:
        main_stdio()