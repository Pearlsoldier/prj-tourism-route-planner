import os
import requests

def search_gourmet(lat: float, lng: float, range: int = 3) -> list[dict]:
    """指定した緯度・経度の周辺の飲食店を検索する。
    ユーザーが食事・グルメの店を探している場合にこの関数を呼び出すこと。

    Args:
        lat: 検索の中心となる緯度
        lng: 検索の中心となる経度
        range: 検索範囲。1:300m 2:500m 3:1000m 4:2000m 5:3000m

    Returns:
        飲食店のリスト。各要素は name, genre, budget, access, lat, lng, url を含む。
    """
    print("★ search_gourmet が呼ばれました")
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

def search_nearby_location(lat: float, lng: float, radius: float, types: list[str]):
    """指定した緯度・経度の周辺の施設を検索する。
    ユーザーが食事・グルメの店、施設など座標で求められる施設を探している場合にこの関数を呼び出すこと。

    Args:
        lat: 検索の中心となる緯度
        lng: 検索の中心となる経度
        radius: 検索範囲。100.0m, 200.0m
        types: 検索したい施設カテゴリのリスト。用途に応じて以下から選択する。
            - 観光・文化: museum, art_gallery, historical_place, cultural_landmark,
                monument, tourist_attraction, park, historical_landmark
            - 宗教施設: shinto_shrine（神社）, buddhist_temple（仏閣）, church
            - 買い物: shopping_mall, gift_shop, market
    Returns:
        観光地のリスト。各要素は name, address, lat, lng, type, description, opening_hoursを含む。
        
    """
    print("★ search_nearby_location が呼ばれました")
    api_key = os.environ.get("PLACES_API_KEY") 
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.primaryTypeDisplayName,places.editorialSummary,places.regularOpeningHours.weekdayDescriptions", 
        }

    body = {
        "includedTypes": types,
        "maxResultCount": 3,
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

    data = response.json()

    simplified = []
    for place in data["places"]:
        simplified.append({
            "name": place["displayName"]["text"],
            "address": place["formattedAddress"],
            "lat": place["location"]["latitude"],
            "lng": place["location"]["longitude"],
            "type": place.get("primaryTypeDisplayName", {}).get("text"),
            "description": place.get("editorialSummary", {}).get("text"),
            "opening_hours": place.get("regularOpeningHours", {}).get("weekdayDescriptions"),
        })
    return simplified

def geocode_place(place_name: str) -> dict:
    """住所や地名から緯度経度を取得する。
    緯度経度が必要なときに、このAPIを使用すること

    Args:
        place_name: 必要な施設名、住所のテキストデータ

    Returns:住所データ、緯度（lat）, 経度（lng）の辞書型データ

    """
    print("★ geocode_place が呼ばれました")
    api_key = os.environ.get("PLACES_API_KEY")
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    result = requests.get(url, params={"address":f"{place_name}", "key": api_key, "language": "ja"})
    low_place = result.json()
    status = low_place["status"]
    if status != "OK":
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