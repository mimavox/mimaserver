import time
import glob
import os

from fastapi import FastAPI, UploadFile, HTTPException
from pyvis.network import Network
import components
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv

from actions import *

load_dotenv()

openai_provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
model = OpenAIModel(model_name="gpt-5", provider=openai_provider)  # ensure this model exists
agent = Agent(model)

# Get latest OBS
def latest_obs_on_file() -> str:
    list_of_files = glob.glob("./obs/*")
    if not list_of_files:
        raise FileNotFoundError("No files in ./obs")
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file


# Upload OBS to LLM
async def obs_upload():
    try:
        path = latest_obs_on_file()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    with open(path, "rb") as f:
        data = f.read()

    result = await agent.run([
        "Describe this image",
        BinaryContent(data=data, media_type="image/png"),
    ])
    return result

app = FastAPI()
'''
we
'''

# Test
@app.get("/", response_model=Actions)
async def root():
    response = Actions()
    response.right = True
    return response

# Get all available modules for the UI
@app.get("/available-modules")
async def available_modules():
    pass

# Update cog_model according ti UI modeling
@app.post("/update-model")
async def update_model():
    pass

# Send current POV and run the model with incoming POV as OBS
@app.post("/run-model")
async def run_model():
    pass




# DEPRECEATED:
# Test
@app.get("/llm")
async def llm():
    result = await agent.run("What is the capital of Sweden?")
    return {"answer": result.output}

# Send latest OBS to LLM for description
@app.get("/send")
async def send():
    result = await obs_upload()
    return {"answer": result.output}

# Get POV and save it as obs
@app.post("/obs")
async def uploadfile(file: UploadFile):
    try:
        os.makedirs("obs", exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d_%H.%M")
        file_path = f"obs/{timestamp}.png"
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        return {"message": "obs saved successfully"}
    except Exception as e:
        print("message:", e.args)
        return {"message": "failed to save obs"}

