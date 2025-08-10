from mcp import Tool, ErrorData, McpError, INVALID_PARAMS, INTERNAL_ERROR
from pydantic import BaseModel, Field
from typing import Dict, Any
from groq import Groq
import datetime
import json

class BestDateIdeaInput(BaseModel):
    location: str = Field(default="unknown city", description="Location for date idea")
    weather: str = Field(default="unknown weather", description="Current weather")
    budget: str = Field(default="flexible", description="Budget level (low, medium, high)")

class BestDateIdea(Tool):
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        super().__init__(
            name="best_date_idea",
            description="Suggest a unique and fun date idea for tonight",
            input_schema=BestDateIdeaInput
        )
        self.client = Groq(api_key=api_key)
        self.model = model

    async def _llm_suggestion(self, location: str, weather: str, budget: str) -> Dict[str, str]:
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

        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a fun, viral date idea generator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=300
            )
            return json.loads(chat_completion.choices[0].message.content)
        except (json.JSONDecodeError, KeyError, Exception) as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"LLM suggestion failed: {str(e)}"))

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated = BestDateIdeaInput(**inputs)
        except ValueError as e:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))

        suggestion = await self._llm_suggestion(validated.location, validated.weather, validated.budget)

        return {
            "title": suggestion["title"],
            "description": suggestion["description"],
            "bonus_tip": suggestion["bonus_tip"],
            "share_text": f"Tonight's date idea: {suggestion['title']} 💡 — {suggestion['description']} #SafeDateIdeas"
        }