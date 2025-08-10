from mcp import ErrorData, McpError
try:  # Prefer constants from mcp.types
    from mcp.types import INVALID_PARAMS, INTERNAL_ERROR  # type: ignore  # noqa
except Exception:  # Fallback JSON-RPC codes
    INVALID_PARAMS = -32602  # type: ignore
    INTERNAL_ERROR = -32603  # type: ignore
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import httpx

class TrendyDateSpotterInput(BaseModel):
    location: str = Field(..., min_length=2, max_length=80, description="City or area (e.g. 'Austin, TX')")
    theme: str | None = Field(default=None, description="Optional theme: rooftop, cozy, arcade, speakeasy, etc.")
    max_results: int = Field(default=6, ge=1, le=12, description="Maximum spots to return")

class TrendyDateSpotter:  # plain class (no inheritance from mcp.Tool)
    def __init__(self, tavily_api_key: str):
        self.name = "trendy_date_spotter"
        self.description = "Find trending date spots via Tavily web search"
        self.api_key = tavily_api_key
        self.endpoint = "https://api.tavily.com/search"

    async def _tavily_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
        }
        try:
            async with httpx.AsyncClient(timeout=12) as client:
                res = await client.post(self.endpoint, json=payload)
                res.raise_for_status()
                data = res.json()
        except Exception as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Tavily API error: {e}"))
        results = data.get("results", [])
        formatted: List[Dict[str, Any]] = []
        for r in results:
            formatted.append({
                "title": r.get("title"),
                "url": r.get("url"),
                "snippet": (r.get("content") or "")[:280],
            })
        return formatted

    def _curate(self, raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        keywords = ["rooftop", "speakeasy", "hidden", "underground", "arcade", "museum", "gallery", "theater", "popup"]
        scored: List[tuple[float, Dict[str, Any]]] = []
        for item in raw:
            text = (item.get("title", "") + " " + item.get("snippet", "")).lower()
            score = sum(3 for k in keywords if k in text) + len(text) / 400
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [i for _, i in scored]

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated = TrendyDateSpotterInput(**inputs)
        except ValueError as e:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
        if not self.api_key:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message="Missing Tavily API key"))
        theme_part = f" {validated.theme} " if validated.theme else " "
        query = f"trending date spots{theme_part}in {validated.location} 2025".strip()
        raw_results = await self._tavily_search(query, validated.max_results * 2)
        if not raw_results:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message="No search results"))
        curated = self._curate(raw_results)[: validated.max_results]
        spots = [
            {"rank": idx + 1, "title": r.get("title"), "url": r.get("url"), "snippet": r.get("snippet")}
            for idx, r in enumerate(curated)
        ]
        share_text = f"Trending date spots in {validated.location}! Top pick: {spots[0]['title'] if spots else 'None'} #SafeDateSpots"
        return {"location": validated.location, "query": query, "spots": spots, "share_text": share_text}