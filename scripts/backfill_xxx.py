# 作者：Alex
# 2026/1/28 16:57
from src.telegram_world_bot.config import load_settings

def main():
    settings = load_settings()
    print("Backfill script placeholder. ENV =", settings.env)

if __name__ == "__main__":
    main()