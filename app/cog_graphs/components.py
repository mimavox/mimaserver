import os

from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv

load_dotenv()

openai_provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
model = OpenAIModel(model_name="gpt-5", provider=openai_provider)
agent = Agent(model)

def text_to_image(text):
    image = text + "image"
    return image

async def image_to_text(img_path):    
    with open(img_path, "rb") as f:
        data = f.read()
    result = await agent.run([
        "Describe this image",
        BinaryContent(data=data, media_type="image/png"),
    ])
    return result

modules = {
    "TtI": ("Converts text to image", "str", "img", text_to_image),
    "ItT": ("Converts image to text", "img", "str", image_to_text)
}
