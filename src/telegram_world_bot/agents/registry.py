# 作者：Alex
# 2026/1/28 17:06
from typing import Dict
from src.telegram_world_bot.agents.base import BaseAgent

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> BaseAgent:
        if name not in self._agents:
            raise KeyError(f"Agent not found: {name}")
        return self._agents[name]
