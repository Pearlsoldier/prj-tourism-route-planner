from datetime import datetime, timedelta

DEFAULT_STAY_MINUTES = 60  # stay_minutes が指定されなかった場合の既定値


def build_timeline(selected: list[dict], legs: list[dict], start_time: str = "09:00") -> list[dict]:
    """巡り順と区間データから、時刻付きのタイムラインを組み立てる。

    Args:
    
        selected: 巡る地点のリスト。先頭が出発地。
            各要素は name（地点名）と stay_minutes（滞在時間・分）を持つ辞書。
        legs: 区間データのリスト。travel_origin / destination / distance_m / duration_min を含む。
        start_time: 観光の開始時刻。"HH:MM" 形式（例: "09:00"）。

    Returns:
        各地点の情報を持つ辞書のリスト。
        time / place / distance_m / duration_min を含む。
        distance_m と duration_min は「次の地点までの移動」を表し、最後の地点は None。
    """
    hour, minute = map(int, start_time.split(":"))
    now = datetime(2026, 1, 1, hour, minute)
    timeline = []

    for i in range(len(selected) - 1):
        start = selected[i]["name"]
        end = selected[i + 1]["name"]

        stay = selected[i].get("stay_minutes")
        if stay is None:
            print(f"★ build_timeline: stay_minutes がありません {start}")
            stay = DEFAULT_STAY_MINUTES

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
            now += timedelta(minutes=stay)
            continue

        timeline.append({
            "time": now.strftime("%H:%M"),
            "place": start,
            "distance_m": found["distance_m"],
            "duration_min": found["duration_min"],
        })

        now += timedelta(minutes=found["duration_min"] + stay)

    # 最後の地点はループに入らないので、ここで追加する
    timeline.append({
        "time": now.strftime("%H:%M"),
        "place": selected[-1]["name"],
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

def format_summary_markdown(summary: dict) -> str:
    total = summary["total_walk_min"] + summary["total_stay_min"]
    hours, minutes = divmod(total, 60)
    return (
        f"\n徒歩 {summary['total_walk_min']} 分 / "
        f"滞在 {summary['total_stay_min']} 分 / "
        f"計 {hours} 時間 {minutes} 分（{summary['total_distance_m']} m）。"
        f"終了見込み {summary['end_time']}"
    )

def summarize_plan(timeline: list[dict], selected: list[dict]) -> dict:
    """タイムラインと巡り順から、合計時間と終了見込みを計算する。

    Args:
        timeline: build_timeline の返り値。
        selected: 巡る地点のリスト。stay_minutes の合計に使う。

    Returns:
        total_walk_min / total_stay_min / total_distance_m / end_time を含む辞書。
        end_time は最終地点の到着時刻に、その地点の滞在時間を足した時刻。
    """
    total_walk_min = sum(row["duration_min"] or 0 for row in timeline)
    total_distance_m = sum(row["distance_m"] or 0 for row in timeline)
    total_stay_min = sum(
        place.get("stay_minutes") or 0 for place in selected
    )

    last_stay = selected[-1].get("stay_minutes") or 0
    hour, minute = map(int, timeline[-1]["time"].split(":"))
    end = datetime(2026, 1, 1, hour, minute) + timedelta(minutes=last_stay)

    return {
        "total_walk_min": total_walk_min,
        "total_stay_min": total_stay_min,
        "total_distance_m": total_distance_m,
        "end_time": end.strftime("%H:%M"),
    }