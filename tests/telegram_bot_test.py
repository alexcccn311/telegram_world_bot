# 作者：Alex
# 2026/2/2 00:11
# tests/grok_talking_telegram_bot.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# 复用你现有逻辑：不改 grok_talking.py
from grok_talking import (  # 注意：同目录 import，必要时改成 tests.grok_talking
    SYSTEM_DEFAULT,
    DATA_DIR,
    ENV_PATH,
    ensure_dirs,
    load_env,
    build_llm,
    read_log_lines,
    extract_system_prompt,
    rebuild_messages_from_logs,
    write_session_header,
    next_session_file,
    clear_all_logs,
    replace_last_assistant_log,
    delete_last_turn_from_log,
    append_log,
)

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage

TELEGRAM_MAX = 3900

# -----------------------
# Per-chat state (in-memory)
# -----------------------
@dataclass
class ChatState:
    log_fp: Path
    system_prompt: str
    messages: List[BaseMessage]


STATE: Dict[int, ChatState] = {}

def format_full_chat(lines: List[dict]) -> str:
    """
    复刻你 grok_talking.py 里的 print_full_chat 输出风格，但返回字符串。
    """
    out: List[str] = []
    out.append("=== 该文件全部聊天记录 ===")
    if not lines:
        out.append("(空)")
        out.append("=========================")
        return "\n".join(out)

    for obj in lines:
        role = obj.get("role", "unknown")
        content = obj.get("content", "")
        if role in ("meta", "error"):
            out.append(f"[{role}] {content}")
            continue
        if role == "system":
            out.append(f"system> {content}")
        elif role == "user":
            out.append(f"you> {content}")
        elif role == "assistant":
            out.append(f"grok> {content}")
        else:
            out.append(f"{role}> {content}")

    out.append("=========================")
    return "\n".join(out)

async def send_long_text(update: Update, text: str) -> None:
    """
    Telegram 单条消息有长度限制，超长时分段发送。
    """
    if not update.message:
        return

    # 按行切分更友好
    lines = text.splitlines(keepends=True)
    buf = ""
    for ln in lines:
        if len(buf) + len(ln) > TELEGRAM_MAX:
            await update.message.reply_text(buf)
            buf = ""
        buf += ln
    if buf:
        await update.message.reply_text(buf)

def list_session_files() -> List[Path]:
    files: List[Tuple[int, Path]] = []
    for p in DATA_DIR.glob("*.jsonl"):
        stem = p.stem
        if stem.isdigit():
            files.append((int(stem), p))
    files.sort(key=lambda x: x[0])
    return [p for _, p in files]


def get_or_init_state(chat_id: int) -> ChatState:
    """
    Telegram 环境下没有阻塞式 choose_session_file。
    策略：如果该 chat 没有 state，就默认：
    - 若 data/grok_talking 下有旧 session：使用最新的那个（续聊）
    - 否则新建一个
    """
    if chat_id in STATE:
        return STATE[chat_id]

    ensure_dirs()

    existing = list_session_files()
    if existing:
        log_fp = existing[-1]
        lines = read_log_lines(log_fp)
        system_prompt = extract_system_prompt(lines) if lines else SYSTEM_DEFAULT
        if not lines:
            write_session_header(log_fp, system_prompt)
        messages = rebuild_messages_from_logs(lines, system_prompt)
    else:
        log_fp = next_session_file()
        system_prompt = SYSTEM_DEFAULT
        write_session_header(log_fp, system_prompt)
        messages = [SystemMessage(content=system_prompt)]

    st = ChatState(log_fp=log_fp, system_prompt=system_prompt, messages=messages)
    STATE[chat_id] = st
    return st


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    st = get_or_init_state(chat_id)
    await update.message.reply_text(
        "\n".join(
            [
                "Grok Talking Telegram Bot 已启动。",
                f"当前会话文件：{st.log_fp.name}",
                "可用命令：",
                "• /list  列出会话",
                "• /use <n>  切换到 n.jsonl 续聊",
                "• /new  新建会话",
                "• /where  查看当前会话文件",
                "",
                "也支持直接发：刷新 / 重置 / 重写消息",
            ]
        )
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    st = get_or_init_state(update.effective_chat.id)
    await update.message.reply_text(
        "\n".join(
            [
                "可用指令：",
                "",
                "对话内指令（直接发文字即可）：",
                "• 刷新        重生成上一条 assistant",
                "• 重置        清空当前会话文件 + 清空上下文",
                "• 重写消息    删除上一轮 user+assistant（用于改写上一轮）",
                "",
                "Telegram 命令：",
                "• /start      启动说明",
                "• /help       显示本帮助",
                "• /list       列出已有会话编号",
                "• /use <n>    切换到 n.jsonl 续聊（例如：/use 3）",
                "• /new        新建会话文件",
                "• /where      查看当前会话文件",
                "",
                f"当前会话：{st.log_fp.name}",
            ]
        )
    )

async def cmd_where(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    st = get_or_init_state(update.effective_chat.id)
    await update.message.reply_text(f"当前会话文件：{st.log_fp}")


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ensure_dirs()
    files = list_session_files()
    if not files:
        await update.message.reply_text("(暂无历史记录)")
        return
    nums = [p.stem for p in files]
    await update.message.reply_text("历史会话：\n" + "\n".join(nums))


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    ensure_dirs()
    log_fp = next_session_file()
    system_prompt = SYSTEM_DEFAULT
    write_session_header(log_fp, system_prompt)
    messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]
    STATE[chat_id] = ChatState(log_fp=log_fp, system_prompt=system_prompt, messages=messages)
    await update.message.reply_text(f"新会话已创建：{log_fp.name}")


async def cmd_use(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    ensure_dirs()

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("用法：/use <数字>  例如：/use 1")
        return

    num = int(context.args[0])
    log_fp = DATA_DIR / f"{num}.jsonl"
    if not log_fp.exists():
        await update.message.reply_text("没有这个编号的记录文件。先 /list 看看有哪些。")
        return

    lines = read_log_lines(log_fp)
    system_prompt = extract_system_prompt(lines) if lines else SYSTEM_DEFAULT
    if not lines:
        write_session_header(log_fp, system_prompt)
    messages = rebuild_messages_from_logs(lines, system_prompt)

    STATE[chat_id] = ChatState(log_fp=log_fp, system_prompt=system_prompt, messages=messages)
    await update.message.reply_text(f"已切换到：{log_fp.name}\n下面是该会话完整记录：")

    full = format_full_chat(lines)
    await send_long_text(update, full)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    这是唯一“迁移交互”的地方：把 input()/print() 变成 Telegram 收发。
    其余逻辑（messages、日志、刷新/重置/重写）尽量复用你现有实现。
    """
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    st = get_or_init_state(chat_id)
    user_in = update.message.text.strip()
    if not user_in:
        return

    llm = context.bot_data["llm"]

    # -----------------------
    # 指令：重置
    # -----------------------
    if user_in == "重置":
        clear_all_logs(st.log_fp)
        st.messages = [SystemMessage(content=st.system_prompt)]
        write_session_header(st.log_fp, st.system_prompt)
        await update.message.reply_text("(已清空该会话文件的所有聊天记录与上下文)")
        return

    # -----------------------
    # 指令：刷新
    # -----------------------
    if user_in == "刷新":
        if len(st.messages) < 3:
            await update.message.reply_text("(当前没有可刷新的上一条回复)")
            return
        if not isinstance(st.messages[-1], AIMessage):
            await update.message.reply_text("(上一条不是 assistant 回复，无法刷新)")
            return

        st.messages.pop()  # 去掉最后一条 assistant

        try:
            resp = llm.invoke(st.messages)
        except Exception as e:
            err = f"[ERROR] {type(e).__name__}: {e}"
            append_log(st.log_fp, "error", err)
            await update.message.reply_text(err)
            return

        assistant_text = getattr(resp, "content", str(resp))
        st.messages.append(AIMessage(content=assistant_text))
        replace_last_assistant_log(st.log_fp, assistant_text)
        append_log(st.log_fp, "meta", "regenerate_last_assistant")

        await update.message.reply_text(assistant_text)
        return

    # -----------------------
    # 指令：重写消息
    # -----------------------
    if user_in == "重写消息":
        # 内存 messages：删掉末尾一轮（assistant + user）
        removed_mem = False
        if len(st.messages) >= 2 and isinstance(st.messages[-1], AIMessage):
            st.messages.pop()
            removed_mem = True
        if len(st.messages) >= 2 and isinstance(st.messages[-1], HumanMessage):
            st.messages.pop()
            removed_mem = True or removed_mem

        removed_file = delete_last_turn_from_log(st.log_fp)

        if removed_mem or removed_file:
            await update.message.reply_text("(已删除上一轮对话，你可以重新输入这一轮内容)")
        else:
            await update.message.reply_text("(没有可删除的上一轮对话)")
        return

    # -----------------------
    # 正常对话
    # -----------------------
    st.messages.append(HumanMessage(content=user_in))
    append_log(st.log_fp, "user", user_in)

    try:
        resp = llm.invoke(st.messages)
    except Exception as e:
        err = f"[ERROR] {type(e).__name__}: {e}"
        append_log(st.log_fp, "error", err)
        await update.message.reply_text(err)
        return

    assistant_text = getattr(resp, "content", str(resp))
    st.messages.append(AIMessage(content=assistant_text))
    append_log(st.log_fp, "assistant", assistant_text)

    await update.message.reply_text(assistant_text)


def main() -> None:
    # 复用你已有的 env 逻辑
    ensure_dirs()
    load_env()  # 会读 .env / 环境变量；你原本就这么做

    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError(
            f"未找到 BOT_TOKEN。请在 {ENV_PATH} 写入 BOT_TOKEN=... 或设置环境变量。"
        )

    llm = build_llm()

    app = Application.builder().token(bot_token).build()
    app.bot_data["llm"] = llm

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("where", cmd_where))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("use", cmd_use))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()


if __name__ == "__main__":
    main()
