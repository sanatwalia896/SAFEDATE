from mcp.server import Tool
from typing import Dict, Any
from groq import Groq

class DateAnalyzer(Tool):
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        super().__init__("date_analyzer", "Analyze chats/dates for red flags, green flags, and safety score")
        self.client = Groq(api_key=api_key)
        self.model = model

    def _llm_analysis(self, text: str) -> Dict[str, Any]:
        """
        Use Groq LLM to detect psychological patterns in the date conversation.
        """
        prompt = f"""
        You are an AI dating safety coach and psychologist.
        Given the following conversation or date description:
        ---
        {text}
        ---

        1. Detect and rate these (0-10 severity):
           - Gaslighting
           - Love bombing
           - White knight behavior
           - Negging or backhanded compliments
           - Controlling behavior
        2. Detect and rate these positive traits (0-10 presence):
           - Respectfulness
           - Empathy
           - Mutual interest
        3. Give a "Danger Index" from 0 (very safe) to 100 (very unsafe).
        4. List evidence quotes for each detection.
        5. Give a friendly, constructive summary and advice.

        Output JSON with keys:
        {{
            "danger_index": int,
            "red_flags": {{ "gaslighting": int, "love_bombing": int, "white_knight": int, "negging": int, "control": int }},
            "green_flags": {{ "respect": int, "empathy": int, "interest": int }},
            "advice": str
        }}
        """
        chat_completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a wise, empathetic dating psychologist who outputs structured JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        import json
        try:
            return json.loads(chat_completion.choices[0].message.content)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON from model", "raw": chat_completion.choices[0].message.content}

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        chat_text = inputs.get("chat_text", "")
        if not chat_text:
            return {"error": "No text provided"}
        
        return self._llm_analysis(chat_text)
