import requests
from mcp.server import Tool
from typing import Dict, Any, List
from groq import Groq

class BestRestaurantsNearMe(Tool):
    def __init__(self, api_key: str, groq_key: str, model: str = "llama3-70b-8192"):
        super().__init__("best_restaurants_near_me", "Find top restaurants near you for a date night")
        self.groq_client = Groq(api_key=groq_key)
        self.model = model
        self.api_key = api_key  # Yelp or Google Places API key

    def _fetch_restaurants(self, location: str) -> List[Dict[str, Any]]:
        """Fetch restaurants from Yelp API (you can switch to Google Places)."""
        url = "https://api.yelp.com/v3/businesses/search"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {
            "term": "romantic restaurant",
            "location": location,
            "limit": 8,
            "sort_by": "rating"
        }
        res = requests.get(url, headers=headers, params=params)
        if res.status_code != 200:
            return []
        return res.json().get("businesses", [])

    def _llm_filter_and_style(self, restaurants: List[Dict[str, Any]]) -> str:
        """Use Groq to filter, style, and make recommendations."""
        restaurant_info = "\n".join([
            f"{r['name']} - {r.get('location', {}).get('address1', '')}, "
            f"Rating: {r.get('rating', '?')} stars, Price: {r.get('price', '?')}"
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
        """
        completion = self.groq_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a fun and knowledgeable foodie guide."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=500
        )
        return completion.choices[0].message.content

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        location = inputs.get("location", "")
        if not location:
            return {"error": "No location provided"}

        restaurants = self._fetch_restaurants(location)
        if not restaurants:
            return {"error": "No restaurants found or API request failed"}

        curated_list = self._llm_filter_and_style(restaurants)

        return {
            "location": location,
            "recommendations": curated_list
        }
