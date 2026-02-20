# 作者：Alex
# 2026/1/28 16:59
from src.telegram_world_bot.services.session_store import SessionStore

def test_session_store_basic():
    store = SessionStore()
    store.set_value(1, "foo", "bar")
    assert store.get_value(1, "foo") == "bar"
    store.clear(1)
    assert store.get_value(1, "foo") is None
