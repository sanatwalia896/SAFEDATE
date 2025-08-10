from mcp import Tool, ErrorData, McpError, INVALID_PARAMS, INTERNAL_ERROR
from mcp.types import ImageContent
from pydantic import BaseModel, Field
from typing import Dict, Any
from groq import Groq
import httpx
import json
import base64
import io
from PIL import Image, ImageDraw, ImageFont
import random

class TextVibeCheckerInput(BaseModel):
    messages: str = Field(..., min_length=1, max_length=1000, description="Conversation text to analyze")
    raw: bool = Field(default=False, description="Return raw analysis if True")

class TextVibeChecker(Tool):
    def __init__(self, api_key: str, giphy_api_key: str, model: str = "llama3-70b-8192"):
        super().__init__(
            name="text_vibe_checker",
            description="Analyze a chat for overall vibe with a shareable meme",
            input_schema=TextVibeCheckerInput
        )
        self.client = Groq(api_key=api_key)
        self.giphy_api_key = giphy_api_key
        self.model = model
        self.vibe_gifs = {
            "Flirty": ["https://media.giphy.com/media/3o6ZsX2PfqDdcZbXnC/giphy.gif"],
            "Bored": ["https://media.giphy.com/media/3o6Zt481isNVuQI1l6/giphy.gif"],
            "Manipulative": ["https://media.giphy.com/media/xT0xezQGU5xCDJuCPe/giphy.gif"],
            "Playful": ["https://media.giphy.com/media/26ufdipQqU2lhNA4g/giphy.gif"],
            "Ghosting": ["https://media.giphy.com/media/3o6Zt6ML6BklcajjsA/giphy.gif"]
        }

    async def _fetch_giphy(self, vibe: str) -> str:
        try:
            url = f"https://api.giphy.com/v1/gifs/search?api_key={self.giphy_api_key}&q={vibe}&limit=1"
            async with httpx.AsyncClient() as client:
                res = await client.get(url, timeout=10)
                res.raise_for_status()
                data = res.json()
                return data["data"][0]["url"] if data["data"] else random.choice(self.vibe_gifs.get(vibe, ["https://media.giphy.com/media/3o7TKsQ8J2e3B8W4z6/giphy.gif"]))
        except Exception:
            return random.choice(self.vibe_gifs.get(vibe, ["https://media.giphy.com/media/3o7TKsQ8J2e3B8W4z6/giphy.gif"]))

    async def _llm_analysis(self, messages: str) -> Dict[str, Any]:
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

        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a fun, witty Vibe Checker AI."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=200
            )
            return json.loads(chat_completion.choices[0].message.content)
        except (json.JSONDecodeError, KeyError, Exception) as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"LLM analysis failed: {str(e)}"))

    def _generate_vibe_meme(self, vibe: str, confidence: int, reason: str) -> ImageContent:
        img = Image.new("RGB", (400, 200), color="#FFFFFF")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()
        draw.text((10, 10), f"Vibe: {vibe} ({confidence}%)", fill="#000000", font=font)
        draw.text((10, 50), f"Because: {reason}", fill="#000000", font=font)
        draw.text((10, 90), "#SafeDateVibes", fill="#FF6B6B", font=font)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return ImageContent(
            type="image",
            mimeType="image/png",
            data=base64.b64encode(buf.getvalue()).decode("utf-8")
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated = TextVibeCheckerInput(**inputs)
        except ValueError as e:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))

        analysis = await self._llm_analysis(validated.messages)
        vibe = analysis.get("vibe", "Unknown")
        confidence = analysis.get("confidence", 0)
        reason = analysis.get("reason", "No vibe detected")

        if validated.raw:
            return analysis

        gif_url = await self._fetch_giphy(vibe)
        meme = self._generate_vibe_meme(vibe, confidence, reason)

        return {
            "vibe": vibe,
            "confidence": confidence,
            "reason": reason,
            "gif_url": gif_url,
            "meme": meme,
            "share_text": f"My chat vibe is {vibe} 😎 ({confidence}% match) — #SafeDateVibes"
        }