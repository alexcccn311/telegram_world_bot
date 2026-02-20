# 作者：Alex
# 2026/1/28 16:52
from dataclasses import dataclass, asdict
from typing import Dict, Optional
import json
from pathlib import Path

@dataclass
class UserProfile:
    user_id: int
    username: str | None = None
    first_name: str | None = None

class UserStore:
    """
    本地轻量 user store（json）。主数据上 MySQL 时可替换掉。
    """
    def __init__(self, path: str = "data/users.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[int, UserProfile] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            for k, v in raw.items():
                self._cache[int(k)] = UserProfile(**v)
        except Exception:
            self._cache = {}

    def _save(self) -> None:
        data = {str(k): asdict(v) for k, v in self._cache.items()}
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def upsert(self, profile: UserProfile) -> None:
        self._cache[profile.user_id] = profile
        self._save()

    def get(self, user_id: int) -> Optional[UserProfile]:
        return self._cache.get(user_id)

