# 作者：Alex
# 2026/1/31 19:56

from telegram import Update
from telegram.ext import ContextTypes

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "/start - 启动\n"
        "/help - 帮助\n"
        "/echo <text> - 回显测试\n"
    )