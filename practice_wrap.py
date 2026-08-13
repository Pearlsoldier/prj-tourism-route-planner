"""
練習用：ラッパーは「いつ作られ」「いつ走る」のか

実行方法:
    python practice_wrap.py

ネットには繋がない。Gemini も Google API も呼ばない。
本物と同じ「順番」だけを再現している。

--------------------------------------------------------------------
【実行する前に、下の予想欄をコメントに書き込むこと】

予想1: [前] の origin には何が入っている？
    → あなたの予想:

予想2: ★ログは [前] と [後] のどちらとどちらの間に出る？
    → あなたの予想:

予想3: [内側] wrapper 実行 のログは何回出る？
    → あなたの予想:
--------------------------------------------------------------------
"""

import functools
from dataclasses import dataclass


# ====================================================================
# 1. しおり（本物の models/guidebook.py を最小化したもの）
# ====================================================================
@dataclass
class Guidebook:
    origin: dict | None = None


# ====================================================================
# 2. ツール（本物の tools.geocode_place の代わり）
#    中身は返すだけ。★ログの位置に注目する。
# ====================================================================
def geocode_place(place: str) -> dict:
    """地名から座標を取る"""
    print(f"      ★ geocode_place が呼ばれました place={place}")
    return {"address": f"日本、神奈川県鎌倉市{place}", "lat": 35.3190647, "lng": 139.5504119}


# ====================================================================
# 3. ラッパー（2層版）
# ====================================================================
def record_to_guidebook(plan: Guidebook, func):
    print(f"      [外側] record_to_guidebook の中に入った func={func.__name__}")

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"      [内側] wrapper の中に入った args={args}")
        result = func(*args, **kwargs)
        if "error" not in result and plan.origin is None:
            plan.origin = result
            print("      [内側] plan.origin に書き込んだ")
        else:
            print(f"      [内側] 書き込まずスキップ（origin既存={plan.origin is not None}）")
        return result

    print("      [外側] wrapper を return する ← まだ一度も呼んでいない")
    return wrapper


# ====================================================================
# 4. Gemini の代わり
#    tools=[...] を受け取り、「使う」と判断したものにカッコを付けて呼ぶ。
# ====================================================================
def fake_generate_content(contents: str, tools: list):
    print("   【generate_content の中に入った】")
    print(f"   受け取ったツール一覧: {[t.__name__ for t in tools]}")
    print(f"   ユーザーの発言: {contents}")

    tool = tools[0]
    print("   Gemini「geocode_place を使おう」と判断 → ここで初めてカッコを付ける")
    result = tool("鎌倉駅")

    print(f"   Gemini がツールの戻り値を読む: {result['address']}")
    result = tool("小町通り")
    print(f"   Gemini がツールの戻り値を読む: {result['address']}")
    print("   【generate_content から出る】")
    return "鎌倉駅ですね。周辺の観光地を探しましょうか？"


# ====================================================================
# 5. 本番の chat_completions と同じ流れ
# ====================================================================
def main():
    print("① リクエスト到着")
    plan = Guidebook()
    print(f"   plan を用意した → {plan}\n")

    print("② ラッパーを作る")
    geocode_place_w = record_to_guidebook(plan, geocode_place)
    print(f"   geocode_place_w の正体 → {geocode_place_w}\n")

    print(f"[前] {plan}\n")

    print("③ Gemini を呼ぶ")
    response = fake_generate_content(
        contents="鎌倉駅を散策したい",
        tools=[geocode_place_w],
    )
    print()

    print(f"[後] {plan}\n")
    print(f"ユーザーに返す文章: {response}")


if __name__ == "__main__":
    main()


# ====================================================================
# 【課題】上を実行して予想と照合できたら、次を順にやる
#
# 課題1: main() の tools=[geocode_place_w] を tools=[geocode_place] に変える。
#        （ラップしていない生のツールを渡す）
#        → ★ログは出るか？ [後] の origin はどうなるか？ なぜか？
#
# 課題2: fake_generate_content の中の tool("鎌倉駅") を消して、
#        代わりに print("Gemini は今回ツールを使わないと判断") と書く。
#        → [後] の origin はどうなるか？
#
# 課題3: fake_generate_content の中で tool(...) を2回呼ぶ。
#        2回目は tool("小町通り") にする。
#        → origin に入るのはどちらか？ ガードのどの条件が効いたか？
#        （これは 7/29 のログに書いた「origin に小町通りが入る」の再現）
#
# 課題4: main() の ② と ③ の行を入れ替えてみる（先に generate_content を呼ぶ）。
#        → 何というエラーが出るか？ トレースバックの一番下の行を読む。
# ====================================================================