# 作者：Alex
# 2026/1/28 16:48
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    name: str
    charset: str = "utf8mb4"

    def sqlalchemy_url(self) -> str:
        # PyMySQL driver
        return (
            f"mysql+pymysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
            f"?charset={self.charset}"
        )

@dataclass(frozen=True)
class Settings:
    bot_token: str
    env: str = "dev"
    log_level: str = "INFO"
    db: DBConfig | None = None

def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing BOT_TOKEN in .env")

    env = os.getenv("ENV", "dev").strip()
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()

    # 你说长期使用本地 MySQL：这里我们直接要求 DB_HOST 必须存在
    host = os.getenv("DB_HOST", "").strip()
    if not host:
        raise RuntimeError("Missing DB_HOST in .env")

    db = DBConfig(
        host=host,
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "").strip(),
        password=os.getenv("DB_PASSWORD", "").strip(),
        name=os.getenv("DB_NAME", "").strip(),
        charset=os.getenv("DB_CHARSET", "utf8mb4").strip(),
    )

    if not db.user or not db.name:
        raise RuntimeError("Missing DB_USER or DB_NAME in .env")

    return Settings(
        bot_token=token,
        env=env,
        log_level=log_level,
        db=db,
    )
