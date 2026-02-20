# 作者：Alex
# 2026/1/28 17:06
"""
Agent memory 的占位实现。
你以后可以替换成：SQLite / Redis / 向量库 / LangChain memory。
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class AgentMemory:
    history: List[Dict[str, Any]] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})

    def last_n(self, n: int = 10) -> List[Dict[str, Any]]:
        return self.history[-n:]
