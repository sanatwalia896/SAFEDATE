from mcp import ErrorData, McpError
try:
    from mcp.types import INVALID_PARAMS, INTERNAL_ERROR  # type: ignore  # noqa
except Exception:
    INVALID_PARAMS = -32602  # type: ignore
    INTERNAL_ERROR = -32603  # type: ignore
from pydantic import BaseModel, Field
from typing import Dict, Any
from groq import Groq
import json

class DateAnalyzerInput(BaseModel):
    conversation: str = Field(..., min_length=1, max_length=1000, description="Conversation text to analyze for manipulation")

class DateAnalyzer:
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.name = "date_analyzer"
        self.description = "Detect manipulation in date conversations like gaslighting or love bombing"

    async def _llm_analysis(self, conversation: str) -> Dict[str, Any]:
        prompt = f"""
        Analyze this conversation for signs of manipulation:
        ---\n{conversation}\n---
        Detect gaslighting, love bombing, white-knighting.
        Return ONLY a strict JSON object (no markdown) with keys:
        manipulations_detected (array of strings), confidence (0-100), explanation.
        Example structure:
        {{"manipulations_detected":["gaslighting"],"confidence":85,"explanation":"..."}}
        """
        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "Output ONLY strict JSON."}, {"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=400,
            )
            return json.loads(chat_completion.choices[0].message.content)
        except (json.JSONDecodeError, KeyError, Exception) as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"LLM analysis failed: {str(e)}"))

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated = DateAnalyzerInput(**inputs)
        except ValueError as e:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
        analysis = await self._llm_analysis(validated.conversation)
        return {
            "manipulations_detected": analysis.get("manipulations_detected", []),
            "confidence": analysis.get("confidence", 0),
            "explanation": analysis.get("explanation", ""),
            "share_text": f"Date analysis: {', '.join(analysis.get('manipulations_detected', []))} detected! ⚠️ #SafeDateAnalyzer",
        }