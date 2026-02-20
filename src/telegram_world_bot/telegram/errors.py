# 作者：Alex
# 2026/1/31 20:09
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("⚠️ 出错了，我这边记录一下。")
        except Exception:
            # 避免二次异常
            pass