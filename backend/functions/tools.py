import os
import requests
import math 

print("[import] tools を読み込み")


def search_nearby_location(lat: float, lng: float, types: list[str], radius: float = 1000.0):
    """指定した緯度・経度の周辺の施設を検索する。
        ユーザーが観光地や名所を探している場合にこの関数を呼び出すこと。
        Args:
            lat: 検索の中心となる緯度
            lng: 検索の中心となる経度
            radius: 検索範囲（メートル）。ユーザーの希望や移動手段に応じて決める。
                    徒歩で狭く巡る場合は 1000、駅周辺を広く見る場合は 3000、
                    市内全域なら 5000 程度を目安にする。最大 50000。
            types: 検索したい施設カテゴリのリスト。用途に応じて以下から選択する。
                - 観光・文化: museum, art_gallery, historical_place, cultural_landmark,
                    monument, tourist_attraction, park, historical_landmark
                - 宗教施設: shinto_shrine（神社）, buddhist_temple（仏閣）, church
                - 買い物: shopping_mall, gift_shop, market
        Returns:
            観光地のリスト。各要素は name, address, lat, lng, type, description, opening_hoursを含む。
    """
    print("★ search_nearby_location が呼ばれました")
    print(f"radius: {radius} mです。")
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY") 
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.primaryTypeDisplayName,places.editorialSummary,places.regularOpeningHours.weekdayDescriptions",
        }

    body = {
        "includedTypes": types,
        "maxResultCount": 5,
        "languageCode": "ja", 
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lng
                },
                "radius": radius
            }
        }
    }

    response = requests.post(url, headers=headers, json=body)
    status = response.status_code
    if 200 != status:
        return [{"error": f"エラーコード{status}: 正常に取得できませんでした。"}]
    
    data = response.json() 
    if not data.get("places"):
        return [{"error": "placesが空です。正常に取得できませんでした。"}]

    simplified = []
    for place in data["places"]:
        simplified.append({
            # place_id はラッパーが get_place_details に渡すためのもの。
            # docstring に書かない＝Gemini には見せない。
            "place_id": place["id"],
            "name": place["displayName"]["text"],
            "address": place["formattedAddress"],
            "lat": place["location"]["latitude"],
            "lng": place["location"]["longitude"],
            "type": place.get("primaryTypeDisplayName", {}).get("text"),
            "description": place.get("editorialSummary", {}).get("text"),
            "opening_hours": place.get("regularOpeningHours", {}).get("weekdayDescriptions"),
        })
    print(f"★ 返した候補: {[(p['name'], p['place_id']) for p in simplified]}") 
    return simplified

def geocode_place(place_name: str) -> dict:
    """住所や地名から緯度経度を取得する。
    緯度経度が必要なときに、このAPIを使用すること

    Args:
        place_name: 必要な施設名、住所のテキストデータ

    Returns:住所データ、緯度（lat）, 経度（lng）の辞書型データ

    """
    print("★ geocode_place が呼ばれました")
    print(f"★ geocode_place: '{place_name}'") 
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    result = requests.get(url, params={"address":f"{place_name}", "key": api_key, "language": "ja"})
    low_place = result.json()
    status = low_place["status"]
    if status != "OK":
        print(f"★ geocode_place 失敗: {status}")
        if status == "ZERO_RESULTS":
            return {"error": "ジオコードは成功したものの結果が返されませんでした。実在しない address が渡された場合に発生することがあります。"}
        elif status == "OVER_DAILY_LIMIT":
            return {"error": "設定した使用量の上限を超えている可能性があります。"}
        elif status == "REQUEST_DENIED":
            return {"error": "リクエストが拒否されました。"}
        elif status == "INVALID_REQUEST":
            return {"error": "クエリ（address、components、latlng）が不足しています。"}
        elif status == "UNKNOWN_ERROR":
            return {"error": "サーバーエラーでリクエストが処理できませんでした。再度リクエストすると、成功する可能性があります。"}
        else:
            return {"error": f"予期しないエラーが発生しました（{status}）"}
    address = low_place["results"][0]['formatted_address']
    location =  low_place["results"][0]['geometry']['location']
    return {"address": address, "lat": location["lat"], "lng": location["lng"]}

def get_walking_leg(travel_origin: str, destination: str) -> dict:
    """2地点間の徒歩での移動距離と所要時間を取得する。

    Args:
        travel_origin: 出発地の施設名または住所（例：鶴岡八幡宮）
        destination: 到着地の施設名または住所（例：長谷寺）

    Returns:
        travel_origin, destination, distance_m（距離・メートル）、
        duration_min（所要時間・分。秒から切り上げ）を含む辞書。
    """
    print(f"★ get_walking_leg が呼ばれました。 {travel_origin} → {destination}")
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": api_key,    
    "X-Goog-FieldMask": "routes.duration,routes.distanceMeters",
    }

    body = {
        "origin": {"address": travel_origin},
        "destination": {"address": destination},
        "travelMode": "WALK",
        "languageCode": "ja",
        "units": "METRIC",
    }

    response = requests.post(url, headers=headers, json=body)
    status = response.status_code
    if 200 != status:
        return {"error": f"エラーコード{status}: 正常に取得できませんでした。"}

    data = response.json() 
    if not data.get("routes"):
        return {"error": "routesが空です。正常に取得できませんでした。"}
    if not data["routes"][0]:
        return {"error": "正常に取得できませんでした。"}
    

    leg = data["routes"][0]
    distance = leg["distanceMeters"]
    duration_sec = int(leg["duration"][:-1])
    duration_min = math.ceil(duration_sec / 60)
    return {
        "travel_origin": travel_origin,
        "destination": destination,
        "distance_m": distance,
        "duration_min": duration_min,
    }

def get_place_details(place_id: str) -> dict:
    """place_id から口コミと要約を取得する。

    Gemini には登録しない。main.py のラッパーがコードから呼ぶ。
    Place Details のフィールドマスクは prefix なし。
    search_nearby_location（"places." が付く）とは記法が違うので使い回さない。

    Args:
        place_id: search_nearby_location が返した place_id

    Returns:
        summary（Googleの要約）、reviews（口コミ本文のリスト・最大5件）を含む辞書。
        失敗時は {"error": ...}。例外は投げない。
    """
    print(f"★ get_place_details が呼ばれました。 {place_id}")
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    url = f"https://places.googleapis.com/v1/places/{place_id}"
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "displayName,reviewSummary,reviews",
    }
    params = {"languageCode": "ja", "regionCode": "JP"}

    response = requests.get(url, headers=headers, params=params)
    status = response.status_code
    if status != 200:
        # Google が返すエラー本文を捨てない（原因の切り分けに要る）
        print(f"★ get_place_details 失敗 {status}: {response.text[:200]}")
        return {"error": f"エラーコード{status}: 正常に取得できませんでした。"}

    data = response.json()

    reviews = []
    for r in data.get("reviews", []):
        text = (r.get("text") or r.get("originalText") or {}).get("text", "")
        if text:
            reviews.append(text.strip())

    return {
        "name": data.get("displayName", {}).get("text"),
        "summary": ((data.get("reviewSummary") or {}).get("text") or {}).get("text"),
        "reviews": reviews,
    }




