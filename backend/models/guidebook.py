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

    def missing_fields(self) -> list[str]:
        return [name for name, value in vars(self).items() if not value]

    def is_ready(self) -> bool:
        return not self.missing_fields()