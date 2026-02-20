# tests/grok_talking.py
from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_xai import ChatXAI


# -----------------------
# Paths / Env
# -----------------------
SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[1]  # .../root/tests/grok_talking.py -> root
DATA_DIR = REPO_ROOT / "data" / "grok_talking"
ENV_PATH = REPO_ROOT / ".env"

SYSTEM_DEFAULT = (
    "You are Grok. Answer clearly and helpfully. "
    "If you need more details, ask concise questions."
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class LogLine:
    ts_utc: str
    role: str  # system/user/assistant/meta/error
    content: str


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_env() -> None:
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH)
    else:
        load_dotenv()


def build_llm() -> ChatXAI:
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            f"未找到 XAI_API_KEY。请在 {ENV_PATH} 写入 XAI_API_KEY=... 或设置环境变量。"
        )
    model = os.getenv("XAI_MODEL", "grok-beta")
    return ChatXAI(model=model, api_key=api_key, temperature=0.3)


# -----------------------
# Log file helpers
# -----------------------
def append_log(fp: Path, role: str, content: str) -> None:
    line = LogLine(ts_utc=utc_now_iso(), role=role, content=content)
    with fp.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(line), ensure_ascii=False) + "\n")


def read_log_lines(fp: Path) -> List[dict]:
    if not fp.exists():
        return []
    out: List[dict] = []
    with fp.open("r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                out.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
    return out


def write_log_lines(fp: Path, lines: List[dict]) -> None:
    with fp.open("w", encoding="utf-8") as f:
        for obj in lines:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def replace_last_assistant_log(fp: Path, new_content: str) -> None:
    lines = read_log_lines(fp)
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].get("role") == "assistant":
            lines[i]["ts_utc"] = utc_now_iso()
            lines[i]["content"] = new_content
            write_log_lines(fp, lines)
            return
    append_log(fp, "assistant", new_content)


def clear_all_logs(fp: Path) -> None:
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text("", encoding="utf-8")


def write_session_header(fp: Path, system_prompt: str) -> None:
    append_log(fp, "meta", f"session_start repo_root={str(REPO_ROOT)} model={os.getenv('XAI_MODEL', 'grok-beta')}")
    append_log(fp, "system", system_prompt)


def delete_last_turn_from_log(fp: Path) -> bool:
    """
    删除“上一轮对话”：最后出现的 user 以及其后的最后一个 assistant（如果存在）。
    返回是否成功删除。
    """
    lines = read_log_lines(fp)
    if not lines:
        return False

    # 找最后一个 user 的位置
    last_user_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].get("role") == "user":
            last_user_idx = i
            break
    if last_user_idx is None:
        return False

    # 在 last_user_idx 之后，找最后一个 assistant（一般紧跟着，但容错处理）
    last_assistant_idx = None
    for j in range(len(lines) - 1, last_user_idx, -1):
        if lines[j].get("role") == "assistant":
            last_assistant_idx = j
            break

    # 只删 user + assistant（若 assistant 不存在，就只删 user）
    to_remove = {last_user_idx}
    if last_assistant_idx is not None:
        to_remove.add(last_assistant_idx)

    new_lines = [ln for k, ln in enumerate(lines) if k not in to_remove]
    write_log_lines(fp, new_lines)
    return True


# -----------------------
# Session selection
# -----------------------
def list_session_files() -> List[Path]:
    files: List[Tuple[int, Path]] = []
    for p in DATA_DIR.glob("*.jsonl"):
        m = re.fullmatch(r"(\d+)\.jsonl", p.name)
        if not m:
            continue
        files.append((int(m.group(1)), p))
    files.sort(key=lambda x: x[0])
    return [p for _, p in files]


def next_session_file() -> Path:
    existing = list_session_files()
    if not existing:
        return DATA_DIR / "1.jsonl"
    last_num = int(existing[-1].stem)
    return DATA_DIR / f"{last_num + 1}.jsonl"


def choose_session_file() -> Tuple[Path, bool]:
    files = list_session_files()
    print("=== Grok Talking 历史会话 ===")
    if files:
        for p in files:
            print(f"  {p.stem}.jsonl")
    else:
        print("  (暂无历史记录)")

    print("\n输入数字选择续聊，例如：1")
    print("输入 N 开始新聊天")
    while True:
        choice = input("选择> ").strip()
        if not choice:
            continue
        if choice.lower() == "n":
            fp = next_session_file()
            return fp, True
        if choice.isdigit():
            num = int(choice)
            fp = DATA_DIR / f"{num}.jsonl"
            if fp.exists():
                return fp, False
            print("没有这个编号的记录文件，请重新输入。")
            continue
        print("输入无效：请输入数字或 N。")


# -----------------------
# Rebuild context from logs
# -----------------------
def extract_system_prompt(lines: List[dict]) -> str:
    system_prompt = SYSTEM_DEFAULT
    for obj in lines:
        if obj.get("role") == "system" and isinstance(obj.get("content"), str):
            system_prompt = obj["content"]
    return system_prompt


def rebuild_messages_from_logs(lines: List[dict], system_prompt: str) -> List[BaseMessage]:
    msgs: List[BaseMessage] = [SystemMessage(content=system_prompt)]
    for obj in lines:
        role = obj.get("role")
        content = obj.get("content")
        if not isinstance(content, str):
            continue
        if role == "user":
            msgs.append(HumanMessage(content=content))
        elif role == "assistant":
            msgs.append(AIMessage(content=content))
    return msgs


def print_full_chat(lines: List[dict]) -> None:
    print("\n=== 该文件全部聊天记录 ===")
    if not lines:
        print("(空)")
        print("=========================\n")
        return

    for obj in lines:
        role = obj.get("role", "unknown")
        content = obj.get("content", "")
        if role in ("meta", "error"):
            print(f"[{role}] {content}")
            continue
        if role == "system":
            print(f"system> {content}")
        elif role == "user":
            print(f"you> {content}")
        elif role == "assistant":
            print(f"grok> {content}")
        else:
            print(f"{role}> {content}")
    print("=========================\n")


# -----------------------
# Main loop
# -----------------------
def main() -> None:
    ensure_dirs()
    load_env()
    llm = build_llm()

    log_fp, is_new = choose_session_file()

    if is_new:
        system_prompt = SYSTEM_DEFAULT
        write_session_header(log_fp, system_prompt)
        messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]
        print(f"\n新聊天：{log_fp.name}")
    else:
        lines = read_log_lines(log_fp)
        print(f"\n续聊文件：{log_fp.name}")
        print_full_chat(lines)
        system_prompt = extract_system_prompt(lines)
        messages = rebuild_messages_from_logs(lines, system_prompt)

        if not lines:
            write_session_header(log_fp, system_prompt)

    print(f"Repo root: {REPO_ROOT}")
    print(f"Log file : {log_fp}")
    print("开始对话。支持三个指令：刷新 / 重置 / 重写消息\n")

    while True:
        try:
            user_in = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出。")
            append_log(log_fp, "meta", "session_end")
            break

        if not user_in:
            continue

        # -----------------------
        # 指令：重置（清空当前文件 + 清空上下文）
        # -----------------------
        if user_in == "重置":
            clear_all_logs(log_fp)
            messages = [SystemMessage(content=system_prompt)]
            write_session_header(log_fp, system_prompt)
            print("(已清空该会话文件的所有聊天记录与上下文)\n")
            continue

        # -----------------------
        # 指令：刷新（重生成上一条 assistant）
        # -----------------------
        if user_in == "刷新":
            if len(messages) < 3:
                print("(当前没有可刷新的上一条回复)\n")
                continue
            if not isinstance(messages[-1], AIMessage):
                print("(上一条不是 assistant 回复，无法刷新)\n")
                continue

            messages.pop()  # 去掉最后一条 assistant

            try:
                resp = llm.invoke(messages)
            except Exception as e:
                err = f"[ERROR] {type(e).__name__}: {e}"
                print(err + "\n")
                append_log(log_fp, "error", err)
                continue

            assistant_text = getattr(resp, "content", str(resp))
            print(f"grok> {assistant_text}\n")

            messages.append(AIMessage(content=assistant_text))
            replace_last_assistant_log(log_fp, assistant_text)
            append_log(log_fp, "meta", "regenerate_last_assistant")
            continue

        # -----------------------
        # 指令：重写消息（删除上一轮 user+assistant）
        # -----------------------
        if user_in == "重写消息":
            # 内存 messages：尝试删掉末尾一轮（assistant + user）
            removed_mem = False
            if len(messages) >= 2 and isinstance(messages[-1], AIMessage):
                messages.pop()
                removed_mem = True
            if len(messages) >= 2 and isinstance(messages[-1], HumanMessage):
                messages.pop()
                removed_mem = True or removed_mem

            # 文件：删除上一轮
            removed_file = delete_last_turn_from_log(log_fp)

            if removed_mem or removed_file:
                print("(已删除上一轮对话，你可以重新输入这一轮内容)\n")
            else:
                print("(没有可删除的上一轮对话)\n")
            continue

        # -----------------------
        # 正常对话
        # -----------------------
        messages.append(HumanMessage(content=user_in))
        append_log(log_fp, "user", user_in)

        try:
            resp = llm.invoke(messages)
        except Exception as e:
            err = f"[ERROR] {type(e).__name__}: {e}"
            print(err + "\n")
            append_log(log_fp, "error", err)
            continue

        assistant_text = getattr(resp, "content", str(resp))
        print(f"grok> {assistant_text}\n")

        messages.append(AIMessage(content=assistant_text))
        append_log(log_fp, "assistant", assistant_text)


if __name__ == "__main__":
    main()
