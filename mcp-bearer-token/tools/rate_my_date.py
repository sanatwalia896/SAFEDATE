from mcp import ErrorData, McpError
try:
    from mcp.types import INVALID_PARAMS, INTERNAL_ERROR  # type: ignore  # noqa
except Exception:
    INVALID_PARAMS = -32602  # type: ignore
    INTERNAL_ERROR = -32603  # type: ignore
from pydantic import BaseModel, Field
from typing import Dict, Any
import re
from groq import Groq

class RateMyDateInput(BaseModel):
    date_text: str = Field(..., min_length=1, max_length=1000, description="Description of the date experience")

class RateMyDate:
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.name = "rate_my_date"
        self.description = "Rate your date experience with a fun but useful score"

    def _quick_score(self, text: str) -> Dict[str, int]:
        text_lower = text.lower()
        humor = len(re.findall(r"😂|🤣|haha|lol|funny", text_lower)) * 10
        vibe = len(re.findall(r"nice|sweet|amazing|awesome|great", text_lower)) * 5
        awkward = len(re.findall(r"awkward|boring|weird|meh", text_lower)) * -5
        humor_score = max(0, min(100, humor))
        vibe_score = max(0, min(100, vibe + 50))
        chemistry_score = max(0, min(100, 50 + (vibe - awkward)))
        return {"humor": humor_score, "vibe": vibe_score, "chemistry": chemistry_score}

    async def _llm_review(self, text: str, scores: Dict[str, int]) -> str:
        prompt = f"""
        You are a witty but kind dating coach.
        Scores: Humor {scores['humor']}, Vibe {scores['vibe']}, Chemistry {scores['chemistry']}.
        Date description:\n{text}\n
        Produce a 'Date Report Card' with these sections exactly:
        Overall Rating: <number>/100 - <short explanation>
        Humor: ...
        Vibe: ...
        Chemistry: ...
        Improvements: bullet-style inline list (2-3 items)
        Second Date Prediction: Yes|No - short playful reason

        Output ONLY the report text in the above structure. No introductions, no markdown fences, no extra commentary.
        """
        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "Return ONLY the structured report text. No extra lines."}, {"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=600,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"LLM review failed: {str(e)}"))

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated = RateMyDateInput(**inputs)
        except ValueError as e:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
        scores = self._quick_score(validated.date_text)
        llm_result = await self._llm_review(validated.date_text, scores)
        return {"scores": scores, "report_card": llm_result, "share_text": f"My date score: Chemistry {scores['chemistry']}/100 ❤️ #SafeDateReview"}