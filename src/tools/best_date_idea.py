from mcp.server import Tool
from typing import Dict, Any
from groq import Groq
import datetime

class BestDateIdea(Tool):
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        super().__init__("best_date_idea", "Suggest a unique and fun date idea for tonight")
        self.client = Groq(api_key=api_key)
        self.model = model

    def _llm_suggestion(self, location: str, weather: str, budget: str) -> str:
        today = datetime.datetime.now().strftime("%A, %B %d")
        prompt = f"""
        You are a quirky Date Idea Generator.
        It's {today}, location: {location}, weather: {weather}, budget: {budget}.

        Suggest ONE unique, fun, slightly unconventional date idea for TONIGHT only.
        Keep it playful and screenshot-worthy, for example:
        - "Go to IKEA and make fake backstories for the couples you see"
        - "Find a quiet diner and order the weirdest thing on the menu"
        Include:
        1. Catchy title
        2. Short description (max 40 words)
        3. Bonus tip for making it memorable

        Respond in JSON:
        {{
            "title": "...",
            "description": "...",
            "bonus_tip": "..."
        }}
        """

        chat_completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a fun, viral date idea generator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=300
        )
        import json
        return json.loads(chat_completion.choices[0].message.content)

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        location = inputs.get("location", "unknown city")
        weather = inputs.get("weather", "unknown weather")
        budget = inputs.get("budget", "flexible")

        suggestion = self._llm_suggestion(location, weather, budget)

        return {
            "title": suggestion["title"],
            "description": suggestion["description"],
            "bonus_tip": suggestion["bonus_tip"],
            "share_text": f"Tonight's date idea: {suggestion['title']} 💡 — {suggestion['description']}"
        }
