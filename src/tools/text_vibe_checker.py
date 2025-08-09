from mcp.server import Tool
from typing import Dict, Any
from groq import Groq
import random

class TextVibeChecker(Tool):
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        super().__init__("text_vibe_checker", "Analyze a chat for overall vibe")
        self.client = Groq(api_key=api_key)
        self.model = model

        # Predefined GIFs for vibes (could be Giphy API later)
        self.vibe_gifs = {
            "Flirty": [
                "https://media.giphy.com/media/3o6ZsX2PfqDdcZbXnC/giphy.gif",
                "https://media.giphy.com/media/l0MYB8Ory7Hqefo9a/giphy.gif"
            ],
            "Bored": [
                "https://media.giphy.com/media/3o6Zt481isNVuQI1l6/giphy.gif",
                "https://media.giphy.com/media/xT9IglFQG8Cak3we7e/giphy.gif"
            ],
            "Manipulative": [
                "https://media.giphy.com/media/xT0xezQGU5xCDJuCPe/giphy.gif",
                "https://media.giphy.com/media/3o7abldj0b3rxrZUxW/giphy.gif"
            ],
            "Playful": [
                "https://media.giphy.com/media/26ufdipQqU2lhNA4g/giphy.gif",
                "https://media.giphy.com/media/l4pTfx2qLszoacZRS/giphy.gif"
            ],
            "Ghosting": [
                "https://media.giphy.com/media/3o6Zt6ML6BklcajjsA/giphy.gif",
                "https://media.giphy.com/media/l41lFw057lAJQMwg0/giphy.gif"
            ]
        }

    def _llm_analysis(self, messages: str) -> Dict[str, Any]:
        prompt = f"""
        You are a fun AI "Vibe Checker".
        Given the following conversation:
        ---
        {messages}
        ---
        Classify the *overall vibe* into exactly ONE of these:
        - Flirty
        - Bored
        - Manipulative
        - Playful
        - Ghosting

        Also give:
        1. Confidence score (0-100)
        2. Short, witty one-line reason (max 15 words)
        Respond in JSON format:
        {{
            "vibe": "...",
            "confidence": ...,
            "reason": "..."
        }}
        """

        chat_completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a fun, witty Vibe Checker AI."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=200
        )
        import json
        return json.loads(chat_completion.choices[0].message.content)

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        chat_text = inputs.get("messages", "")
        if not chat_text:
            return {"error": "No messages provided"}

        analysis = self._llm_analysis(chat_text)
        vibe = analysis["vibe"]
        gif_url = random.choice(self.vibe_gifs.get(vibe, []))

        return {
            "vibe": vibe,
            "confidence": analysis["confidence"],
            "reason": analysis["reason"],
            "gif_url": gif_url,
            "share_text": f"My chat vibe is {vibe} 😎 ({analysis['confidence']}% match) — what's yours?"
        }
