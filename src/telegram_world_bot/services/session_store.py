# 作者：Alex
# 2026/1/28 16:55
from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class Session:
    user_id: int
    data: Dict[str, Any] = field(default_factory=dict)

class SessionStore:
    """
    短期会话：给 flows（ConversationHandler）用
    不建议拿它做 agent 长期 memory。
    """
    def __init__(self):
        self._sessions: Dict[int, Session] = {}

    def get(self, user_id: int) -> Session:
        if user_id not in self._sessions:
            self._sessions[user_id] = Session(user_id=user_id)
        return self._sessions[user_id]

    def clear(self, user_id: int) -> None:
        self._sessions.pop(user_id, None)

    def set_value(self, user_id: int, key: str, value: Any) -> None:
        sess = self.get(user_id)
        sess.data[key] = value

    def get_value(self, user_id: int, key: str, default: Any = None) -> Any:
        return self.get(user_id).data.get(key, default)
