# -*- coding: utf-8 -*-
"""结果整理与输出：ipv4/ipv6 目录下的 txt、m3u 以及 sort.log。"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote

from .models import Candidate
from .names import ChannelDB
from .resolution import UNKNOWN, describe_table, threshold_for
from .settings import Settings


# --------------------------------------------------------------------------- #
# 工具
# --------------------------------------------------------------------------- #
def fmt_size(nbytes: int) -> str:
    kb = nbytes / 1024.0
    if kb >= 1024:
        return f"{kb / 1024:.2f}MB"
    return f"{kb:.1f}KB"


def fmt_num(value: float) -> str:
    return f"{value:.0f}" if abs(value - round(value)) < 0.01 else f"{value:.2f}"


def safe_name(name: str) -> str:
    """去掉会破坏 txt/m3u 结构的字符。"""
    return (name or "").replace(",", " ").replace('"', "").strip()


def logo_for(name: str, settings: Settings) -> str:
    return f"{settings.logo_base}{quote(name, safe='')}.png"


def _url_sort_key(c: Candidate) -> tuple[int, float]:
    if c.local:
        return (0, 0.0)
    if not c.testable:
        return (1, 0.0)
    return (2, -c.speed)


# --------------------------------------------------------------------------- #
# 分组排序
# --------------------------------------------------------------------------- #
def build_groups(
    candidates: list[Candidate], db: ChannelDB, settings: Settings
) -> dict[str, list[tuple[str, list[dict[str, Any]]]]]:
    """按 协议族 -> 分组 -> 频道 组织可用地址。"""
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for c in candidates:
        if not (c.ok or not c.testable):
            continue
        bkey = (c.ipver, c.name_key)
        bucket = buckets.get(bkey)
        if bucket is None:
            bucket = {"name": c.name, "key": c.name_key, "group": c.group, "items": []}
            buckets[bkey] = bucket
        bucket["items"].append(c)

    tree: dict[str, dict[str, list[dict[str, Any]]]] = {"ipv4": {}, "ipv6": {}}
    for (ipver, _key), bucket in buckets.items():
        items = sorted(bucket["items"], key=_url_sort_key)[: settings.max_urls_per_channel]
        tree.setdefault(ipver, {}).setdefault(bucket["group"], []).append(
            {"name": bucket["name"], "key": bucket["key"], "items": items}
        )

    out: dict[str, list[tuple[str, list[dict[str, Any]]]]] = {}
    for ipver in ("ipv4", "ipv6"):
        groups = tree.get(ipver) or {}
        ordered: list[tuple[str, list[dict[str, Any]]]] = []
        for gname in sorted(groups.keys(), key=lambda g: (db.group_index(g), g)):
            chans = sorted(groups[gname], key=lambda ch: (db.order_of(ch["key"]), ch["name"]))
            ordered.append((gname, chans))
        out[ipver] = ordered
    return out


def count_stats(groups: list[tuple[str, list[dict[str, Any]]]]) -> tuple[int, int]:
    channels = 0
    urls = 0
    for _gname, chans in groups:
        channels += len(chans)
        urls += sum(len(ch["items"]) for ch in chans)
    return channels, urls


# --------------------------------------------------------------------------- #
# 文件输出
# --------------------------------------------------------------------------- #
def write_txt(path: Path, groups: list[tuple[str, list[dict[str, Any]]]]) -> None:
    lines: list[str] = []
    for gname, chans in groups:
        if not chans:
            continue
        lines.append(f"{safe_name(gname)},#genre#")
        for ch in chans:
            name = safe_name(ch["name"])
            for c in ch["items"]:
                lines.append(f"{name},{c.url}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_m3u(
    path: Path, groups: list[tuple[str, list[dict[str, Any]]]], settings: Settings
) -> None:
    lines = [f'#EXTM3U x-tvg-url="{settings.epg_url}"']
    for gname, chans in groups:
        group = safe_name(gname)
        for ch in chans:
            name = safe_name(ch["name"])
            for c in ch["items"]:
                logo = c.logo or logo_for(name, settings)
                lines.append(
                    f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" '
                    f'group-title="{group}",{name}'
                )
                lines.append(c.url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_log(
    path: Path,
    settings: Settings,
    rows: list[Candidate],
    stats: dict[str, Any],
    started_at: str,
) -> None:
    """sort.log：表头 + 逐条测速结果（含分辨率与对应阈值） + 统计。"""
    if settings.threshold_kbps:
        threshold_line = f"速度阈值: {fmt_num(settings.threshold_kbps)}KB/s（统一阈值）"
    else:
        threshold_line = f"速度阈值: 按分辨率判定 {describe_table()}"

    lines = [
        f"测速日志 {started_at}",
        threshold_line,
        f"HTTPS验证: {settings.https_verify}",
    ]
    if settings.bitrate_aware and settings.threshold_kbps is None:
        lines.append(
            f"判定基准: 流码率优先（码率×{settings.bitrate_margin:g}，保底 "
            f"{settings.min_floor_kbps:g}KB/s，与分辨率阈值取较宽松者）"
        )
    lines.append(
        f"测速口径: 稳态速度（剔除前 {settings.warmup:g}s 慢启动）"
        + (
            f" | 临界重测: 开启（并发 {settings.retest_workers}，"
            f"线 {settings.retest_ratio:.0%}）"
            if settings.retest
            else " | 临界重测: 关闭"
        )
    )

    for c in rows:
        stamp = c.ts or started_at
        bucket = c.resolution or UNKNOWN
        threshold = c.threshold or threshold_for(bucket, settings.threshold_kbps)
        basis = c.basis or "分辨率阈值"
        if c.bitrate > 0:
            basis += f"（流码率 {c.bitrate:.0f}KB/s）"
        detail = (
            f"分辨率: {bucket} | 判定: {basis} | 速度: {c.speed:.2f}KB/s | "
            f"阈值: {threshold:g}KB/s"
        )
        if c.speed_avg > 0 and c.speed > 0:
            detail += f" | 均速: {c.speed_avg:.2f}KB/s"
        detail += f" | 数据量: {fmt_size(c.total_bytes)} | 总耗时: {c.elapsed:.2f}s"
        if c.status >= 400:
            detail += f" | HTTP {c.status}"

        if c.ok:
            lines.append(f"[{stamp}] ✅ 通过阈值 {c.method}: {c.name}, {c.url}")
            lines.append(detail)
        else:
            reason = c.reason or "未通过阈值"
            headline = "未通过阈值" if reason.startswith("速度") else reason
            lines.append(f"[{stamp}] ❌ {headline} {c.method}: {c.name}, {c.url}")
            lines.append(f"原因: {reason} | {detail}")

    lines.append("")
    lines.append("-" * 60)
    lines.append(
        "统计: 订阅源 {sources} | 原始地址 {raw} | 去重后 {uniq} | 黑名单跳过 {blocked} | "
        "测速 {tested} | 可用 {passed} | 状态码失效 {dead} | 耗时 {cost:.1f}s".format(
            sources=stats.get("sources", 0),
            raw=stats.get("raw", 0),
            uniq=stats.get("uniq", 0),
            blocked=stats.get("blocked", 0),
            tested=stats.get("tested", 0),
            passed=stats.get("passed", 0),
            dead=stats.get("dead", 0),
            cost=stats.get("cost", 0.0),
        )
    )
    if stats.get("retested"):
        lines.append(
            f"重测: 补测 {stats.get('retested', 0)} 个临界源，救回 "
            f"{stats.get('retest_pass', 0)} 个"
        )
    lines.append(
        "输出: IPv4 频道 {v4c} / 地址 {v4u} | IPv6 频道 {v6c} / 地址 {v6u}".format(
            v4c=stats.get("v4_channels", 0),
            v4u=stats.get("v4_urls", 0),
            v6c=stats.get("v6_channels", 0),
            v6u=stats.get("v6_urls", 0),
        )
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
