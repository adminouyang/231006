# -*- coding: utf-8 -*-
"""失效域名 / IP:端口 黑名单：避免每轮重复测速。"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from .sources import url_host, url_hostport

TIME_FMT = "%Y-%m-%d %H:%M:%S"

HEADER = """\
# 失效源黑名单（脚本自动维护，可手工编辑）
# 只有「返回错误状态码」的源才会入库；超时、连不上、速度不达标一律不记录
# 格式: host:port,失败次数,最后失败时间,原因
# 失败次数按「轮」累加：同一轮里同一主机的多个频道只算一次，
# 所以要连续多轮都返回错误状态码才会真正被跳过
# 也可只写 host:port 或 host（代表该主机所有端口），视为失效
"""

# 这些状态码属于临时抖动，不作为失效依据
TRANSIENT_STATUS = (408, 425, 429)


def is_dead_status(status: int) -> bool:
    """只有服务端明确返回错误状态码才算失效。"""
    return status >= 400 and status not in TRANSIENT_STATUS


@dataclass
class BlackEntry:
    key: str
    count: int = 1
    last: str = ""
    reason: str = ""

    def expired(self, ttl_days: int) -> bool:
        if ttl_days <= 0:
            return False
        try:
            last = datetime.strptime(self.last, TIME_FMT)
        except (TypeError, ValueError):
            return False
        return datetime.now() - last > timedelta(days=ttl_days)


class Blacklist:
    def __init__(self, path: Path, ttl_days: int = 7, threshold: int = 3) -> None:
        self.path = path
        self.ttl_days = ttl_days
        self.threshold = threshold
        self.entries: dict[str, BlackEntry] = {}
        self._lock = threading.Lock()
        # 本轮已经记过的主机：同一台服务器下的几十个频道只算一次失败，
        # 否则「累计 3 次」会变成「一轮就拉黑」，一次网络抖动就能把整台主机废掉
        self._struck: set[str] = set()

    # ------------------------------------------------------------------ #
    @classmethod
    def load(cls, path: Path, ttl_days: int = 7, threshold: int = 3) -> "Blacklist":
        bl = cls(path, ttl_days, threshold)
        if not path.exists():
            return bl
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            key = parts[0].rstrip("/").lower()
            if not key:
                continue
            # 只写了 host / host:port 的行视为手工拉黑，直接生效
            if len(parts) == 1:
                count = 9999
            else:
                try:
                    count = int(parts[1])
                except ValueError:
                    count = 9999
            last = parts[2] if len(parts) > 2 else ""
            reason = parts[3] if len(parts) > 3 else ("手工添加" if count == 9999 else "")
            bl.entries[key] = BlackEntry(key, count, last, reason)
        return bl

    # ------------------------------------------------------------------ #
    def is_bad(self, url: str) -> bool:
        for key in (url_hostport(url), url_host(url)):
            if not key:
                continue
            entry = self.entries.get(key)
            if entry is not None and entry.count >= self.threshold and not entry.expired(self.ttl_days):
                return True
        return False

    def record_fail(self, url: str, reason: str) -> None:
        key = url_hostport(url)
        if not key:
            return
        now = datetime.now().strftime(TIME_FMT)
        with self._lock:
            entry = self.entries.get(key)
            if entry is None:
                self.entries[key] = BlackEntry(key=key, count=1, last=now, reason=reason)
                self._struck.add(key)
                return
            # 同一台主机本轮只加一次计数：失败次数代表「连续失败的轮数」
            if key not in self._struck:
                entry.count += 1
                self._struck.add(key)
            entry.last = now
            entry.reason = reason

    def record_ok(self, url: str) -> None:
        with self._lock:
            self.entries.pop(url_hostport(url), None)

    # ------------------------------------------------------------------ #
    def save(self) -> None:
        now = datetime.now()
        # 未过期就留着：失败 1~2 次的记录会跨轮累计，达到阈值后自动跳过
        active = {k: v for k, v in self.entries.items() if not v.expired(self.ttl_days)}
        self.entries = dict(active)

        lines = [HEADER.rstrip("\n")]
        for key in sorted(active):
            entry = active[key]
            reason = (entry.reason or "").replace(",", " ").strip()[:40]
            last = entry.last or now.strftime(TIME_FMT)
            lines.append(f"{key},{entry.count},{last},{reason}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def __len__(self) -> int:
        return len(self.entries)
