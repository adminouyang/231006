# -*- coding: utf-8 -*-
"""分辨率档位与对应速度阈值。

判定优先级：
    1. m3u8 主播放列表里的 RESOLUTION=1920x1080（最可靠，来自源本身）
    2. 频道名里的分辨率线索（4K / 1080P / 超清 / 高清 …）
    3. 都没有 -> unknown
"""

from __future__ import annotations

import re

# 各分辨率速度阈值（KB/s）
SPEED_THRESHOLD_KBPS: dict[str, float] = {
    "8K": 2048,
    "4K": 1900,
    "1080p": 465,
    "720p": 282,
    "576p": 144,
    "540p": 130,
    "480p": 125,
    "360p": 60,
    "unknown": 1024,
}

ORDER = ("8K", "4K", "1080p", "720p", "576p", "540p", "480p", "360p", "unknown")

UNKNOWN = "unknown"

# 频道名里的显式分辨率标记（小写匹配，自上而下）
_NAME_RULES: tuple[tuple[str, str], ...] = (
    (r"8k|4320[pi]?|7680", "8K"),
    (r"4k|2160[pi]?|uhd", "4K"),
    (r"1080[pi]?", "1080p"),
    (r"720p", "720p"),
    (r"576[pi]?", "576p"),
    (r"540p", "540p"),
    (r"480[pi]?|ntsc", "480p"),
    (r"360p", "360p"),
)

# 中文画质描述（必须放在显式标记之后，且“超高清”要先于“高清”）
_WORD_RULES: tuple[tuple[str, str], ...] = (
    ("超高清", "4K"),
    ("超清", "1080p"),
    ("蓝光", "1080p"),
    ("高清", "720p"),
    ("标清", "576p"),
)


def threshold_for(bucket: str, override: float | None = None) -> float:
    """取档位对应的阈值；override 不为空时统一使用它。"""
    if override:
        return float(override)
    return float(SPEED_THRESHOLD_KBPS.get(bucket or UNKNOWN, SPEED_THRESHOLD_KBPS[UNKNOWN]))


def bucket_from_size(width: int | None, height: int | None) -> str:
    """按画面高度归档（宽高任一缺失则返回 unknown）。"""
    if not height or not width:
        return UNKNOWN
    if height >= 4320 or width >= 7680:
        return "8K"
    if height >= 2160 or width >= 3840:
        return "4K"
    if height >= 1080:
        return "1080p"
    if height >= 720:
        return "720p"
    if height >= 576:
        return "576p"
    if height >= 540:
        return "540p"
    if height >= 480:
        return "480p"
    if height >= 360:
        return "360p"
    return UNKNOWN


def from_text(text: str) -> str:
    """从频道名里猜分辨率档位，猜不到返回空串。"""
    if not text:
        return ""
    low = str(text).lower()
    for pattern, bucket in _NAME_RULES:
        if re.search(pattern, low):
            return bucket
    for word, bucket in _WORD_RULES:
        if word in text:
            return bucket
    return ""


def describe_table() -> str:
    """日志表头用的一行说明。"""
    parts = [f"{name}={SPEED_THRESHOLD_KBPS[name]:g}" for name in ORDER]
    return " ".join(parts) + " KB/s"
