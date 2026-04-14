"""
Streamlit适配器层

将Streamlit的session_state适配为通用接口
"""

from typing import TypeVar, Generic, Optional, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime

T = TypeVar('T')


class SessionStateAdapter:
    """
    Session State 适配器

    抽象Streamlit特定的session_state操作
    """

    def __init__(self, prefix: str = ""):
        self._prefix = prefix
        try:
            import streamlit as st
            self._st = st
        except ImportError:
            self._st = None

    def _full_key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def get(self, key: str, default: T = None) -> T:
        if self._st is None:
            return default
        return self._st.session_state.get(self._full_key(key), default)

    def set(self, key: str, value: T) -> None:
        if self._st is None:
            return
        self._st.session_state[self._full_key(key)] = value

    def has(self, key: str) -> bool:
        if self._st is None:
            return False
        return self._full_key(key) in self._st.session_state

    def append_to_list(self, key: str, value: T, max_size: int = None) -> List[T]:
        lst = self.get(key, [])
        if lst is None:
            lst = []
        lst = lst.copy()
        lst.append(value)
        if max_size and len(lst) > max_size:
            lst = lst[-max_size:]
        self.set(key, lst)
        return lst

    def increment(self, key: str, default: int = 0) -> int:
        current = self.get(key, default)
        new_value = current + 1
        self.set(key, new_value)
        return new_value


class LogAdapter:
    """日志适配器"""

    def __init__(
        self,
        state_adapter: SessionStateAdapter,
        log_key: str = "behavior_logs",
        max_logs: int = 100
    ):
        self._state = state_adapter
        self._log_key = log_key
        self._max_logs = max_logs

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self._state.append_to_list(self._log_key, entry, self._max_logs)

    def get_logs(self, count: int = None) -> List[str]:
        logs = self._state.get(self._log_key, [])
        if count:
            return logs[-count:]
        return logs


def st_async(func: Callable) -> Callable:
    """Streamlit异步装饰器"""
    import asyncio
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(func(*args, **kwargs))
    return wrapper
