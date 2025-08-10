from mcp import ErrorData, McpError
try:
    from mcp.types import INVALID_PARAMS, INTERNAL_ERROR  # type: ignore  # noqa
except Exception:
    INVALID_PARAMS = -32602  # type: ignore
    INTERNAL_ERROR = -32603  # type: ignore
from pydantic import BaseModel, Field
from typing import Dict, Any
from groq import Groq
import datetime, json

class BestDateIdeaInput(BaseModel):
    location: str = Field(default="unknown city", description="Location for date idea")
    weather: str = Field(default="unknown weather", description="Current weather")
    budget: str = Field(default="flexible", description="Budget level (low, medium, high)")

class BestDateIdea:
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.name = "best_date_idea"
        self.description = "Suggest a unique and fun date idea for tonight"

    async def _llm_suggestion(self, location: str, weather: str, budget: str) -> Dict[str, str]:
        today = datetime.datetime.now().strftime("%A, %B %d")
        prompt = f"""
        You are a quirky Date Idea Generator.
        It's {today}, location: {location}, weather: {weather}, budget: {budget}.
        Suggest ONE unique, fun, slightly unconventional date idea for TONIGHT only.
        Keep it playful and screenshot-worthy.
        Respond ONLY with a strict JSON object (no markdown, no commentary) with keys: title, description (<=40 words), bonus_tip.
        Example structure:
        {{"title":"...","description":"...","bonus_tip":"..."}}
        """
        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "Output ONLY strict JSON."}, {"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=300,
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
        return {"title": suggestion.get("title"), "description": suggestion.get("description"), "bonus_tip": suggestion.get("bonus_tip"), "share_text": f"Tonight's date idea: {suggestion.get('title')} 💡 — {suggestion.get('description')} #SafeDateIdeas"}