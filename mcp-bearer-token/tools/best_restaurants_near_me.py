from mcp import ErrorData, McpError
try:
    from mcp.types import INVALID_PARAMS, INTERNAL_ERROR  # type: ignore  # noqa
except Exception:
    INVALID_PARAMS = -32602  # type: ignore
    INTERNAL_ERROR = -32603  # type: ignore
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from groq import Groq
import httpx

class BestRestaurantsNearMeInput(BaseModel):
    location: str = Field(..., min_length=1, description="Location for restaurant search (e.g., 'New York, NY' or '40.7128,-74.0060')")

class BestRestaurantsNearMe:
    def __init__(self, google_api_key: str, groq_api_key: str, model: str = "llama3-70b-8192"):
        self.google_api_key = google_api_key
        self.groq_client = Groq(api_key=groq_api_key)
        self.model = model
        self.name = "best_restaurants_near_me"
        self.description = "Find top romantic restaurants near a location using Google Places API"

    async def _fetch_restaurants(self, location: str) -> List[Dict[str, Any]]:
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": location,
            "radius": 5000,
            "type": "restaurant",
            "keyword": "romantic",
            "key": self.google_api_key
        }
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(url, params=params, timeout=10)
                res.raise_for_status()
                return res.json().get("results", [])
            except Exception as e:
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Google Places API failed: {str(e)}"))

    async def _llm_filter_and_style(self, restaurants: List[Dict[str, Any]]) -> str:
        restaurant_info = "\n".join([
            f"{r['name']} - {r.get('vicinity', '')}, Rating: {r.get('rating', '?')} stars"
            for r in restaurants
        ])
        prompt = f"""
        You are a fun but knowledgeable date night planner.
        Here’s a list of nearby restaurants:
        {restaurant_info}
        1. Pick the **top 3 date night spots** based on romance, vibe, and uniqueness.
        2. Give each a short, fun review (1-2 sentences).
        3. Suggest 3 backup options if the top spots are full.
        4. Add a 'Pro Tip' for each top choice (e.g., best time to go, what to order).
        Keep it concise but exciting, like a TikTok foodie influencer.
        Output ONLY the formatted recommendations text. No introductory or closing phrases.
        """
        try:
            completion = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Respond with ONLY the requested formatted content. No extra sentences."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"LLM filtering failed: {str(e)}"))

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated = BestRestaurantsNearMeInput(**inputs)
        except ValueError as e:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))

        restaurants = await self._fetch_restaurants(validated.location)
        if not restaurants:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message="No restaurants found"))

        curated_list = await self._llm_filter_and_style(restaurants)

        return {
            "location": validated.location,
            "recommendations": curated_list,
            "share_text": f"Top date spots in {validated.location}! 🍽️ #SafeDateEats"
        }