from enum import IntEnum

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

class S(IntEnum):
    CHOOSE_MODE = 1
    CONFIRM = 2


MODE_KB = ReplyKeyboardMarkup(
    [["新用户模式", "老用户迁移"], ["取消"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

CONFIRM_KB = ReplyKeyboardMarkup(
    [["确认提交"], ["取消"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


def _deps(context: ContextTypes.DEFAULT_TYPE):
    session_store = context.application.bot_data["session_store"]
    user_store = context.application.bot_data["user_store"]
    dao = context.application.bot_data["dao"]
    agents = context.application.bot_data.get("agents")
    return session_store, user_store, dao, agents


# ---------- /start ----------
async def entry_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.effective_user or not update.message:
        return ConversationHandler.END

    session_store, _, _, _ = _deps(context)
    session_store.clear(update.effective_user.id)

    await update.message.reply_text(
        "请选择模式：",
        reply_markup=MODE_KB,
    )
    return S.CHOOSE_MODE


# ---------- 选择模式 ----------
async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    msg = update.message
    if not user or not msg:
        return ConversationHandler.END

    text = (msg.text or "").strip()

    if text == "取消":
        return await cancel(update, context)

    if text not in ("新用户模式", "老用户迁移"):
        await msg.reply_text("请选择键盘上的选项。", reply_markup=MODE_KB)
        return S.CHOOSE_MODE

    session_store, _, _, _ = _deps(context)
    session_store.set_value(user.id, "mode", text)

    await msg.reply_text(
        f"你选择了：{text}\n\n确认提交？",
        reply_markup=CONFIRM_KB,
    )
    return S.CONFIRM


# ---------- 确认 ----------
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    msg = update.message
    if not user or not msg:
        return ConversationHandler.END

    text = (msg.text or "").strip()

    if text == "取消":
        return await cancel(update, context)

    if text != "确认提交":
        await msg.reply_text("请选择键盘上的按钮。", reply_markup=CONFIRM_KB)
        return S.CONFIRM

    session_store, user_store, dao, agents = _deps(context)

    mode = session_store.get_value(user.id, "mode")

    # ---- 幂等 ----
    idem_key = f"onboarding_submit:{user.id}:{mode}"
    if not dao.try_acquire_idempotency(idem_key):
        await msg.reply_text("这个提交已处理过。", reply_markup=ReplyKeyboardRemove())
        session_store.clear(user.id)
        return ConversationHandler.END

    # ---- 日志 ----
    dao.log_event(user.id, "onboarding_submit", payload=f"mode={mode}")

    # ---- 写 user_store ----
    profile = user_store.get(user.id)
    if profile is None:
        from telegram_world_bot.services.user_store import UserProfile
        profile = UserProfile(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
        )

    user_store.upsert(profile)

    # ---- agent（可选）----
    agent_reply = None
    if agents:
        try:
            agent = agents.get("onboarding")
            result = await agent.run({"mode": mode})
            agent_reply = result.get("reply")
        except Exception:
            pass

    session_store.clear(user.id)

    text = "✅ 已完成设置。"
    if agent_reply:
        text += "\n\n" + str(agent_reply)

    await msg.reply_text(text, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ---------- 取消 ----------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        await update.message.reply_text("已取消。", reply_markup=ReplyKeyboardRemove())

    if update.effective_user:
        session_store, _, _, _ = _deps(context)
        session_store.clear(update.effective_user.id)

    return ConversationHandler.END


def build_onboarding_conv() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("start", entry_start)],
        states={
            S.CHOOSE_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_mode)],
            S.CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex(r"^取消$"), cancel),
        ],
        name="onboarding_conversation",
        persistent=False,
    )
