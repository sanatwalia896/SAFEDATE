import asyncio
from typing import Annotated
import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp import ErrorData, McpError
from mcp.server.auth.provider import AccessToken
from mcp.types import TextContent, ImageContent, INVALID_PARAMS, INTERNAL_ERROR
from pydantic import BaseModel, Field, AnyUrl

import markdownify
import httpx
import readabilipy

# Import extra tool classes
import json
from tools.best_date_idea import BestDateIdea
from tools.best_restaurants_near_me import BestRestaurantsNearMe
from tools.date_analyzer import DateAnalyzer
from tools.date_meme_generator import DateMemeGenerator
from tools.dm_risk_meter import DMRiskMeter
from tools.outfit_rater import OutfitRater
from tools.rate_my_date import RateMyDate
from tools.safety_tools import SafetyTools
from tools.text_vibe_checker import TextVibeChecker
from tools.trendy_date_spotter import TrendyDateSpotter

# --- Load environment variables ---
load_dotenv()

TOKEN = os.environ.get("AUTH_TOKEN")
MY_NUMBER = os.environ.get("MY_NUMBER")
# Extra API keys for tools
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GIPHY_API_KEY = os.environ.get("GIPHY_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

assert TOKEN is not None, "Please set AUTH_TOKEN in your .env file"
assert MY_NUMBER is not None, "Please set MY_NUMBER in your .env file"

# --- Auth Provider ---
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

# --- Rich Tool Description model ---
class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None = None

# --- Fetch Utility Class ---
class Fetch:
    USER_AGENT = "Puch/1.0 (Autonomous)"

    @classmethod
    async def fetch_url(
        cls,
        url: str,
        user_agent: str,
        force_raw: bool = False,
    ) -> tuple[str, str]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    follow_redirects=True,
                    headers={"User-Agent": user_agent},
                    timeout=30,
                )
            except httpx.HTTPError as e:
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url}: {e!r}"))

            if response.status_code >= 400:
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url} - status code {response.status_code}"))

            page_raw = response.text

        content_type = response.headers.get("content-type", "")
        is_page_html = "text/html" in content_type

        if is_page_html and not force_raw:
            return cls.extract_content_from_html(page_raw), ""

        return (
            page_raw,
            f"Content type {content_type} cannot be simplified to markdown, but here is the raw content:\n",
        )

    @staticmethod
    def extract_content_from_html(html: str) -> str:
        """Extract and convert HTML content to Markdown format."""
        ret = readabilipy.simple_json.simple_json_from_html_string(html, use_readability=True)
        if not ret or not ret.get("content"):
            return "<error>Page failed to be simplified from HTML</error>"
        content = markdownify.markdownify(ret["content"], heading_style=markdownify.ATX)
        return content

    @staticmethod
    async def google_search_links(query: str, num_results: int = 5) -> list[str]:
        """
        Perform a scoped DuckDuckGo search and return a list of job posting URLs.
        (Using DuckDuckGo because Google blocks most programmatic scraping.)
        """
        ddg_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        links = []

        async with httpx.AsyncClient() as client:
            resp = await client.get(ddg_url, headers={"User-Agent": Fetch.USER_AGENT})
            if resp.status_code != 200:
                return ["<error>Failed to perform search.</error>"]

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", class_="result__a", href=True):
            href = a["href"]
            if "http" in href:
                links.append(href)
            if len(links) >= num_results:
                break

        return links or ["<error>No results found.</error>"]

# --- MCP Server Setup ---
mcp = FastMCP(
    "Job Finder MCP Server",
    auth=SimpleBearerAuthProvider(TOKEN),
)

# --- Tool: validate (required by Puch) ---
@mcp.tool
async def validate() -> str:
    return MY_NUMBER

# --- Tool: job_finder (now smart!) ---
JobFinderDescription = RichToolDescription(
    description="Smart job tool: analyze descriptions, fetch URLs, or search jobs based on free text.",
    use_when="Use this to evaluate job descriptions or search for jobs using freeform goals.",
    side_effects="Returns insights, fetched job descriptions, or relevant job links.",
)

@mcp.tool(description=JobFinderDescription.model_dump_json())
async def job_finder(
    user_goal: Annotated[str, Field(description="The user's goal (can be a description, intent, or freeform query)")],
    job_description: Annotated[str | None, Field(description="Full job description text, if available.")] = None,
    job_url: Annotated[AnyUrl | None, Field(description="A URL to fetch a job description from.")] = None,
    raw: Annotated[bool, Field(description="Return raw HTML content if True")] = False,
) -> str:
    """
    Handles multiple job discovery methods: direct description, URL fetch, or freeform search query.
    """
    if job_description:
        return (
            f"📝 **Job Description Analysis**\n\n"
            f"---\n{job_description.strip()}\n---\n\n"
            f"User Goal: **{user_goal}**\n\n"
            f"💡 Suggestions:\n- Tailor your resume.\n- Evaluate skill match.\n- Consider applying if relevant."
        )

    if job_url:
        content, _ = await Fetch.fetch_url(str(job_url), Fetch.USER_AGENT, force_raw=raw)
        return (
            f"🔗 **Fetched Job Posting from URL**: {job_url}\n\n"
            f"---\n{content.strip()}\n---\n\n"
            f"User Goal: **{user_goal}**"
        )

    if "look for" in user_goal.lower() or "find" in user_goal.lower():
        links = await Fetch.google_search_links(user_goal)
        return (
            f"🔍 **Search Results for**: _{user_goal}_\n\n" +
            "\n".join(f"- {link}" for link in links)
        )

    raise McpError(ErrorData(code=INVALID_PARAMS, message="Please provide either a job description, a job URL, or a search query in user_goal."))


# Image inputs and sending images

MAKE_IMG_BLACK_AND_WHITE_DESCRIPTION = RichToolDescription(
    description="Convert an image to black and white and save it.",
    use_when="Use this tool when the user provides an image URL and requests it to be converted to black and white.",
    side_effects="The image will be processed and saved in a black and white format.",
)

@mcp.tool(description=MAKE_IMG_BLACK_AND_WHITE_DESCRIPTION.model_dump_json())
async def make_img_black_and_white(
    puch_image_data: Annotated[str, Field(description="Base64-encoded image data to convert to black and white")] = None,
) -> list[TextContent | ImageContent]:
    import base64
    import io

    from PIL import Image

    try:
        image_bytes = base64.b64decode(puch_image_data)
        image = Image.open(io.BytesIO(image_bytes))

        bw_image = image.convert("L")

        buf = io.BytesIO()
        bw_image.save(buf, format="PNG")
        bw_bytes = buf.getvalue()
        bw_base64 = base64.b64encode(bw_bytes).decode("utf-8")

        return [ImageContent(type="image", mimeType="image/png", data=bw_base64)]
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

# Helper to convert any tool result dict (and optional image) to MCP contents

def _to_contents(tool_name: str, result: dict) -> list[TextContent | ImageContent]:
    contents: list[TextContent | ImageContent] = []
    # Extract image-like payloads if present (e.g., meme)
    if isinstance(result, dict):
        img_keys = [k for k, v in result.items() if isinstance(v, ImageContent)]
        for k in img_keys:
            contents.append(result[k])
        # Prepare a compact JSON for text
        try:
            text_result = {k: v for k, v in result.items() if k not in img_keys}
            text = json.dumps(text_result, ensure_ascii=False, indent=2)
        except TypeError:
            # Fallback if non-serializable objects are present
            text = str(result)
        contents.append(TextContent(type="text", text=f"{tool_name} result:\n\n{text}"))
        return contents
    # If it's already a list of content items or plain text
    if isinstance(result, list):
        return result  # type: ignore[return-value]
    return [TextContent(type="text", text=str(result))]

# --- Tool wrappers for tools/ classes ---

# Best Date Idea
BestDateIdeaDescription = RichToolDescription(
    description="Suggest a unique and fun date idea for tonight",
    use_when="User wants a quick, quirky date idea given location/weather/budget.",
)

@mcp.tool(description=BestDateIdeaDescription.model_dump_json())
async def best_date_idea(
    location: Annotated[str, Field(description="Location for date idea", default="unknown city")],
    weather: Annotated[str, Field(description="Current weather", default="unknown weather")] = "unknown weather",
    budget: Annotated[str, Field(description="Budget level (low, medium, high)", default="flexible")] = "flexible",
) -> list[TextContent | ImageContent]:
    if not GROQ_API_KEY:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Missing GROQ_API_KEY"))
    tool = BestDateIdea(api_key=GROQ_API_KEY)
    result = await tool.run({"location": location, "weather": weather, "budget": budget})
    return _to_contents("best_date_idea", result)

# Best Restaurants Near Me
BestRestaurantsDescription = RichToolDescription(
    description="Find top romantic restaurants near a location using Google Places + LLM curation",
    use_when="User asks for romantic restaurants around a place.",
)

@mcp.tool(description=BestRestaurantsDescription.model_dump_json())
async def best_restaurants_near_me(
    location: Annotated[str, Field(min_length=1, description="Location (e.g., 'New York, NY' or '40.7128,-74.0060')")],
) -> list[TextContent | ImageContent]:
    if not GOOGLE_API_KEY:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Missing GOOGLE_API_KEY"))
    if not GROQ_API_KEY:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Missing GROQ_API_KEY"))
    tool = BestRestaurantsNearMe(google_api_key=GOOGLE_API_KEY, groq_api_key=GROQ_API_KEY)
    result = await tool.run({"location": location})
    return _to_contents("best_restaurants_near_me", result)

# Date Analyzer
DateAnalyzerDescription = RichToolDescription(
    description="Detect manipulation in date conversations like gaslighting or love bombing",
    use_when="You need a safety read on a chat or conversation.",
)

@mcp.tool(description=DateAnalyzerDescription.model_dump_json())
async def date_analyzer(
    conversation: Annotated[str, Field(min_length=1, max_length=1000, description="Conversation text to analyze for manipulation")],
) -> list[TextContent | ImageContent]:
    if not GROQ_API_KEY:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Missing GROQ_API_KEY"))
    tool = DateAnalyzer(api_key=GROQ_API_KEY)
    result = await tool.run({"conversation": conversation})
    return _to_contents("date_analyzer", result)

# Date Meme Generator
DateMemeGeneratorDescription = RichToolDescription(
    description="Generate a meme based on a date or conversation with an LLM-caption",
    use_when="User wants a quick meme image from text and vibe.",
)

@mcp.tool(description=DateMemeGeneratorDescription.model_dump_json())
async def date_meme_generator(
    text: Annotated[str, Field(min_length=1, max_length=500, description="Text or conversation to base meme on")],
    vibe: Annotated[str, Field(description="Desired meme vibe (e.g., funny, romantic)", default="funny")] = "funny",
) -> list[TextContent | ImageContent]:
    if not GROQ_API_KEY:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Missing GROQ_API_KEY"))
    tool = DateMemeGenerator(api_key=GROQ_API_KEY)
    result = await tool.run({"text": text, "vibe": vibe})
    return _to_contents("date_meme_generator", result)

# DM Risk Meter
DMRiskMeterDescription = RichToolDescription(
    description="Rate unsolicited DMs for creepiness or risk with a danger gauge",
    use_when="Assess if a DM is harmless or risky.",
)

@mcp.tool(description=DMRiskMeterDescription.model_dump_json())
async def dm_risk_meter(
    dm_text: Annotated[str, Field(min_length=1, max_length=500, description="DM text to analyze")],
    raw: Annotated[bool, Field(description="Return raw analysis if True", default=False)] = False,
) -> list[TextContent | ImageContent]:
    if not GROQ_API_KEY:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Missing GROQ_API_KEY"))
    tool = DMRiskMeter(api_key=GROQ_API_KEY)
    result = await tool.run({"dm_text": dm_text, "raw": raw})
    return _to_contents("dm_risk_meter", result)

# Outfit Rater
OutfitRaterDescription = RichToolDescription(
    description="Rate and review outfits with fashion tips and optional image support",
    use_when="User wants feedback on an outfit (text or image).",
)

@mcp.tool(description=OutfitRaterDescription.model_dump_json())
async def outfit_rater(
    outfit_description: Annotated[str, Field(description="Text description of the outfit", default="")] = "",
    puch_image_data: Annotated[str, Field(description="Base64-encoded image data of the outfit", default="")] = "",
    roast_mode: Annotated[bool, Field(description="Enable roast mode for playful feedback", default=False)] = False,
) -> list[TextContent | ImageContent]:
    if not GROQ_API_KEY:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Missing GROQ_API_KEY"))
    tool = OutfitRater(api_key=GROQ_API_KEY)
    result = await tool.run({
        "outfit_description": outfit_description,
        "puch_image_data": puch_image_data,
        "roast_mode": roast_mode,
    })
    return _to_contents("outfit_rater", result)

# Rate My Date
RateMyDateDescription = RichToolDescription(
    description="Rate your date experience with a fun but useful score",
    use_when="User wants a report card for a date night.",
)

@mcp.tool(description=RateMyDateDescription.model_dump_json())
async def rate_my_date(
    date_text: Annotated[str, Field(min_length=1, max_length=1000, description="Description of the date experience")],
) -> list[TextContent | ImageContent]:
    if not GROQ_API_KEY:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Missing GROQ_API_KEY"))
    tool = RateMyDate(api_key=GROQ_API_KEY)
    result = await tool.run({"date_text": date_text})
    return _to_contents("rate_my_date", result)

# Safety Tools
SafetyToolsDescription = RichToolDescription(
    description="Find nearby police stations, emergency numbers and SOS links",
    use_when="User needs quick safety resources around current location.",
)

@mcp.tool(description=SafetyToolsDescription.model_dump_json())
async def safety_tools(
    latitude: Annotated[float, Field(description="User's latitude")],
    longitude: Annotated[float, Field(description="User's longitude")],
) -> list[TextContent | ImageContent]:
    if not GOOGLE_API_KEY:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Missing GOOGLE_API_KEY"))
    tool = SafetyTools(google_api_key=GOOGLE_API_KEY)
    result = await tool.run({"latitude": latitude, "longitude": longitude})
    return _to_contents("safety_tools", result)

# Text Vibe Checker
TextVibeCheckerDescription = RichToolDescription(
    description="Analyze a chat for overall vibe and generate a shareable meme",
    use_when="User wants to know the overall vibe of a chat.",
)

@mcp.tool(description=TextVibeCheckerDescription.model_dump_json())
async def text_vibe_checker(
    messages: Annotated[str, Field(min_length=1, max_length=1000, description="Conversation text to analyze")],
    raw: Annotated[bool, Field(description="Return raw analysis if True", default=False)] = False,
) -> list[TextContent | ImageContent]:
    if not GROQ_API_KEY:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Missing GROQ_API_KEY"))
    if not GIPHY_API_KEY:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Missing GIPHY_API_KEY"))
    tool = TextVibeChecker(api_key=GROQ_API_KEY, giphy_api_key=GIPHY_API_KEY)
    result = await tool.run({"messages": messages, "raw": raw})
    return _to_contents("text_vibe_checker", result)

# Trendy Date Spotter
TrendyDateSpotterDescription = RichToolDescription(
    description="Find trending date spots via Tavily web search",
    use_when="User wants hot/trendy date spots in a city.",
)

@mcp.tool(description=TrendyDateSpotterDescription.model_dump_json())
async def trendy_date_spotter(
    location: Annotated[str, Field(min_length=2, max_length=80, description="City or area (e.g. 'Austin, TX')")],
    theme: Annotated[str | None, Field(description="Optional theme: rooftop, cozy, arcade, speakeasy, etc.", default=None)] = None,
    max_results: Annotated[int, Field(ge=1, le=12, description="Maximum spots to return", default=6)] = 6,
) -> list[TextContent | ImageContent]:
    if not TAVILY_API_KEY:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Missing TAVILY_API_KEY"))
    tool = TrendyDateSpotter(tavily_api_key=TAVILY_API_KEY)
    result = await tool.run({"location": location, "theme": theme, "max_results": max_results})
    return _to_contents("trendy_date_spotter", result)

# --- Run MCP Server ---
async def main():
    print("🚀 Starting MCP server on http://0.0.0.0:8086")
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8086)

if __name__ == "__main__":
    asyncio.run(main())
