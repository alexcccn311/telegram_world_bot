# 作者：Alex
# 2026/1/28 16:59
from src.telegram_world_bot.db.local import make_session_factory, init_local_db
from src.telegram_world_bot.db.dao import LocalDAO

def test_idempotency():
    session_factory, engine = make_session_factory("sqlite:///:memory:")
    init_local_db(engine)

    dao = LocalDAO(session_factory)
    assert dao.try_acquire_idempotency("k1") is True
    assert dao.try_acquire_idempotency("k1") is False
