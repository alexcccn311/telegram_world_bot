# 作者：Alex
# 2026/1/28 17:06
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    name: str

    @abstractmethod
    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        输入/输出都用结构化 dict。
        不要在 agent 内部直接触达 Telegram。
        """
        raise NotImplementedError
