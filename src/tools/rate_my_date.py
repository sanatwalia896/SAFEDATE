from mcp.server import Tool
from typing import Dict, Any
import re
from groq import Groq

class RateMyDate(Tool):
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        super().__init__("rate_my_date", "Rate your date experience with a fun but useful score")
        self.client = Groq(api_key=api_key)
        self.model = model

    def _quick_score(self, text: str) -> Dict[str, int]:
        """Simple heuristic-based scoring for speed before LLM analysis."""
        text_lower = text.lower()

        humor = len(re.findall(r"😂|🤣|haha|lol|funny", text_lower)) * 10
        vibe = len(re.findall(r"nice|sweet|amazing|awesome|great", text_lower)) * 5
        awkward = len(re.findall(r"awkward|boring|weird|meh", text_lower)) * -5

        humor_score = max(0, min(100, humor))
        vibe_score = max(0, min(100, vibe + 50))  # start from neutral
        chemistry_score = max(0, min(100, 50 + (vibe - awkward)))

        return {
            "humor": humor_score,
            "vibe": vibe_score,
            "chemistry": chemistry_score
        }

    def _llm_review(self, text: str, scores: Dict[str, int]) -> str:
        prompt = f"""
        You are a witty but kind dating coach.
        The user went on a date. Here are the quick scores:
        Humor: {scores['humor']}
        Vibe: {scores['vibe']}
        Chemistry: {scores['chemistry']}

        Date description:
        ---
        {text}
        ---

        1. Give a short, funny but supportive review of the date.
        2. Suggest 2-3 improvements for the next date.
        3. Predict if there should be a second date and why (lighthearted tone).
        Output in a 'Date Report Card' style.
        """
        chat_completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a funny but insightful date reviewer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=600
        )
        return chat_completion.choices[0].message.content

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        date_text = inputs.get("date_text", "")
        if not date_text:
            return {"error": "No date description provided"}

        scores = self._quick_score(date_text)
        llm_result = self._llm_review(date_text, scores)

        return {
            "scores": scores,
            "report_card": llm_result
        }
