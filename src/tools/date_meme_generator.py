from mcp import Tool, ErrorData, McpError, INVALID_PARAMS, INTERNAL_ERROR
from mcp.types import ImageContent
from pydantic import BaseModel, Field
from typing import Dict, Any
from groq import Groq
import json
import base64
import io
from PIL import Image, ImageDraw, ImageFont

class DateMemeGeneratorInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=500, description="Text or conversation to base meme on")
    vibe: str = Field(default="funny", description="Desired meme vibe (e.g., funny, romantic)")

class DateMemeGenerator(Tool):
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        super().__init__(
            name="date_meme_generator",
            description="Generate a meme based on date or conversation with LLM caption",
            input_schema=DateMemeGeneratorInput
        )
        self.client = Groq(api_key=api_key)
        self.model = model

    async def _llm_caption(self, text: str, vibe: str) -> str:
        prompt = f"""
        Generate a funny meme caption based on this text: {text}
        Vibe: {vibe}
        Keep it short and viral.
        """
        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a meme caption generator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=100
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"LLM caption failed: {str(e)}"))

    def _generate_meme_image(self, caption: str) -> ImageContent:
        img = Image.new("RGB", (400, 200), color="#FFFFFF")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        draw.text((10, 10), caption[:100], fill="#000000", font=font)
        draw.text((10, 150), "#SafeDateMeme", fill="#FF6B6B", font=font)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return ImageContent(
            type="image",
            mimeType="image/png",
            data=base64.b64encode(buf.getvalue()).decode("utf-8")
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated = DateMemeGeneratorInput(**inputs)
        except ValueError as e:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))

        caption = await self._llm_caption(validated.text, validated.vibe)
        meme = self._generate_meme_image(caption)

        return {
            "caption": caption,
            "meme": meme,
            "share_text": f"{caption} 😂 #SafeDateMeme"
        }