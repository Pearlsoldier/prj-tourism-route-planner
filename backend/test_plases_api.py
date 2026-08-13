import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("PLACES_API_KEY")  # ← .envのキー名と完全一致させる
url = "https://places.googleapis.com/v1/places:searchNearby"

headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": api_key,
    "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.primaryTypeDisplayName,places.editorialSummary,places.regularOpeningHours.weekdayDescriptions",
}

body = {
    "includedTypes": ["restaurant"],
    "maxResultCount": 5,
    "languageCode": "ja",
    "locationRestriction": {
        "circle": {
            "center": {"latitude": 35.003691, "longitude": 135.7785464},
            "radius": 500.0,
        }
    },
}

response = requests.post(url, headers=headers, json=body)

data = response.json()
print(json.dumps(data, indent=2, ensure_ascii=False))
