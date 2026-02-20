# 作者：Alex
# 2026/1/28 16:48
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    bot_token: str
    env: str = "dev"
    log_level: str = "INFO"

def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing BOT_TOKEN in environment (.env).")
    return Settings(
        bot_token=token,
        env=os.getenv("ENV", "dev").strip(),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
    )