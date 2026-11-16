# -*- coding: utf-8 -*-
"""数据结构。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Candidate:
    """一个待输出/待测速的 频道-地址 条目。"""

    name: str                     # 展示名（已按 demo.txt 校正）
    name_key: str                 # 归一化频道 key
    group: str                    # 标准分组
    url: str
    ipver: str = "ipv4"           # ipv4 / ipv6
    local: bool = False           # 来自 local.txt，不参与测速
    matched: bool = False         # 是否命中 demo.txt 别名
    logo: str = ""                # 源自带台标
    testable: bool = True         # 是否可测速（非 HTTP 协议为 False）
    resolution: str = "unknown"   # 分辨率档位：8K/4K/1080p/720p/…/unknown
    threshold: float = 0.0        # 实际使用的判定目标 KB/s
    basis: str = ""               # 判定依据：分辨率阈值 / 码率基准
    ok: bool = False              # 达到该档位的硬阈值
    weak: bool = False            # 未达硬阈值，但可判定为"临界可用"（链路受限时仍会输出）
    speed: float = 0.0            # 稳态速度（判定依据）
    speed_avg: float = 0.0        # 全程平均速度，仅用于日志对照
    speed_peak: float = 0.0       # 最佳滑动窗口速度，抗抖动
    bitrate: float = 0.0          # 流自身码率 KB/s
    total_bytes: int = 0
    elapsed: float = 0.0
    reason: str = ""
    reject_kind: str = ""         # 内容不合格：drm（加密）/ static（静止画面）/ vod（点播短片）
    status: int = 0               # HTTP 状态码，0 表示没拿到响应
    method: str = "HTTP测速"
    ts: str = ""                  # 测速完成时间
