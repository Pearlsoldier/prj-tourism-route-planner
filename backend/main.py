from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from functions.tools import get_kyoto_locations, search_gourmet, search_nearby_location

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    messages: List[Message]


app = FastAPI()

origins = ["http://localhost:5173"]

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
    contents = []
    for m in request.messages:
        if m.role == "system":
            pass
        elif m.role == "assistant":
            contents.append(types.Content(role="model", parts=[types.Part(text=m.content)]))
        else:  # user
            contents.append(types.Content(role="user", parts=[types.Part(text=m.content)]))
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        
        
        config=types.GenerateContentConfig(
        tools=[get_kyoto_locations, search_gourmet, search_nearby_location],
        system_instruction=(
            "あなたは観光ナビゲーターです。"
        "京都・東山エリアの神社仏閣を周遊するルートを、ユーザーの希望をもとに組み立ててください。"
        "ユーザーが食事や飲食店を希望する場合は、search_gourmet を使って周辺の店を検索して提案してください。"
        "ユーザーが観光施設を探したい場合は、search_nearby_locationを使ってユーザーが気になるジャンルのお店や施設を提案してください。"
        )
    ),
    )
    return {"choices": [{"message": {"content": response.text}}]}
