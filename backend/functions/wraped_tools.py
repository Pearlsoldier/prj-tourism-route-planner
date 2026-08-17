import functools
from models.guidebook import Guidebook
print("[import] wrapped_tools を読み込み開始")

print("[import] wrapped_tools を読み込み開始")


def record_to_guidebook(plan: Guidebook, field: str, mode: str = "once"):
    """Guidebook に記録するデコレータ"""
    print(f"   [1層目] record_to_guidebook 実行 plan={plan}")

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
                    pass
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