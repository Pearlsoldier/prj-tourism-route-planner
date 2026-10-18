import pytest

from functions.plan_payload import to_plan
from models.guidebook import Guidebook

# ── 入力：build_route が Guidebook に書き込むのと同じ形 ──

# スタート地点（selected[0] / origin）
start = {
    "name": "広島駅",
    "lat": 34.3972, "lng": 132.4753,
    "address": "広島県広島市南区松原町",
    "arrival_time": "10:00",
    "departure_time": "10:00",
    "stay_minutes": 0,
}

# 目的地1（selected[1]）
dest1 = {
    "name": "原爆ドーム",
    "place_id": "dummy-dome",
    "lat": 34.3955, "lng": 132.4536,
    "address": "広島県広島市中区大手町1丁目",
    "type": "historical_landmark",
    "description": "世界遺産",
    "opening_hours": None,
    "summary": "ダミーの要約",
    "reviews": ["ダミーの口コミ"],
    "arrival_time": "10:30", "departure_time": "11:30", "stay_minutes": 60,
}

# 目的地2（selected[2]）
dest2 = {
    "name": "平和記念資料館",
    "place_id": "dummy-museum",
    "lat": 34.3915, "lng": 132.4525,
    "address": "広島県広島市中区中島町1-2",
    "type": "museum",
    "description": "原爆の資料を展示",
    "opening_hours": None,
    "summary": "ダミーの要約",
    "reviews": ["ダミーの口コミ"],
    "arrival_time": "11:40", "departure_time": "12:40", "stay_minutes": 60,
}

# 移動（legs）
leg1 = {"from": "広島駅", "to": "原爆ドーム", "distance_m": 2100, "duration_min": 30}
leg2 = {"from": "原爆ドーム", "to": "平和記念資料館", "distance_m": 700, "duration_min": 10}


EXPECTED = {
    "origin": {
        "place": {"name": "広島駅", "lat": 34.3972, "lng": 132.4753},
        "departure_time": "10:00",
    },
    "visits": [
        {
            "place": {"name": "原爆ドーム", "lat": 34.3955, "lng": 132.4536},
            "arrival_time": "10:30", "stay_minutes": 60, "departure_time": "11:30",
            "travel": {"distance_m": 2100, "duration_min": 30, "mode": "walk"},
        },
        {
            "place": {"name": "平和記念資料館", "lat": 34.3915, "lng": 132.4525},
            "arrival_time": "11:40", "stay_minutes": 60, "departure_time": "12:40",
            "travel": {"distance_m": 700, "duration_min": 10, "mode": "walk"},
        },
    ],
}



def test_none_gb():
    gb = Guidebook()
    test_plan = to_plan(gb)
    assert test_plan is None

def test_to_plan_same_EXPECTED():
    gb = Guidebook(origin=start, selected=[start, dest1, dest2], legs=[leg1,leg2], start_time="10:00")
    test_plan = to_plan(gb)
    assert test_plan == EXPECTED

def test_none_legs():
    gb = Guidebook(origin=start, selected=[start, dest1, dest2], legs=[leg1], start_time="10:00")
    test_plan = to_plan(gb)
    assert test_plan is None