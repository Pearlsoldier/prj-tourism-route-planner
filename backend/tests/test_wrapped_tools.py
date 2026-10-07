import pytest

from functions.wrapped_tools import _add_minutes


@pytest.mark.parametrize("hhmm, minutes, expected", [
    ("09:00", 30, "09:30"),
    ("23:59", 1, "00:00"),
    ("23:58", 1, "23:59"), # 日を跨がない直前（結果が "23:59" になる）
    ("23:59", 0, "23:59"), # minutes=0（何も足さない）
    ("23:30", 45, "00:15"),# "23:30" + 45 → "00:15"（分がゼロでない跨ぎ）
])
def test_add_minutes(hhmm, minutes, expected):
    assert _add_minutes(hhmm, minutes) == expected

# 24時間（1440分）以上は対象外。呼び出し元（build_route）が足すのは
# 徒歩1区間か滞在時間のみで、1回あたり最大でも数十分程度のため。