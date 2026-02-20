# 作者：Alex
# 2026/1/31 20:09
from telegram.ext import Application, CommandHandler

from src.telegram_world_bot.config import load_settings
from src.telegram_world_bot.logging_setup import setup_logging
from src.telegram_world_bot.telegram.errors import on_error

from src.telegram_world_bot.services.session_store import SessionStore
from src.telegram_world_bot.services.user_store import UserStore

from src.telegram_world_bot.db.mysql import make_session_factory
from src.telegram_world_bot.db.models import Base
from src.telegram_world_bot.db.dao import MySQLDAO

from src.telegram_world_bot.agents.registry import AgentRegistry
from src.telegram_world_bot.agents.onboarding_agent import OnboardingAgent
from src.telegram_world_bot.agents.control_agent import ControlAgent
from src.telegram_world_bot.agents.moderation_agent import ModerationAgent

from src.telegram_world_bot.handlers.help import help_cmd
from src.telegram_world_bot.handlers.debug.echo import echo_cmd
from src.telegram_world_bot.flows.onboarding import build_onboarding_conv


def build_app() -> Application:
    settings = load_settings()
    setup_logging(settings.log_level)

    app = Application.builder().token(settings.bot_token).build()

    # --- MySQL ---
    session_factory, engine = make_session_factory(settings.db)
    Base.metadata.create_all(engine)
    app.bot_data["dao"] = MySQLDAO(session_factory)
    app.bot_data["db_engine"] = engine  # 如果你后面要做原生查询/健康检查用

    # --- Stores ---
    app.bot_data["session_store"] = SessionStore()
    app.bot_data["user_store"] = UserStore()  # 你接 MySQL 后可替换成 MySQLUserStore

    # --- Agents ---
    registry = AgentRegistry()
    registry.register(OnboardingAgent())
    registry.register(ControlAgent())
    registry.register(ModerationAgent())
    app.bot_data["agents"] = registry

    # --- Flows / Handlers ---
    app.add_handler(build_onboarding_conv())
    app.add_handler(CommandHandler("help", help_cmd))
    if settings.env != "prod":
        app.add_handler(CommandHandler("echo", echo_cmd))

    app.add_error_handler(on_error)
    return app
