# 作者：Alex
# 2026/1/28 17:07
from typing import Any, Dict
from src.telegram_world_bot.agents.base import BaseAgent
from src.telegram_world_bot.agents.tools import safe_trim

class ControlAgent(BaseAgent):
    name = "control"

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        user_message = safe_trim(str(input.get("user_message", "")))
        return {"reply": f"[control agent stub]\nyou said: {user_message}", "confidence": 0.5}
