import math

from functions.tools import (
    geocode_place,
    search_nearby_location,
    get_walking_leg,
    get_place_details,
)


import functools
from models.guidebook import Guidebook
print("[import] wrapped_tools を読み込み開始")

def record_to_guidebook(plan: Guidebook, field: str, mode: str = "once"):
    """Guidebook に記録するデコレータ"""
    print(f"   [1層目] record_to_guidebook 実行 field={field} / mode={mode}")

    def recorder(func):
        print(f"   [2層目] deco 実行 func={func.__name__}")

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"   [3層目] wrapper 実行")
            result = func(*args, **kwargs)

            if "error" in result:
                print(f"   [3層目] スキップ（field={field} / エラー）")
            elif mode == "append":
                if result not in getattr(plan, field):
                    getattr(plan, field).append(result)
                print(f"   [3層目] 追記（field={field} / 件数={len(getattr(plan, field))}）")
            else:
                if getattr(plan, field) is None:
                    setattr(plan, field, result)
                    print(f"   [3層目] 記録（field={field}）")
                else:
                    print(f"   [3層目] スキップ（field={field} / 既存あり）")

            return result
        return wrapper

    return recorder


def make_select_places(plan: Guidebook):
    def select_places(places: list[dict]) -> dict:
        """ユーザーが巡る観光地と順番を確定したら、この関数を呼び出す。

    出発地を先頭に含め、ユーザーが挙げた順にリストへ並べること。
    この順序がそのまま巡り順として扱われる。

    Args:
        places: 巡る地点のリスト。先頭が出発地。
            各要素は name と stay_minutes の2つのキーを持つ辞書にすること。
            name: 地点の名称。search_nearby_location が返した name を
                そのまま使うこと。住所に変えたり省略したりしない。
            stay_minutes: その地点での滞在時間（分）。整数で指定する。
                出発地の stay_minutes は必ず 0 にすること。
            （例: [{"name": "鎌倉駅", "stay_minutes": 0},
                   {"name": "鶴岡八幡宮", "stay_minutes": 45},
                   {"name": "小町通り", "stay_minutes": 60}]）

    Returns:
        登録された巡り順のリストを含む辞書。
    """
        print(f"★ select_places が呼ばれました。 {places}")
        plan.selected = places
        return {"selected": places}
    return select_places

def make_set_start_time(plan: Guidebook):
    def set_start_time(start_time: str) -> dict:
        """ユーザーが観光の開始時刻を指定したら、この関数を呼び出す。

    Args:
        start_time: 観光を始める時刻。"HH:MM" 形式の24時間表記で指定する。
            （例: "09:00", "13:30"）

    Returns:
        登録された開始時刻を含む辞書。
    """
        print(f"★ set_start_time が呼ばれました。 {start_time}")
        plan.start_time = start_time
        return {"start_time": start_time}
    return set_start_time

def make_reorder_places(plan: Guidebook):
    def reorder_places(names: list[str]) -> dict:
        """ユーザーが巡る順番の変更を指示したら、この関数を呼び出す。

        出発地は先頭に固定されており、並べ替えの対象外。
        names に出発地を含めてはいけない。

        Args:
            names: 変更後の巡り順に並べた観光地の名前のリスト。
                出発地を除いた観光地を「すべて」含めること。
                1ヶ所だけ動かす場合も、並べ替え後の全体を渡すこと。
                名前はしおりに記録されているものと完全に一致させること。

        Returns:
            変更後の巡り順。失敗した場合は error を含む辞書。
        """
        print(f"★ reorder_places が呼ばれました。 {names}")

        # 1. 並べ替えられる状態か（起点 + 2ヶ所以上）
        if len(plan.selected) < 3:
            return {"error": "並べ替えの対象となる観光地が2ヶ所ありません。"}

        origin = plan.selected[0]
        others = plan.selected[1:]

        # 2. 起点が混ざっていたら黙って除く
        names = [n for n in names if n != origin["name"]]

        # 3. 検証（plan にはまだ触らない）
        by_name = {place["name"]: place for place in others}

        unknown = [n for n in names if n not in by_name]
        if unknown:
            return {
                "error": f"しおりに無い観光地が含まれています: {unknown}",
                "指定できる観光地": list(by_name),
            }

        if len(names) != len(set(names)):
            return {"error": "同じ観光地が複数回指定されています。"}

        if len(names) != len(others):
            return {
                "error": (
                    f"観光地は{len(others)}ヶ所ありますが、{len(names)}ヶ所しか"
                    f"指定されていません。並べ替え後の全体を渡してください。"
                ),
                "指定できる観光地": list(by_name),
            }

        # 4. 反映
        plan.selected = [origin] + [by_name[n] for n in names]
        plan.legs = []

        print(f"★ 巡り順を変更しました。 {[p['name'] for p in plan.selected]}")
        return {"selected": [p["name"] for p in plan.selected]}

    return reorder_places

"""build_route の実装。

wrapped_tools.py に追記して使う想定。
ファイル先頭の import と定数は、既存の import 群のそばにまとめて置くこと。
"""

# ---------------------------------------------------------------
# 対応表・定数
# ---------------------------------------------------------------

# 自由時間の選択肢（prompts.py の手順3の番号と対応）
# 予算は幅の下限を取る。少なめに組んで余らせるほうが、超過するより安全。
BUDGET_TABLE = {
    1: {"minutes": 180, "max_stops": 3},   # 3〜4時間
    2: {"minutes": 360, "max_stops": 6},   # 6〜8時間
    3: {"minutes": 600, "max_stops": 8},   # 10時間以上
}

# 興味のジャンル（prompts.py の手順4の選択肢と対応）
# Gemini に英語の種別名を選ばせない。ここで一元管理する。
INTEREST_TABLE = {
    # tourist_attraction は入れない。
    # 観光客が行く場所すべてに付く広すぎる分類で、
    # 「歴史・文化」を選んだのにフードホールが出た（2026-09-05 実測、旧軸での話）。
    "史跡": ["historical_place", "historical_landmark", "monument", "castle"],
    "神社仏閣": ["shinto_shrine", "buddhist_temple"],
    "アート": ["art_museum", "art_gallery", "art_studio", "sculpture"],
    "博物館": ["museum", "history_museum", "visitor_center"],
    "庭園": ["garden", "botanical_garden", "city_park"],
}

STAY_MINUTES = 60        # 各地点の滞在時間（起点は 0）
SEARCH_RADIUS = 1500.0   # search_nearby_location に渡す半径（m）
NEARBY_LIMIT_KM = 1.5    # 現在地からこの距離までを「歩ける範囲」とみなす
MIN_SPOT_DISTANCE_M = 150.0  # これより近い候補は同一施設の構成要素とみなして除外
SPOT_GROUP_DISTANCE_M = 300.0  # 1回の検索結果の中で、これ以内の候補は同一施設とみなしてグループ化する


# ---------------------------------------------------------------
# 補助関数
# ---------------------------------------------------------------

def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """2点間の直線距離（km）。Haversine の公式。

    実際の徒歩距離は get_walking_leg で測る。
    ここでは候補を絞り込むためだけに使う（API を呼ぶ回数を減らす目的）。
    """
    earth_radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * earth_radius_km * math.asin(math.sqrt(a))


def _add_minutes(hhmm: str, minutes: int) -> str:
    """"HH:MM" に分を足して "HH:MM" で返す。"""
    hour, minute = map(int, hhmm.split(":"))
    total = hour * 60 + minute + minutes
    return f"{(total // 60) % 24:02d}:{total % 60:02d}"


def _types_from_interests(interests: list[str]) -> list[str]:
    """日本語のジャンル名を Places API の種別名に変換する。

    重複は取り除き、渡された順序は保つ。
    """
    types: list[str] = []
    for name in interests:
        for t in INTEREST_TABLE.get(name, []):
            if t not in types:
                types.append(t)
    return types


# INTEREST_TABLE の逆引き（type -> ジャンル名）。ベタ書きせず動的に作る。
_TYPE_TO_INTEREST = {
    t: genre for genre, types in INTEREST_TABLE.items() for t in types
}


def _interest_of_type(type_name: str | None) -> str | None:
    """Places API の primary_type から、対応する興味ジャンル名を引く。

    該当なしの場合は None を返す。
    """
    return _TYPE_TO_INTEREST.get(type_name)


def _dedupe_by_area(candidates: list[dict]) -> list[dict]:
    """近接する候補を同一施設の構成要素とみなしてグループ化し、代表1件に集約する。

    1件目を起点に SPOT_GROUP_DISTANCE_M 以内の候補を集めてグループとし、
    残りに対して同じことを繰り返す単純な方法（候補は最大20件なので総当たりで十分）。
    各グループの代表は user_rating_count が最大の候補。同点の場合は
    元のリストで先に出現したものを採る。戻り値は元の並び順を保つ。
    """
    remaining = list(enumerate(candidates))
    groups: list[list[tuple[int, dict]]] = []

    while remaining:
        seed_idx, seed = remaining.pop(0)
        group = [(seed_idx, seed)]
        rest = []
        for idx, cand in remaining:
            dist_m = _distance_km(
                seed["lat"], seed["lng"], cand["lat"], cand["lng"]
            ) * 1000
            if dist_m <= SPOT_GROUP_DISTANCE_M:
                group.append((idx, cand))
            else:
                rest.append((idx, cand))
        remaining = rest
        groups.append(group)

    representatives: list[tuple[int, dict]] = []
    for group in groups:
        rep_idx, rep = max(group, key=lambda pair: pair[1].get("user_rating_count", 0))
        representatives.append((rep_idx, rep))
        if len(group) > 1:
            print(
                f"★ 同一施設としてグループ化: "
                f"{[c['name'] for _, c in group]} → 代表「{rep['name']}」"
            )

    representatives.sort(key=lambda pair: pair[0])
    return [rep for _, rep in representatives]


# ---------------------------------------------------------------
# 本体
# ---------------------------------------------------------------

def make_build_route(plan, fetch_details):
    """build_route を作って返す。

    Args:
        plan: 記録先の Guidebook。
        fetch_details: place_id を受け取って口コミ・要約を返す関数。
            main.py の fetch_details_cached を渡すこと。
            tools.get_place_details を直接渡すとキャッシュが効かず、
            同じ場所に何度も課金される。
    """
    def build_route(
        origin: str,
        start_time: str,
        budget_choice: int,
        interests: list[str],
    ) -> dict:
        """ヒアリングした4項目をもとに、徒歩の観光ルートを組み立てる。

        起点・開始時刻・自由時間・興味のジャンルがすべて揃ってから呼び出すこと。
        1つでも欠けている場合は呼び出してはいけない。

        経由地の選定・順番・所要時間の計算はすべてこの関数の内部で行う。
        戻り値の時刻や距離をあなたが計算し直す必要はない。

        Args:
            origin: 起点にする駅名または施設名（例：広島駅）
            start_time: 歩き始める時刻。"HH:MM" 形式の24時間表記（例："09:00"）
            budget_choice: 自由時間の選択肢の番号。
                1 = 3〜4時間、2 = 6〜8時間、3 = 10時間以上。
                分に変換せず、番号のまま整数で渡すこと。
            interests: 興味のあるジャンル名の日本語のリスト。
                「史跡」「神社仏閣」「アート」「博物館」「庭園」のいずれかを含めること。
                （例：["史跡", "神社仏閣"]）

        Returns:
            start_time, end_time, total_minutes, stops, legs を含む辞書。
            stops の各要素は name, arrival_time, departure_time, stay_minutes,
            address, description, summary, opening_hours を持つ。
            失敗した場合は error を含む辞書。
        """
        print(f"★ build_route が呼ばれました。 {origin} / {start_time} / "
              f"choice={budget_choice} / {interests}")

        # --- 引数の検証 ---
        try:
            budget = BUDGET_TABLE[int(budget_choice)]
        except (KeyError, ValueError, TypeError):
            return {"error": "自由時間の選択肢は 1・2・3 のいずれかを整数で渡してください。"}

        types = _types_from_interests(interests)
        if not types:
            return {
                "error": "ジャンルが判別できませんでした。",
                "指定できるジャンル": list(INTEREST_TABLE),
            }

        # --- 起点の座標を取る ---
        geo = geocode_place(origin)
        if "error" in geo:
            return geo

        # --- 起点をしおりの1件目に置く ---
        stops = [{
            "name": origin,
            "lat": geo["lat"],
            "lng": geo["lng"],
            "address": geo["address"],
            "arrival_time": start_time,
            "departure_time": start_time,
            "stay_minutes": 0,
        }]
        legs: list[dict] = []
        visited = {origin}

        used_minutes = 0
        clock = start_time
        current = stops[0]
        genres_covered: set[str] = set()

        # --- 数珠つなぎで経由地を足していく ---
        while len(stops) - 1 < budget["max_stops"]:
            candidates = search_nearby_location(
                current["lat"], current["lng"], types, SEARCH_RADIUS
            )
            if not candidates or "error" in candidates[0]:
                print("   [build_route] 候補が取得できないため打ち切り")
                break

            candidates = _dedupe_by_area(candidates)

            # 直線距離で絞る。訪問済みは除く。
            nearby = []
            for cand in candidates:
                if cand["name"] in visited:
                    continue

                # 採用済みの全地点（起点を含む）に近すぎる候補は、
                # 同一施設の構成要素（チケット売り場・橋など）とみなして除く。
                too_close = False
                for stop in stops:
                    dist_m = _distance_km(
                        stop["lat"], stop["lng"], cand["lat"], cand["lng"]
                    ) * 1000
                    if dist_m <= MIN_SPOT_DISTANCE_M:
                        print(
                            f"★ 候補除外: {cand['name']}（{stop['name']} から "
                            f"{dist_m:.0f}m、同一施設の構成要素とみなす）"
                        )
                        too_close = True
                        break
                if too_close:
                    continue

                km = _distance_km(
                    current["lat"], current["lng"], cand["lat"], cand["lng"]
                )
                if km <= NEARBY_LIMIT_KM:
                    nearby.append((km, cand))

            if not nearby:
                print("   [build_route] 歩ける範囲に未訪問の候補なし。打ち切り")
                break

            # 近い順に見て、予算に収まる1件を採る
            nearby.sort(key=lambda pair: pair[0])

            # ジャンル枠: まだ1件も採用していないジャンルがあれば優先する
            remaining_genres = [g for g in interests if g not in genres_covered]
            pool = nearby
            quota_genre = None
            if remaining_genres:
                for g in remaining_genres:
                    genre_pool = [
                        pair for pair in nearby
                        if _interest_of_type(pair[1].get("primary_type")) == g
                    ]
                    if genre_pool:
                        pool = genre_pool
                        quota_genre = g
                        break
                else:
                    print(
                        f"   [build_route] 未充足ジャンル {remaining_genres} の候補が"
                        f"範囲内に無いためスキップ。通常ロジックで選ぶ"
                    )

            picked = None
            budget_over = False

            for _, cand in pool:
                leg = get_walking_leg(current["name"], cand["name"])
                if "error" in leg:
                    continue  # この候補は測れない。次を試す

                cost = leg["duration_min"] + STAY_MINUTES
                if used_minutes + cost > budget["minutes"]:
                    # 近い順に見ているので、これで超えるなら残りも超える
                    budget_over = True
                    break

                picked = (cand, leg, cost)
                break

            if budget_over:
                print(f"   [build_route] 予算 {budget['minutes']}分 に収まらないため打ち切り")
                break
            if picked is None:
                print("   [build_route] 採用できる候補がないため打ち切り")
                break

            cand, leg, cost = picked

            if quota_genre:
                print(f"★ ジャンル枠「{quota_genre}」から採用: {cand['name']}")
                genres_covered.add(quota_genre)
                if all(g in genres_covered for g in interests):
                    print("★ 全ジャンルの枠が埋まりました。以降は通常ロジックで選びます")

            arrival = _add_minutes(clock, leg["duration_min"])
            departure = _add_minutes(arrival, STAY_MINUTES)

            stops.append({
                "name": cand["name"],
                "place_id": cand["place_id"],
                "lat": cand["lat"],
                "lng": cand["lng"],
                "address": cand["address"],
                "type": cand.get("type"),
                "description": cand.get("description"),
                "opening_hours": cand.get("opening_hours"),
                "arrival_time": arrival,
                "departure_time": departure,
                "stay_minutes": STAY_MINUTES,
            })
            legs.append({
                "from": current["name"],
                "to": cand["name"],
                "distance_m": leg["distance_m"],
                "duration_min": leg["duration_min"],
            })

            visited.add(cand["name"])
            used_minutes += cost
            clock = departure
            current = stops[-1]

        if len(stops) == 1:
            return {"error": "条件に合う観光地が見つかりませんでした。"
                             "起点やジャンルを変えて試してください。"}

        # --- 確定した地点だけ口コミを取りに行く ---
        # 絞り込みの前に呼ぶと、捨てる候補にも課金される（2026-07-29 の方針）
        for stop in stops[1:]:
            details = fetch_details(stop["place_id"])
            if "error" not in details:
                stop["summary"] = details.get("summary")
                stop["reviews"] = details.get("reviews")

        # --- しおりに記録する ---
        plan.origin = stops[0]
        plan.selected = stops
        plan.legs = legs
        plan.start_time = start_time

        result = {
            "start_time": start_time,
            "end_time": clock,
            "total_minutes": used_minutes,
            "budget_minutes": budget["minutes"],
            "stops": stops,
            "legs": legs,
        }
        print(f"★ ルートを組みました。 {[s['name'] for s in stops]} / "
              f"{used_minutes}分（予算 {budget['minutes']}分）")
        return result

    return build_route