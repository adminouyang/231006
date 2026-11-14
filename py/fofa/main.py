#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IPfofa 直播源检测入口。

流程：
    1. 读取 config/subscribe.txt 中的远程订阅，拉取并解析 txt / m3u
    2. 读取 config/local.txt 本地源（不测速，只做频道名校正）
    3. 用 config/demo.txt 校正频道名、归类分组
    4. 过滤 config/blacklist.txt 中的失效主机（只按 HTTP 状态码判定）
    5. 多线程测速，按该源的分辨率档位取阈值判定是否输出
    6. 输出 output/ipv4、output/ipv6 下的 txt + m3u，以及 output/sort.log

用法：
    python py/fofa/main.py                    # 全量检测
    python py/fofa/main.py --limit 2 -v       # 只跑前 2 个订阅源，调试用
    python py/fofa/main.py --skip-test        # 只合并改名，不测速
"""

from __future__ import annotations

import sys
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

fofa_DIR = Path(__file__).resolve().parent
if str(fofa_DIR) not in sys.path:
    sys.path.insert(0, str(fofa_DIR))

from fofacheck.blacklist import Blacklist, is_dead_status  # noqa: E402
from fofacheck.models import Candidate  # noqa: E402
from fofacheck.names import ChannelDB, clean_name, normalize  # noqa: E402
from fofacheck.resolution import (  # noqa: E402
    UNKNOWN,
    describe_table,
    from_text as resolution_from_text,
    threshold_for,
)
from fofacheck.settings import Settings, parse_args  # noqa: E402
from fofacheck.sources import (  # noqa: E402
    Entry,
    classify_ipver,
    fetch_text,
    is_http,
    normalize_url,
    parse_text,
    read_subscribe,
    url_host,
)
from fofacheck.speedtest import SpeedTester  # noqa: E402
from fofacheck.writer import (  # noqa: E402
    build_groups,
    count_stats,
    write_log,
    write_m3u,
    write_txt,
)

TIME_FMT = "%Y-%m-%d %H:%M:%S"


def log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------- #
# 1. 采集
# --------------------------------------------------------------------------- #
def load_remote(settings: Settings) -> tuple[list[Entry], int]:
    urls = read_subscribe(settings.subscribe_file)
    if settings.limit:
        urls = urls[: settings.limit]
    if not urls:
        log(f"[警告] {settings.subscribe_file} 中没有可用的订阅链接")
        return [], 0

    entries: list[Entry] = []
    for idx, url in enumerate(urls, 1):
        try:
            text = fetch_text(url)
            items = parse_text(text, source=url)
            entries.extend(items)
            log(f"[源 {idx}/{len(urls)}] {url} -> {len(items)} 条")
        except Exception as exc:  # noqa: BLE001
            log(f"[源 {idx}/{len(urls)}] {url} -> 拉取失败: {exc}")
    return entries, len(urls)


def load_local(settings: Settings) -> list[Entry]:
    path = settings.local_file
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    items = parse_text(text, source="local.txt")
    if items:
        log(f"[本地] {path.name} -> {len(items)} 条")
    return items


# --------------------------------------------------------------------------- #
# 2. 校正 + 去重
# --------------------------------------------------------------------------- #
def build_candidates(
    remote: list[Entry],
    local: list[Entry],
    db: ChannelDB,
    settings: Settings,
    blacklist: Blacklist,
) -> tuple[list[Candidate], dict[str, int]]:
    stats = {"raw": 0, "uniq": 0, "blocked": 0, "non_http": 0, "no_name": 0}
    seen: set[str] = set()
    candidates: list[Candidate] = []

    # 本地源优先占位：同一个地址既在本地又在远程时，以本地的人工命名为准
    pairs: list[tuple[Entry, bool]] = [(e, True) for e in local]
    pairs += [(e, False) for e in remote]

    for entry, is_local in pairs:
        url = normalize_url(entry.url)
        if not url:
            continue
        stats["raw"] += 1
        if url in seen:
            continue
        seen.add(url)
        stats["uniq"] += 1

        info = db.match(entry.name, entry.fofag_name)
        if info is not None:
            name, group, matched = info.name, info.group, True
        else:
            # 名称不在 demo.txt 里：不改名，统一归入模板的兜底分组（其它频道）
            name = clean_name(entry.name) or clean_name(entry.fofag_name)
            if not name:
                stats["no_name"] += 1
                continue
            group, matched = db.default_group, False

        key = normalize(name)
        if not key:
            stats["no_name"] += 1
            continue

        testable = True
        if not is_http(url):
            stats["non_http"] += 1
            if not settings.keep_non_http:
                continue
            testable = False
        if is_local:
            testable = False
        elif testable and blacklist.is_bad(url):
            stats["blocked"] += 1
            continue

        # 分辨率线索：优先用频道名判断，测速时若播放列表带 RESOLUTION 会被覆盖
        resolution = (
            resolution_from_text(name)
            or resolution_from_text(entry.name)
            or resolution_from_text(entry.fofag_name)
            or UNKNOWN
        )

        candidates.append(
            Candidate(
                name=name,
                name_key=key,
                group=group,
                url=url,
                ipver=classify_ipver(url),
                local=is_local,
                matched=matched,
                logo=entry.logo,
                testable=testable,
                resolution=resolution,
                threshold=threshold_for(resolution, settings.threshold_kbps),
                ok=not testable,
            )
        )
    return candidates, stats


# --------------------------------------------------------------------------- #
# 3. 测速
# --------------------------------------------------------------------------- #
def interleave(items: list[Candidate]) -> list[Candidate]:
    """按 host 轮转排队：避免同一台服务器的几十个频道占满线程队列。"""
    buckets: dict[str, deque[Candidate]] = defaultdict(deque)
    for c in items:
        buckets[url_host(c.url) or c.url].append(c)

    queues = list(buckets.values())
    out: list[Candidate] = []
    while queues:
        remain: list[deque[Candidate]] = []
        for q in queues:
            out.append(q.popleft())
            if q:
                remain.append(q)
        queues = remain
    return out


def run_tests(
    candidates: list[Candidate], settings: Settings, blacklist: Blacklist
) -> dict[str, int]:
    todo = interleave([c for c in candidates if c.testable])
    result = {"tested": 0, "passed": 0, "dead": 0, "retested": 0, "retest_pass": 0}
    if not todo:
        return result

    if settings.skip_test:
        stamp = datetime.now().strftime(TIME_FMT)
        for c in todo:
            c.ok = True
            c.speed = 0.0
            c.ts = stamp
            c.reason = "未测速"
        result["tested"] = len(todo)
        result["passed"] = len(todo)
        log(f"[测速] 已跳过，直接放行 {len(todo)} 个地址")
        return result

    tester = SpeedTester(settings)
    total = len(todo)
    started = time.monotonic()
    limit_desc = (
        f"统一 {settings.threshold_kbps:g}KB/s"
        if settings.threshold_kbps
        else f"按分辨率 {describe_table()}"
    )
    if settings.bitrate_aware and settings.threshold_kbps is None:
        limit_desc += f"，码率基准 ×{settings.bitrate_margin:g}（保底 {settings.min_floor_kbps:g}）"
    log(f"[测速] 共 {total} 个地址，并发 {settings.workers}，阈值 {limit_desc}")

    with ThreadPoolExecutor(max_workers=settings.workers) as pool:
        futures = {pool.submit(tester.test, c.url, c.resolution): c for c in todo}
        for done, future in enumerate(as_completed(futures), 1):
            cand = futures[future]
            try:
                res = future.result()
            except Exception as exc:  # noqa: BLE001
                res = None
                cand.reason = f"异常:{type(exc).__name__}"
            if res is not None:
                absorb(cand, res)
            cand.ts = datetime.now().strftime(TIME_FMT)

            if cand.ok:
                blacklist.record_ok(cand.url)
                result["passed"] += 1
            elif is_dead_status(cand.status):
                # 只有明确的 HTTP 错误状态码才写进黑名单
                blacklist.record_fail(cand.url, f"HTTP {cand.status}")
                result["dead"] += 1

            if done % 50 == 0 or done == total:
                log(
                    f"[测速] {done}/{total} | 通过 {result['passed']} | "
                    f"{time.monotonic() - started:.1f}s"
                )
    result["tested"] = total

    if settings.retest:
        retest_borderline(todo, settings, blacklist, result)

    return result


def absorb(cand: Candidate, res, suffix: str = "") -> None:
    """把一次测速结果写回候选，速度取历史最好值。"""
    cand.ok = res.ok
    if res.speed_kbps > cand.speed:
        cand.speed = res.speed_kbps
    cand.speed_avg = res.speed_avg or cand.speed_avg
    cand.total_bytes = max(cand.total_bytes, res.total_bytes)
    cand.elapsed = res.elapsed
    cand.method = res.method + suffix
    cand.status = res.status
    cand.resolution = res.resolution or cand.resolution
    cand.threshold = res.threshold or cand.threshold
    if res.basis:
        cand.basis = res.basis
    if res.bitrate_kbps:
        cand.bitrate = res.bitrate_kbps
    cand.reason = res.reason


def retest_borderline(
    todo: list[Candidate], settings: Settings, blacklist: Blacklist, result: dict[str, int]
) -> None:
    """临界源低并发重测。

    首轮 96 并发时每条源都在抢同一根出口带宽，测出来的速度天然偏低；
    真正"能流畅播放却卡在阈值线下"的源，绝大多数在低并发下能回到目标之上。
    因此这轮只挑差一点的源，用很小的并发补测，取两次的最好成绩。
    """
    borderline: list[Candidate] = []
    unlucky: list[Candidate] = []
    for c in todo:
        if c.ok or c.status >= 400:
            continue
        if c.threshold > 0 and c.speed >= c.threshold * settings.retest_ratio:
            borderline.append(c)
        elif c.speed <= 0 and c.reason.startswith(("读取超时", "连接超时", "数据量不足")):
            # 首轮大概率是被自己人挤超时的，低并发下值得再看一眼
            unlucky.append(c)

    if not borderline and not unlucky:
        return

    pool = borderline[: settings.retest_max]
    room = settings.retest_max - len(pool)
    if room > 0:
        pool += unlucky[:room]

    log(
        f"[重测] 临界 {len(borderline)} 个 + 疑似挤超时 {len(unlucky)} 个 "
        f"→ 取 {len(pool)} 个，并发 {settings.retest_workers}"
    )
    tester = SpeedTester(settings)
    started = time.monotonic()
    total = len(pool)
    with ThreadPoolExecutor(max_workers=settings.retest_workers) as pool_exec:
        futures = {pool_exec.submit(tester.test, c.url, c.resolution): c for c in pool}
        for done, future in enumerate(as_completed(futures), 1):
            cand = futures[future]
            try:
                res = future.result()
            except Exception:  # noqa: BLE001
                continue
            result["retested"] += 1
            if not res.valid:
                continue
            absorb(cand, res, suffix="(重测)")
            cand.ts = datetime.now().strftime(TIME_FMT)
            if cand.ok:
                blacklist.record_ok(cand.url)
                result["passed"] += 1
                result["retest_pass"] += 1
            if done % 50 == 0 or done == total:
                log(
                    f"[重测] {done}/{total} | 救回 {result['retest_pass']} | "
                    f"{time.monotonic() - started:.1f}s"
                )
    if result["retest_pass"]:
        log(f"[重测] 完成，救回 {result['retest_pass']} 个源")


# --------------------------------------------------------------------------- #
# 4. 输出
# --------------------------------------------------------------------------- #
def log_sort_key(c: Candidate, db: ChannelDB):
    return (
        db.group_index(c.group),
        db.order_of(c.name_key),
        c.name,
        0 if c.ok else 1,
        -c.speed,
    )


def main(argv: list[str] | None = None) -> int:
    settings = parse_args(argv)
    if settings.self_test:
        from fofacheck.selftest import run_selftest

        return run_selftest()

    started_at = datetime.now().strftime(TIME_FMT)
    started = time.monotonic()

    for folder in (settings.ipv4_dir, settings.ipv6_dir):
        folder.mkdir(parents=True, exist_ok=True)

    db = ChannelDB.load(settings.demo_file)
    blacklist = Blacklist.load(
        settings.blacklist_file, settings.blacklist_ttl_days, settings.blacklist_threshold
    )
    log(f"[配置] 别名 {len(db.alias)} 条 / 分组 {len(db.groups)} 个 / 黑名单 {len(blacklist)} 条")

    remote, source_count = load_remote(settings)
    local = load_local(settings) if settings.include_local else []

    candidates, stats = build_candidates(remote, local, db, settings, blacklist)
    log(
        f"[整理] 原始 {stats['raw']} | 去重后 {stats['uniq']} | "
        f"黑名单跳过 {stats['blocked']} | 非HTTP {stats['non_http']} | 待测 {len(candidates)}"
    )

    test_stats = run_tests(candidates, settings, blacklist)

    groups = build_groups(candidates, db, settings)
    v4_channels, v4_urls = count_stats(groups["ipv4"])
    v6_channels, v6_urls = count_stats(groups["ipv6"])

    # 全军覆没时不动上一轮结果，避免把可用列表覆盖成空文件
    if v4_channels + v6_channels == 0:
        log("[错误] 本轮没有产出任何可用频道，已保留上一轮的输出文件")
        write_log(
            settings.log_file,
            settings,
            sorted([c for c in candidates if c.testable], key=lambda c: log_sort_key(c, db)),
            {
                "sources": source_count,
                "raw": stats["raw"],
                "uniq": stats["uniq"],
                "blocked": stats["blocked"],
                "tested": test_stats["tested"],
                "passed": test_stats["passed"],
                "dead": test_stats["dead"],
                "retested": test_stats.get("retested", 0),
                "retest_pass": test_stats.get("retest_pass", 0),
                "cost": time.monotonic() - started,
            },
            started_at,
        )
        return 1

    write_txt(settings.ipv4_dir / "fofa.txt", groups["ipv4"])
    write_m3u(settings.ipv4_dir / "fofa.m3u", groups["ipv4"], settings)
    write_txt(settings.ipv6_dir / "fofa.txt", groups["ipv6"])
    write_m3u(settings.ipv6_dir / "fofa.m3u", groups["ipv6"], settings)

    blacklist.save()

    cost = time.monotonic() - started
    summary = {
        "sources": source_count,
        "raw": stats["raw"],
        "uniq": stats["uniq"],
        "blocked": stats["blocked"],
        "tested": test_stats["tested"],
        "passed": test_stats["passed"],
        "dead": test_stats["dead"],
        "retested": test_stats.get("retested", 0),
        "retest_pass": test_stats.get("retest_pass", 0),
        "cost": cost,
        "v4_channels": v4_channels,
        "v4_urls": v4_urls,
        "v6_channels": v6_channels,
        "v6_urls": v6_urls,
    }

    rows = sorted(
        [c for c in candidates if c.testable], key=lambda c: log_sort_key(c, db)
    )
    write_log(settings.log_file, settings, rows, summary, started_at)

    log("")
    log(
        f"[完成] 订阅 {source_count} 个 | 去重 {stats['uniq']} | 通过 {test_stats['passed']}"
        f"/{test_stats['tested']}"
        + (
            f"（重测救回 {test_stats['retest_pass']}）"
            if test_stats.get("retest_pass")
            else ""
        )
        + f" | 耗时 {cost:.1f}s"
    )
    log(f"[输出] IPv4: {v4_channels} 频道 / {v4_urls} 地址  ({settings.ipv4_dir})")
    log(f"[输出] IPv6: {v6_channels} 频道 / {v6_urls} 地址  ({settings.ipv6_dir})")
    log(f"[输出] 日志: {settings.log_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
