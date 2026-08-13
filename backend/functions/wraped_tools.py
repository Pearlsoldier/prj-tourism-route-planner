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