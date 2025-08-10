from mcp import ErrorData, McpError
from mcp.types import ImageContent
try:
    from mcp.types import INVALID_PARAMS, INTERNAL_ERROR  # type: ignore  # noqa
except Exception:
    INVALID_PARAMS = -32602  # type: ignore
    INTERNAL_ERROR = -32603  # type: ignore
from pydantic import BaseModel, Field
from typing import Dict, Any
from groq import Groq
import json, base64, io
from PIL import Image, ImageDraw, ImageFont

class DateMemeGeneratorInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=500, description="Text or conversation to base meme on")
    vibe: str = Field(default="funny", description="Desired meme vibe (e.g., funny, romantic)")

class DateMemeGenerator:
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.name = "date_meme_generator"
        self.description = "Generate a meme based on date or conversation with LLM caption"

    async def _llm_caption(self, text: str, vibe: str) -> str:
        prompt = f"Generate a short meme caption (max 15 words). Text: {text} | Vibe: {vibe}. Return ONLY the caption text with no quotes, no markdown." 
        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "Return ONLY the caption text."}, {"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=100,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"LLM caption failed: {str(e)}"))

    def _generate_meme_image(self, caption: str) -> ImageContent:
        img = Image.new("RGB", (400, 200), color="#FFFFFF")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:  # noqa
            font = ImageFont.load_default()
        draw.text((10, 10), caption[:100], fill="#000000", font=font)
        draw.text((10, 150), "#SafeDateMeme", fill="#FF6B6B", font=font)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return ImageContent(type="image", mimeType="image/png", data=base64.b64encode(buf.getvalue()).decode("utf-8"))

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated = DateMemeGeneratorInput(**inputs)
        except ValueError as e:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
        caption = await self._llm_caption(validated.text, validated.vibe)
        meme = self._generate_meme_image(caption)
        return {"caption": caption, "meme": meme, "share_text": f"{caption} 😂 #SafeDateMeme"}