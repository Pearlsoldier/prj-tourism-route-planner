
from datetime import datetime, timedelta

STAY_MINUTES = 60  # 各地点の滞在時間（分）


def build_timeline(selected: list[str], legs: list[dict], start_hour: int = 9) -> list[dict]:
    """巡り順と区間データから、時刻付きのタイムラインを組み立てる。

    Args:
        selected: 巡る地点の名称リスト。先頭が出発地。
        legs: 区間データのリスト。travel_origin / destination / distance_m / duration_min を含む。
        start_hour: 出発時刻（時）。

    Returns:
        各地点の情報を持つ辞書のリスト。
        time / place / distance_m / duration_min を含む。
        distance_m と duration_min は「次の地点までの移動」を表し、最後の地点は None。
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
                "duration_min": None,
            })
            now += timedelta(minutes=STAY_MINUTES)
            continue

        timeline.append({
            "time": now.strftime("%H:%M"),
            "place": start,
            "distance_m": found["distance_m"],
            "duration_min": found["duration_min"],
        })

        now += timedelta(minutes=found["duration_min"] + STAY_MINUTES)

    # 最後の地点はループに入らないので、ここで追加する
    timeline.append({
        "time": now.strftime("%H:%M"),
        "place": selected[-1],
        "distance_m": None,
        "duration_min": None,
    })

    return timeline


def format_timeline_markdown(timeline: list[dict]) -> str:
    lines = ["| 時刻 | 場所 | 次までの距離 | 徒歩 |", "|---|---|---|---|"]
    for row in timeline:
        d = f"{row['distance_m']} m" if row["distance_m"] is not None else "—"
        m = f"{row['duration_min']} 分" if row["duration_min"] is not None else "—"
        lines.append(f"| {row['time']} | {row['place']} | {d} | {m} |")
    return "\n".join(lines)