# from mcp.server import Tool
# from typing import Dict, Any
# from groq import Groq

# class DMRiskMeter(Tool):
#     def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
#         super().__init__("dm_risk_meter", "Rate unsolicited DMs for creepiness or risk")
#         self.client = Groq(api_key=api_key)
#         self.model = model

#     def _llm_analysis(self, dm_text: str) -> Dict[str, str]:
#         prompt = f"""
#         You are an expert in reading between the lines of unsolicited DMs.
#         Given this DM:
#         ---
#         {dm_text}
#         ---
#         Classify it as one of: "Harmless", "Flirty but fine", "Weird but safe", "Borderline creepy", "Run".
#         Provide:
#         1. risk_level → exactly one of the categories above
#         2. three_word_summary → exactly 3 words, funny roast style (e.g., "Creepy power move", "Thirsty but harmless")
#         3. reasoning → short reason why you rated it that way
#         Respond in JSON:
#         {{
#             "risk_level": "...",
#             "three_word_summary": "...",
#             "reasoning": "..."
#         }}
#         """

#         chat_completion = self.client.chat.completions.create(
#             model=self.model,
#             messages=[
#                 {"role": "system", "content": "You are a witty but accurate DM safety analyst."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.8,
#             max_tokens=300
#         )
#         import json
#         return json.loads(chat_completion.choices[0].message.content)

#     async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
#         dm_text = inputs.get("dm_text", "")
#         if not dm_text:
#             return {"error": "No DM text provided"}

#         result = self._llm_analysis(dm_text)

#         return {
#             "risk_level": result["risk_level"],
#             "three_word_summary": result["three_word_summary"],
#             "reasoning": result["reasoning"],
#             "share_text": f"DM Risk: {result['risk_level']} 🚨 — {result['three_word_summary']}"
#         }


from mcp import Tool, ErrorData, McpError, INVALID_PARAMS, INTERNAL_ERROR
from pydantic import BaseModel, Field
from typing import Dict, Any
from groq import Groq
import json
import httpx

class DMRiskMeterInput(BaseModel):
    dm_text: str = Field(..., min_length=1, max_length=500, description="DM text to analyze")
    raw: bool = Field(default=False, description="Return raw analysis if True")

class DMRiskMeter(Tool):
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        super().__init__(
            name="dm_risk_meter",
            description="Rate unsolicited DMs for creepiness or risk with a danger gauge",
            input_schema=DMRiskMeterInput
        )
        self.client = Groq(api_key=api_key)
        self.model = model

    async def _llm_analysis(self, dm_text: str) -> Dict[str, str]:
        prompt = f"""
        You are an expert in reading between the lines of unsolicited DMs.
        Given this DM:
        ---
        {dm_text}
        ---
        Classify it as one of: "Harmless", "Flirty but fine", "Weird but safe", "Borderline creepy", "Run".
        Provide:
        1. risk_level → exactly one of the categories above
        2. three_word_summary → exactly 3 words, funny roast style (e.g., "Creepy power move", "Thirsty but harmless")
        3. reasoning → short reason why you rated it that way
        Respond in JSON:
        {{
            "risk_level": "...",
            "three_word_summary": "...",
            "reasoning": "..."
        }}
        """

        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a witty but accurate DM safety analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=300
            )
            return json.loads(chat_completion.choices[0].message.content)
        except (json.JSONDecodeError, KeyError, Exception) as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"LLM analysis failed: {str(e)}"))

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated = DMRiskMeterInput(**inputs)
        except ValueError as e:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))

        result = await self._llm_analysis(validated.dm_text)

        if validated.raw:
            return result

        # Add danger gauge (ASCII for virality)
        levels = ["Harmless", "Flirty but fine", "Weird but safe", "Borderline creepy", "Run"]
        index = levels.index(result["risk_level"]) if result["risk_level"] in levels else 0
        gauge = "🟢" * (index + 1) + "🔴" * (4 - index)

        return {
            "risk_level": result["risk_level"],
            "three_word_summary": result["three_word_summary"],
            "reasoning": result["reasoning"],
            "danger_gauge": gauge,
            "share_text": f"DM Risk: {result['risk_level']} 🚨 — {result['three_word_summary']} #SafeDateRisk"
        }