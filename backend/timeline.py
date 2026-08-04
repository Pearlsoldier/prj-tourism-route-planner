from datetime import datetime, timedelta

STAY_SECONDS = 3600  # 各地点の滞在時間（1時間）


def build_timeline(selected: list[str], legs: list[dict], start_hour: int = 9) -> list[dict]:
    """巡り順と区間データから、時刻付きのタイムラインを組み立てる。

    Args:
        selected: 巡る地点の名称リスト。先頭が出発地。
        legs: 区間データのリスト。travel_origin / destination / distance_m / duration_sec を含む。
        start_hour: 出発時刻（時）。

    Returns:
        各地点の情報を持つ辞書のリスト。
        time / place / distance_m / duration_sec を含む。
        distance_m と duration_sec は「次の地点までの移動」を表し、最後の地点は None。
    """
    now = datetime(2026, 1, 1, start_hour, 0)
    timeline = []

    for i in range(len(selected) - 1):
        start = selected[i]
        end = selected[i + 1]

        found = None
        for leg in legs:
            if leg["travel_origin"] == start and leg["destination"] == end:
                found = leg
                break

        if found is None:
            print(f"★ build_timeline: 区間が見つかりません {start} → {end}")
            timeline.append({
                "time": now.strftime("%H:%M"),
                "place": start,
                "distance_m": None,
                "duration_sec": None,
            })
            now += timedelta(seconds=STAY_SECONDS)
            continue

        timeline.append({
            "time": now.strftime("%H:%M"),
            "place": start,
            "distance_m": found["distance_m"],
            "duration_sec": found["duration_sec"],
        })

        now += timedelta(seconds=found["duration_sec"] + STAY_SECONDS)

    # 最後の地点はループに入らないので、ここで追加する
    timeline.append({
        "time": now.strftime("%H:%M"),
        "place": selected[-1],
        "distance_m": None,
        "duration_sec": None,
    })

    return timeline