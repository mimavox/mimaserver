from fastapi import FastAPI

description = """
Mimaserver - Gymnasium lets you train agents.

## Agents

You can **train agents**.

"""

app = FastAPI(
    title="Mimaserver - Gymnasium",
    description=description,
    summary="Training of agents",
    version="0.0.1",
    terms_of_service="",
    contact={
        "name": "Andreas Chatzopoulos",
        "url": "http://minadress",
        "email": "andreas.chatzopoulos@gmail.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


# grocery_list : dict[int, ItemPayload] = {}


# http://triathlon.itit.gu.se:8001/gymnasium
@app.get("/mima2d")
async def root():
    return {"message": "Hello mima2d"}

