from mcp.server import Tool
from typing import Dict, Any
import re
from groq import Groq

class OutfitRater(Tool):
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        super().__init__("outfit_rater", "Rate and review your outfit with fashion tips")
        self.client = Groq(api_key=api_key)
        self.model = model

    def _style_score(self, description: str) -> Dict[str, int]:
        """Quick scoring from keywords before AI analysis."""
        desc = description.lower()

        # Style hints
        classy_points = len(re.findall(r"suit|blazer|dress|heels|silk|tailored", desc)) * 10
        casual_points = len(re.findall(r"jeans|t-shirt|hoodie|sneakers", desc)) * 5
        trendy_points = len(re.findall(r"oversized|retro|vintage|streetwear", desc)) * 8
        mismatch_points = len(re.findall(r"clashing|mismatched|wrinkled", desc)) * -10

        style_score = max(0, min(100, classy_points + casual_points + trendy_points + 50 + mismatch_points))
        fit_score = max(0, min(100, 50 + trendy_points - abs(mismatch_points)))
        uniqueness_score = max(0, min(100, trendy_points * 2 + 40))

        return {
            "style": style_score,
            "fit": fit_score,
            "uniqueness": uniqueness_score
        }

    def _llm_fashion_review(self, description: str, scores: Dict[str, int], roast_mode: bool = False) -> str:
        tone = "lightly roast their outfit in a playful way" if roast_mode else "give kind but confident fashion advice"
        prompt = f"""
        You are a top-tier fashion stylist with a fun personality.
        The user describes their outfit:
        ---
        {description}
        ---
        Here are the quick style scores:
        Style: {scores['style']}
        Fit: {scores['fit']}
        Uniqueness: {scores['uniqueness']}

        Your job:
        1. Give an overall rating (0-100) with a brief explanation.
        2. Comment on style, fit, and uniqueness in detail.
        3. Suggest improvements for the occasion they described (if any).
        4. {tone}.
        Keep it short, fun, and Instagram-caption-worthy.
        """
        chat_completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a witty but professional fashion stylist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=500
        )
        return chat_completion.choices[0].message.content

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        description = inputs.get("outfit_description", "")
        roast_mode = inputs.get("roast_mode", False)

        if not description:
            return {"error": "No outfit description provided"}

        scores = self._style_score(description)
        llm_review = self._llm_fashion_review(description, scores, roast_mode)

        return {
            "scores": scores,
            "fashion_review": llm_review
        }
