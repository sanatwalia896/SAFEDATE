import asyncio
import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp.server.auth.provider import AccessToken
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
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
MY_NUMBER = os.getenv("MY_NUMBER")

assert all([GROQ_API_KEY, GOOGLE_API_KEY, TAVILY_API_KEY, GIPHY_API_KEY, AUTH_TOKEN, MY_NUMBER]), "Missing required environment variables"

# Custom Bearer Auth Provider
class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(public_key=k.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token,
                client_id="puch-client",
                scopes=["*"],
                expires_at=None,
            )
        return None

# Initialize FastMCP server
mcp = FastMCP(
    name="SafeDate MCP Server",
    auth=SimpleBearerAuthProvider(AUTH_TOKEN),
)

# Required validate tool
@mcp.tool
async def validate() -> str:
    return MY_NUMBER

# Register tools dynamically
def register_tools():
    tools = [
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
    for tool in tools:
        mcp.register_tool(tool)
        print(f"Registered tool: {tool.name}")  # Debug print for hackathon testing

async def main():
    print("🚀 Starting SafeDate MCP server on http://0.0.0.0:8086")
    register_tools()
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8086)

if __name__ == "__main__":
    asyncio.run(main())