# -*- coding: utf-8 -*-
"""全局配置与命令行参数。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

# py/fofa
fofa_DIR = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    fofa_dir: Path = fofa_DIR
    config_dir: Path = field(default_factory=lambda: fofa_DIR / "config")
    output_dir: Path = field(default_factory=lambda: fofa_DIR / "output")

    # ---- 测速 ----
    # 默认按分辨率取阈值（见 resolution.SPEED_THRESHOLD_KBPS）；
    # 显式指定 threshold_kbps 则所有源统一使用该阈值。
    threshold_kbps: float | None = None
    https_verify: bool = False             # 是否校验 HTTPS 证书
    connect_timeout: float = 6.0           # 建连超时
    read_timeout: float = 8.0              # 单次读取超时
    test_timeout: float = 20.0             # 单个源的总耗时上限
    max_bytes: int = 3072 * 1024           # 单源最多下载多少字节
    soft_bytes: int = 768 * 1024           # 快源攒够这么多字节且窗口足够就提前收手
    soft_window: float = 2.5               # 软阈值对应的最短测速窗口（秒）
    min_bytes: int = 20 * 1024             # 低于此数据量视为无效流
    playlist_max_bytes: int = 512 * 1024   # m3u8 播放列表最大读取量
    max_segments: int = 4                  # 最多取几个分片测速
    max_variants: int = 3                  # 主播放列表最多尝试几个清晰度变体

    # ---- 测速准确度（关键）----
    # 1) 慢启动预热段不计入速度：TCP 从 0 爬到满速要 0.5~2s，
    #    短窗口里平均速度只有稳态的一半，是"能播却测不出"的主因之一。
    warmup: float = 1.0
    # 2) 用流自身码率作为判定基准：能流畅播放的定义是「下载速度 ≥ 码率」，
    #    而不是「下载速度 ≥ 某分辨率的人眼需求」。对没有分辨率元数据的源尤其重要。
    bitrate_aware: bool = True
    bitrate_margin: float = 1.35           # 码率冗余系数，留 35% 缓冲
    bitrate_min_ratio: float = 0.2         # 码率基准不得低于「档位阈值」的这个比例，防错误码率放太松
    bitrate_strict: bool = False           # True 时完全按码率判定（高码率源也会被收紧）
    min_floor_kbps: float = 100.0          # 任何源都不得低于此速度，挡住劣质源
    # 3) 首轮高并发会互相抢带宽，临界源用低并发补测一次
    retest: bool = True
    retest_ratio: float = 0.6              # 首轮达到目标的百分之多少才值得重测
    retest_workers: int = 8                # 重测并发，远低于首轮
    retest_max: int = 1500                 # 重测数量上限，防止无限拖延
    strict: bool = False                   # 严格模式：退回旧的单轮判定行为

    # ---- 并发 ----
    workers: int = 96
    per_host_workers: int = 6              # 同一 host 的并发上限，防止把源站打死

    # ---- 输出 ----
    max_urls_per_channel: int = 6          # 每个频道最多保留几个可用地址
    keep_non_http: bool = False            # 是否保留 rtmp/rtsp 等非 HTTP 协议源
    include_local: bool = True             # 是否把 local.txt 合并进输出

    # ---- 黑名单 ----
    blacklist_threshold: int = 3           # 累计失败多少次后拉黑
    blacklist_ttl_days: int = 7            # 黑名单有效期（天），过期自动重试

    # ---- 元数据 ----
    epg_url: str = (
        "https://gh-proxy.com/https://raw.githubusercontent.com/"
        "adminouyang/231006/refs/heads/main/py/fofa/EPG/epg.xml"
    )
    logo_base: str = "https://codeberg.org/ou-yang/fofa/raw/branch/main/LOGO/"

    # ---- 运行控制 ----
    verbose: bool = False
    limit: int = 0                         # >0 时只处理前 N 个源，便于调试
    skip_test: bool = False                # 只做合并/改名，不测速
    self_test: bool = False                # 离线自检

    @property
    def subscribe_file(self) -> Path:
        return self.config_dir / "subscribe.txt"

    @property
    def demo_file(self) -> Path:
        return self.config_dir / "demo.txt"

    @property
    def blacklist_file(self) -> Path:
        return self.config_dir / "blacklist.txt"

    @property
    def local_file(self) -> Path:
        return self.config_dir / "local.txt"

    @property
    def log_file(self) -> Path:
        return self.output_dir / "sort.log"

    @property
    def ipv4_dir(self) -> Path:
        return self.output_dir / "ipv4"

    @property
    def ipv6_dir(self) -> Path:
        return self.output_dir / "ipv6"


def parse_args(argv: list[str] | None = None) -> Settings:
    parser = argparse.ArgumentParser(
        description="IPfofa 直播源检测脚本：拉取订阅 -> 校正频道名 -> 测速 -> 输出 txt/m3u"
    )
    parser.add_argument("--workers", type=int, default=None, help="并发线程数，默认 96")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="强制统一速度阈值 KB/s（默认按分辨率判定：8K/2048 4K/1900 1080p/465 720p/282 …）",
    )
    parser.add_argument("--timeout", type=float, default=None, help="单源总超时（秒），默认 20")
    parser.add_argument("--max-per-channel", type=int, default=None, help="每频道保留地址数，默认 6")
    parser.add_argument("--verify", action="store_true", help="强制校验 HTTPS 证书")
    parser.add_argument("--keep-non-http", action="store_true", help="保留 rtmp/rtsp 等非 HTTP 源")
    parser.add_argument("--no-local", action="store_true", help="不合并 local.txt")
    parser.add_argument("--skip-test", action="store_true", help="跳过测速，仅合并与改名")
    parser.add_argument("--limit", type=int, default=0, help="只处理前 N 个源（调试用）")
    parser.add_argument("--self-test", action="store_true", help="离线自检：不联网，验证解析与输出逻辑")
    parser.add_argument("--verbose", "-v", action="store_true", help="输出更多日志")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式：不做稳态修正、不按码率放宽、不重测（回到旧的单轮判定）",
    )
    parser.add_argument("--no-retest", action="store_true", help="只跑一轮，不做临界源重测")
    parser.add_argument(
        "--warmup", type=float, default=None, help="慢启动预热秒数，不计入速度，默认 1.0；0 表示不剔除"
    )
    parser.add_argument(
        "--bitrate-margin", type=float, default=None, help="码率冗余系数，默认 1.35"
    )
    parser.add_argument(
        "--floor", type=float, default=None, help="最低速度要求 KB/s，默认 100"
    )
    parser.add_argument(
        "--bitrate-strict",
        action="store_true",
        help="完全按流码率判定（连高码率源也按真实需求收紧），默认只放宽不收紧",
    )
    args = parser.parse_args(argv)

    s = Settings()
    if args.workers:
        s.workers = args.workers
    if args.threshold:
        s.threshold_kbps = args.threshold
    if args.timeout:
        s.test_timeout = args.timeout
    if args.max_per_channel:
        s.max_urls_per_channel = args.max_per_channel
    s.https_verify = bool(args.verify)
    s.keep_non_http = bool(args.keep_non_http)
    s.include_local = not args.no_local
    s.skip_test = bool(args.skip_test)
    s.limit = args.limit or 0
    s.self_test = bool(args.self_test)
    s.verbose = bool(args.verbose)

    if args.warmup is not None:
        s.warmup = max(args.warmup, 0.0)
    if args.bitrate_margin:
        s.bitrate_margin = max(args.bitrate_margin, 1.0)
    if args.floor is not None:
        s.min_floor_kbps = max(args.floor, 0.0)
    if args.no_retest:
        s.retest = False
    if args.bitrate_strict:
        s.bitrate_strict = True
    if args.strict:
        # 一次性回到旧行为：不剔慢启动、不按码率放宽、不重测、短窗口
        s.strict = True
        s.warmup = 0.0
        s.bitrate_aware = False
        s.retest = False
        s.soft_window = 1.0
    return s
