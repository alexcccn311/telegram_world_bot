# 作者：Alex
# 2026/1/28 17:06
"""
给 agent 使用的工具函数（不是 scripts）。
例：格式化、简单检索、规则判断等
"""
from typing import Any, Dict

def safe_trim(text: str, limit: int = 800) -> str:
    text = text or ""
    text = text.strip()
    return text[:limit]
