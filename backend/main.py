from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from models.guidebook import Guidebook
import hashlib
from functions.wrapped_tools import make_build_route
import functions.tools
from prompts import build_system_instruction

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
ACCESS_KEYS = {
    os.environ["ACCESS_KEY_OWNER"]: "owner",
    os.environ["ACCESS_KEY_REVIEWER"]: "reviewer",
}

print("[main] 開始")


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    messages: List[Message]


def verify_token(authorization: str | None = Header(None)) -> str:
    """Authorization ヘッダーのアクセスキーを照合し、持ち主の名前を返す。"""
    if authorization is None:
        print("★ 認証失敗: Authorization ヘッダーなし")
        raise HTTPException(status_code=401, detail="アクセスキーが正しくありません。設定画面でアクセスキーを入力してください。")

    if not authorization.startswith("Bearer "):
        print("★ 認証失敗: 形式が不正")
        raise HTTPException(status_code=401, detail="アクセスキーが正しくありません。設定画面でアクセスキーを入力してください。")

    token = authorization[len("Bearer "):]
    who = ACCESS_KEYS.get(token)

    if who is None:
        print("★ 認証失敗: 未登録のアクセスキー")
        raise HTTPException(status_code=401, detail="アクセスキーが正しくありません。設定画面でアクセスキーを入力してください。")

    print(f"★ 認証OK: {who}")
    return who

app = FastAPI()

origins = ["http://localhost:5173", "https://prj-tourism-route-planner.vercel.app"]
sessions = {}
place_cache: dict[str, dict] = {}
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def fetch_details_cached(place_id: str) -> dict:
    """place_cache を先に見る。無ければ取りに行って入れる。

    ラッパーの外側に置くのは、既存のラッパーが「元の関数を実行した後」に動くため。
    実行後に判定してもリクエストは飛んでいる（8/13 の not in ガードと同じ構図）。
    キャッシュは呼ぶ前に止めないと課金が止まらない。
    """
    if place_id in place_cache:
        print(f"★ cache HIT  {place_id}")
        return place_cache[place_id]

    print(f"★ cache MISS {place_id} → Place Details 発行")
    details = functions.tools.get_place_details(place_id)
    if "error" not in details:
        place_cache[place_id] = details   # 失敗をキャッシュしない
    return details

@app.get("/")
async def hello():
    return {"message": "Hello,World"}


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, who: str = Depends(verify_token)):
    # user が 0 件のリクエストは想定していない（IndexError で落ちる）
    user_messages = [m.content for m in request.messages if m.role == "user"]
    # 第一声が同じ会話は同じしおりを共有する（実測済み）
    # 本番ではフロントに会話IDを持たせる
    session_key = hashlib.sha256(user_messages[0].encode()).hexdigest()
    print(session_key)

    plan = sessions.setdefault(session_key, Guidebook())
    # Gemini に見せるツールは build_route ひとつだけ。
    # geocode や get_walking_leg を個別に登録すると、Gemini がそれらを
    # 単独で呼び始め、ルートの組み立てが会話の外に漏れる。
    build_route = make_build_route(plan, fetch_details_cached)
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
            tools=[build_route],
            system_instruction=build_system_instruction(plan),
            ),
        )
    print(plan, plan.missing_fields())

    text = response.text
    if text is None:
        print("★ 応答テキストが空でした")
        text = ""

    # 表（timeline）の追記はしない。
    # build_route が時刻まで確定させ、Gemini がそれを文章で案内するため、
    # 表を足すと同じ内容が二重に出る（2026-09-05 の判断）。

    return {"choices": [{"message": {"content": text}}]}