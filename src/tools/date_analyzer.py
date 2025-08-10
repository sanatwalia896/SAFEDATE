from mcp import Tool, ErrorData, McpError, INVALID_PARAMS, INTERNAL_ERROR
from pydantic import BaseModel, Field
from typing import Dict, Any
from groq import Groq
import json

class DateAnalyzerInput(BaseModel):
    conversation: str = Field(..., min_length=1, max_length=1000, description="Conversation text to analyze for manipulation")

class DateAnalyzer(Tool):
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        super().__init__(
            name="date_analyzer",
            description="Detect manipulation in date conversations like gaslighting or love bombing",
            input_schema=DateAnalyzerInput
        )
        self.client = Groq(api_key=api_key)
        self.model = model

    async def _llm_analysis(self, conversation: str) -> Dict[str, Any]:
        prompt = f"""
        Analyze this conversation for signs of manipulation:
        ---
        {conversation}
        ---
        Detect:
        - Gaslighting (denying reality, blaming)
        - Love bombing (excessive flattery)
        - White-knighting (savior complex)
        Respond in JSON:
        {{
            "manipulations_detected": ["type1", "type2", ...],
            "confidence": ...,
            "explanation": "..."
        }}
        """
        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a manipulation detection expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=400
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
            "share_text": f"Date analysis: {', '.join(analysis.get('manipulations_detected', []))} detected! ⚠️ #SafeDateAnalyzer"
        }