import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()


def search_gourmet(lat: float, lng: float, range: int = 3) -> list[dict]:
    print("★ search_gourmet が呼ばれました")
    """指定した緯度・経度の周辺の飲食店を検索する。
    ユーザーが食事・グルメの店を探している場合にこの関数を呼び出すこと。

    Args:
        lat: 検索の中心となる緯度
        lng: 検索の中心となる経度
        range: 検索範囲。1:300m 2:500m 3:1000m 4:2000m 5:3000m

    Returns:
        飲食店のリスト。各要素は name, genre, budget, access, lat, lng, url を含む。
    """
    api_key = os.environ.get("HOTPEPPER_API_KEY")  # ← .envのキー名と完全一致させる
    url = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/"
    params = {
        "key": api_key,
        "lat": lat,
        "lng": lng,
        "range": range,
        "order": 4,
        "count": 3,
        "format": "json",
    }

    response = requests.get(url, params=params)

    data = response.json()

    shops = data["results"]["shop"]
    simplified = []
    for shop in shops:
        simplified.append(
            {
                "name": shop["name"],
                "genre": shop["genre"]["name"],  # ジャンル名
                "budget": shop["budget"]["name"],
                "access": shop["access"],
                "lat": shop["lat"],
                "lng": shop["lng"],
                "url": shop["urls"]["pc"],
            }
        )

    return simplified


result = search_gourmet(lat=34.67, lng=135.52, range=5)
print(json.dumps(result, ensure_ascii=False, indent=2))
