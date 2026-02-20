# 作者：Alex
# 2026/1/31 21:38
import pytest
from src.telegram_world_bot.agents.registry import AgentRegistry
from src.telegram_world_bot.agents.onboarding_agent import OnboardingAgent

def test_registry_register_get():
    reg = AgentRegistry()
    reg.register(OnboardingAgent())
    agent = reg.get("onboarding")
    assert agent is not None

def test_registry_missing():
    reg = AgentRegistry()
    with pytest.raises(KeyError):
        reg.get("missing")
