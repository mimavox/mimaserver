import os
from typing import Optional

from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Provide it via .env or environment.")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")

_agent: Optional[Agent] = None

def get_agent() -> Agent:
    global _agent
    if _agent is None:
        provider = OpenAIProvider(api_key=OPENAI_API_KEY)
        model = OpenAIModel(model_name=OPENAI_MODEL, provider=provider)
        _agent = Agent(model)
    return _agent

# ------------ Modules ------------

def text_to_image(text: str) -> str:
    image = text + "image"
    return image

async def image_to_text(img_path: str) -> str:
    with open(img_path, "rb") as f:
        data = f.read()
    result = await get_agent().run([
        "Describe this image",
        BinaryContent(data=data, media_type="image/png"),
    ])
    return result.output


modules = {
    "TtI": ("Converts text to image", "str", "img", text_to_image),
    "ItT": ("Converts image to text", "img", "str", image_to_text),
}
