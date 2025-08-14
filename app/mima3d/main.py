import time
import glob

from fastapi import FastAPI, UploadFile

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from dotenv import load_dotenv
import os
load_dotenv()

from actions import *

# Working setup for openai calls. Don't forget .env in FastAPI root.
openai_provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
model = OpenAIModel(model_name="gpt-4o", provider=openai_provider)
agent = Agent(model)

# Get the filename of the latest file in /obs
def latest_obs_on_file() -> str:
    list_of_files = glob.glob("./obs/*")
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file
   
app = FastAPI()

# http://triathlon.itit.gu.se:8001 eller
# http://localhost:8001

# Test
@app.get("/", response_model=Actions)
async def root():
    response = Actions()
    response.right = True
    return response

# Send POV to LLM for description
@app.get("/llm")
async def llm():
    result = await agent.run('What it the capital of Sweden?')  
    return {"answer": result.output}

# Upload POV-image (assumes png) as OBS
@app.post("/obs")
async def uploadfile(file: UploadFile):
    try:        
        timestamp = time.strftime('%Y-%m-%d_%H.%M')
        filename = timestamp + ".png"
        file_path = f"obs/{filename}"    
        with open(file_path, "wb") as f:
            f.write(file.file.read())
            return {"message": "obs saved successfully"}
    except Exception as e:
        print("message:", e.args)