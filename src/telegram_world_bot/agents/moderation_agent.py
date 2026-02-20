# 作者：Alex
# 2026/1/28 17:07
from typing import Any, Dict
from src.telegram_world_bot.agents.base import BaseAgent

class ModerationAgent(BaseAgent):
    name = "moderation"

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        # 这里只做占位：你以后可加敏感词/策略模型/第三方审核
        text = str(input.get("text", ""))
        blocked = False
        reason = None

        return {"blocked": blocked, "reason": reason}
