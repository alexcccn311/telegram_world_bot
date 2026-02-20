# 作者：Alex
# 2026/1/28 17:06
from typing import Any, Dict
from src.telegram_world_bot.agents.base import BaseAgent
from src.telegram_world_bot.agents.tools import safe_trim

class OnboardingAgent(BaseAgent):
    name = "onboarding"

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        # 这是一个 stub：后面你接 LangChain / LLM 的时候替换这里
        user_message = safe_trim(str(input.get("user_message", "")))
        mode = str(input.get("mode", ""))
        reply = f"[onboarding agent stub]\nmode={mode}\nyou said: {user_message}"

        return {"reply": reply, "confidence": 0.5}
