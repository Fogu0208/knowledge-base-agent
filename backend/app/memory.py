"""会话记忆：每个 session_id 维护一份消息历史（进程内存实现）。

进阶方向（README 里有）：换成 Redis / 数据库持久化，
再加上按 token 长度的裁剪策略，就是完整的短期记忆模块。
"""
from collections import defaultdict
from typing import Any, Dict, List

from langchain_core.messages import AnyMessage

MAX_HISTORY_MESSAGES = 20  # 最多带 20 条历史，防止 token 爆炸

_histories: Dict[str, List[AnyMessage]] = defaultdict(list)


def load_history(session_id: str) -> List[AnyMessage]:
    return list(_histories[session_id])


def save_messages(session_id: str, messages: List[AnyMessage]) -> None:
    _histories[session_id] = list(messages)[-MAX_HISTORY_MESSAGES:]
