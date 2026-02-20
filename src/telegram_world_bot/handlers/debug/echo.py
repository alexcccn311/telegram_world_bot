from telegram import Update
from telegram.ext import ContextTypes

async def echo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("用法：/echo 你好")
        return
    await update.message.reply_text(text)

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 非命令消息的回显（测试用）
    if update.message and update.message.text:
        await update.message.reply_text(f"你说：{update.message.text}")
