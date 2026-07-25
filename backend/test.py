import os
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.environ.get("PLACES_API_KEY")


# エンドポイント：https://routes.googleapis.com/directions/v2:computeRoutes
# メソッド：POST
# ヘッダー：X-Goog-Api-Key と X-Goog-FieldMask
# ボディに origin / destination / travelMode: "TRANSIT"


url = "https://routes.googleapis.com/directions/v2:computeRoutes"

headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": api_key,          # ← どの変数を入れる？
    "X-Goog-FieldMask": "*",        # ← デバッグ中は "*" が楽
}

body = {
    "origin": { "address": "京都駅" },
    "destination": { "address": "清水寺" },
    "departureTime": "2026-07-25T01:00:00Z",
    "travelMode": "WALK",
    "languageCode": "ja",
    "units": "METRIC",
}

response = requests.post(url, headers=headers, json=body)

print(response.status_code)   # まず番号を見る（curlの -i と同じ役割）
print(response.json())        # 中身を見る