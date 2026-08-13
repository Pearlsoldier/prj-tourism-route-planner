from dataclasses import dataclass, field
print("[import] models.guidebook を読み込み")

@dataclass
class Guidebook:
    # originは出発地
    origin: dict | None = None
    # candidatesは候補地
    # candidates: list[dict] = field(default_factory=list)
    # 入ってきた順序が巡り順を表す
    selected: list[dict] = field(default_factory=list)
    # legsは区間
    legs: list[dict] = field(default_factory=list)

    # 観光の開始時刻（"HH:MM" 形式）。任意項目なので missing_fields には含めない
    start_time: str | None = None

    # 揃っていないとしおりが組めない欄
    REQUIRED_FIELDS = ("origin", "selected", "legs")

    def missing_fields(self) -> list[str]:
        return [name for name in self.REQUIRED_FIELDS if not getattr(self, name)]

    def is_ready(self) -> bool:
        return not self.missing_fields()