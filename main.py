# 作者：Alex
# 2026/1/28 16:48
from src.telegram_world_bot.telegram.build_app import build_app

def main():
    app = build_app()
    app.run_polling(allowed_updates=["message"])

if __name__ == "__main__":
    main()