# 作者：Alex
# 2026/1/28 16:57
from telegram_world_bot.config import load_settings
from telegram_world_bot.db.local import make_session_factory, init_local_db

def main():
    settings = load_settings()
    _, engine = make_session_factory(settings.local_db_url)
    init_local_db(engine)
    print(f"✅ local db initialized: {settings.local_db_url}")

if __name__ == "__main__":
    main()