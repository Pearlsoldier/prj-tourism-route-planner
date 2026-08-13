from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from models.guidebook import Guidebook
import hashlib
from functions.wraped_tools import record_to_guidebook, make_select_places
import functions.tools
from timeline import build_timeline, format_timeline_markdown
from prompts import build_system_instruction

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)


print("[main] 開始")


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    messages: List[Message]


app = FastAPI()

origins = ["http://localhost:5173", "https://prj-tourism-route-planner.vercel.app"]
sessions = {}
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def hello():
    return {"message": "Hello,World"}


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    # user が 0 件のリクエストは想定していない（IndexError で落ちる）
    user_messages = [m.content for m in request.messages if m.role == "user"]
    # 第一声が同じ会話は同じしおりを共有する（実測済み）
    # 本番ではフロントに会話IDを持たせる
    session_key = hashlib.sha256(user_messages[0].encode()).hexdigest()
    print(session_key)

    plan = sessions.setdefault(session_key, Guidebook())
    recorder_origin = record_to_guidebook(plan, "origin")
    geocode_place_w = recorder_origin(functions.tools.geocode_place)
    recorder_legs = record_to_guidebook(plan, "legs", "append")
    get_walking_leg_w = recorder_legs(functions.tools.get_walking_leg)
    select_places = make_select_places(plan)
    import inspect
    print(inspect.signature(geocode_place_w))
    print(geocode_place_w.__doc__)
    contents = []
    for m in request.messages:
        if m.role == "system":
            pass
        elif m.role == "assistant":
            contents.append(
                types.Content(role="model", parts=[types.Part(text=m.content)])
            )
        else:  # user
            contents.append(
                types.Content(role="user", parts=[types.Part(text=m.content)])
            )

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=contents,
        config=types.GenerateContentConfig(
            tools=[
                geocode_place_w,
                get_walking_leg_w,
                select_places,
                functions.tools.search_gourmet,
                functions.tools.search_nearby_location,
                ],
            system_instruction=(build_system_instruction(plan)
            ),
        ),
    )
    print(plan, plan.missing_fields())

    text = response.text
    if plan.is_ready():
        timeline = build_timeline(plan.selected, plan.legs)
        text += "\n\n" + format_timeline_markdown(timeline)

    return {"choices": [{"message": {"content": text}}]}
