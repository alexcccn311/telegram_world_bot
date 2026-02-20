# 作者：Alex
# 2026/1/28 16:58
from src.telegram_world_bot.config import load_settings
from src.telegram_world_bot.db.mysql import make_session_factory
from src.telegram_world_bot.db.models import Base
from src.telegram_world_bot.db.dao import MySQLDAO

def main():
    settings = load_settings()
    session_factory, engine = make_session_factory(settings.db)
    Base.metadata.create_all(engine)

    dao = MySQLDAO(session_factory)
    deleted = dao.clear_idempotency_keys()
    print(f"✅ cleared idempotency keys: {deleted}")

if __name__ == "__main__":
    main()
