"""统一日志配置 — 仅由服务入口 (server.py) 调用一次

库内其余模块只需 `logging.getLogger(__name__)` 取用 logger，
不应自行添加 handler，避免重复输出。
"""

from __future__ import annotations

import logging
import os

_CONFIGURED = False

_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str | None = None) -> None:
    """配置 jianying_utils 包的日志输出（幂等，重复调用无副作用）。

    日志级别通过环境变量 JIANYING_LOG_LEVEL 控制（默认 INFO）。
    输出到 stdout，供 `docker logs` / gunicorn 直接查看。
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = (level or os.environ.get("JIANYING_LOG_LEVEL", "INFO")).upper()
    resolved_level = logging.getLevelName(level_name)
    if not isinstance(resolved_level, int):
        resolved_level = logging.INFO

    package_logger = logging.getLogger("jianying_utils")
    package_logger.setLevel(resolved_level)
    package_logger.propagate = False

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    package_logger.addHandler(handler)

    # uvicorn/gunicorn 自身的 access/error logger 保持默认行为，不受影响
    _CONFIGURED = True
