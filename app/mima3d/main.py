import time

from typing import Annotated
from fastapi import FastAPI, File, UploadFile

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from dotenv import load_dotenv
import os
load_dotenv()

# Working setup for openai calls. Don't forget .env in FastAPI root.
openai_provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
model = OpenAIModel(model_name="gpt-4o", provider=openai_provider)
agent = Agent(model)
   
app = FastAPI()

# http://triathlon.itit.gu.se:8001 eller
# http://localhost:8001
@app.get("/")
async def root():
    result = await agent.run('What it the capital of Sweden?')  
    return {"answer": result.output}

@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    return {"file_size": len(file)}

# Upload pov-image (assumes png) as obs
@app.post("/obs/")
async def uploadfile(file: UploadFile):
    try:        
        timestamp = time.strftime('%Y-%m-%d-%H.%M')
        filename = timestamp + ".png"
        file_path = f"obs/{filename}"    
        with open(file_path, "wb") as f:
            f.write(file.file.read())
            return {"message": "File saved successfully"}
    except Exception as e:
        print("message:", e.args)
        