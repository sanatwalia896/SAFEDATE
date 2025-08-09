from mcp import Tool, ErrorData, McpError, INVALID_PARAMS, INTERNAL_ERROR
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import httpx
import json

class TrendyDateSpotterInput(BaseModel):
    location: str = Field(..., min_length=1, description="City or area to find trending date spots for")
    max_results: int = Field(default=5, ge=1, le=10, description="Number of results to return")

class TrendyDateSpotter(Tool):
    def __init__(self, tavily_api_key: str):
        super().__init__(
            name="trendy_date_spotter",
            description="Find trending date spots using real-time Tavily search",
            input_schema=TrendyDateSpotterInput
        )
        self.tavily_api_key = tavily_api_key

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated = TrendyDateSpotterInput(**inputs)
        except ValueError as e:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))

        query = f"trending date spots in {validated.location}"
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "max_results": validated.max_results,
            "search_depth": "advanced",
            "include_answer": True
        }

        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(url, json=payload, timeout=10)
                res.raise_for_status()
                data = res.json()
            except Exception as e:
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Tavily search failed: {str(e)}"))

        spots = [
            {"title": result["title"], "url": result["url"], "snippet": result["content"][:200]}
            for result in data.get("results", [])
        ]
        share_text = f"Hot date spots in {validated.location}! 🔥 Check out: {spots[0]['url'] if spots else ''} #SafeDateTrends"

        return {
            "location": validated.location,
            "trending_spots": spots,
            "share_text": share_text
        }