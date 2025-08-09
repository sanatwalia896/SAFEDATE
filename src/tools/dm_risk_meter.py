from mcp.server import Tool
from typing import Dict, Any
from groq import Groq

class DMRiskMeter(Tool):
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        super().__init__("dm_risk_meter", "Rate unsolicited DMs for creepiness or risk")
        self.client = Groq(api_key=api_key)
        self.model = model

    def _llm_analysis(self, dm_text: str) -> Dict[str, str]:
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

        chat_completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a witty but accurate DM safety analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=300
        )
        import json
        return json.loads(chat_completion.choices[0].message.content)

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        dm_text = inputs.get("dm_text", "")
        if not dm_text:
            return {"error": "No DM text provided"}

        result = self._llm_analysis(dm_text)

        return {
            "risk_level": result["risk_level"],
            "three_word_summary": result["three_word_summary"],
            "reasoning": result["reasoning"],
            "share_text": f"DM Risk: {result['risk_level']} 🚨 — {result['three_word_summary']}"
        }
