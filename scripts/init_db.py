# 作者：Alex
# 2026/1/28 16:57
from src.telegram_world_bot.config import load_settings
from src.telegram_world_bot.db.mysql import make_session_factory
from src.telegram_world_bot.db.models import Base

def main():
    settings = load_settings()
    session_factory, engine = make_session_factory(settings.db)
    Base.metadata.create_all(engine)
    print("✅ MySQL tables created/verified.")

if __name__ == "__main__":
    main()
