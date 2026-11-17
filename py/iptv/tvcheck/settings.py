# -*- coding: utf-8 -*-
"""全局配置与命令行参数。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

# py/TV
TV_DIR = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    tv_dir: Path = TV_DIR
    config_dir: Path = field(default_factory=lambda: TV_DIR / "config")
    output_dir: Path = field(default_factory=lambda: TV_DIR / "output")

    # ---- 测速 ----
    # 默认按分辨率取阈值（见 resolution.SPEED_THRESHOLD_KBPS）；
    # 显式指定 threshold_kbps 则所有源统一使用该阈值。
    threshold_kbps: float | None = None
    https_verify: bool = False             # 是否校验 HTTPS 证书
    connect_timeout: float = 6.0           # 建连超时
    read_timeout: float = 8.0              # 单次读取超时
    test_timeout: float = 24.0             # 单个源的总耗时上限
    max_bytes: int = 6144 * 1024           # 单源最多下载多少字节
    soft_bytes: int = 1280 * 1024          # 快源攒够这么多字节且窗口足够就提前收手
    soft_window: float = 3.0               # 软阈值对应的最短测速窗口（秒）
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
    # 只有「差一点点」的源才值得补测：临界源（≥60%）已经会输出，
    # 再花 8 并发去补测上千个临界源只会把总耗时拉长十几分钟。
    retest_ratio: float = 0.85             # 首轮达到目标的百分之多少才值得重测
    retest_workers: int = 8                # 重测并发，远低于首轮
    retest_max: int = 600                  # 重测数量上限，防止无限拖延
    strict: bool = False                   # 严格模式：退回旧的单轮判定行为
    # 4) 分级输出：检测机（GitHub runner）到源的跨境链路往往比用户家宽差一个量级，
    #    「在这台机器上跑不到标称速度」不等于「用户那边播不动」。
    #    因此达不到硬阈值的源不直接丢弃，而是标成「临界」排在达标源之后。
    weak_enabled: bool = True
    weak_ratio: float = 0.6                # 稳态速度达到目标的这个比例即视为临界可用
    peak_window: float = 2.0               # 峰值速度的滑动窗口（秒），抗抖动

    # ---- 内容校验（拿到数据 ≠ 能播出画面）----
    # 有的源 HTTP 200、字节数也够，但载荷是 DRM 加密的，或者干脆是张静止图片。
    # 这类源速度再快也没有意义，必须在测速之后再过一道内容关。
    reject_drm: bool = True                # 拒绝 DRM 加密载荷 / 不可解的加密播放列表
    reject_audio: bool = True              # 拒绝只有音频轨的源（广播频道不是电视频道）
    static_detect: bool = True             # 拒绝静止画面（帧大小中位数极低）
    min_live_seconds: float = 600.0        # 点播列表总时长低于此值视为短片，0 表示不限制

    # ---- 并发 ----
    workers: int = 96
    per_host_workers: int = 6              # 同一 host 的并发上限，防止把源站打死

    # ---- 输出 ----
    # 同一频道按分辨率档位从高到低写入：先铺满 1080p，名额没满再用 720p 补，
    # 总数封顶。「档位:名额」之外的档位（8K/4K 等）直接用剩余名额。
    max_urls_per_channel: int = 8          # 每个频道最多保留几个可用地址
    tier_quota: dict[str, int] = field(
        default_factory=lambda: {"1080p": 4, "720p": 4}
    )
    tier_fill: bool = True                 # 高分辨率档位不够时，允许 720p 及以下补满总名额
    keep_non_http: bool = False            # 是否保留 rtmp/rtsp 等非 HTTP 协议源
    include_local: bool = True             # 是否把 local.txt 合并进输出

    # ---- 黑名单 ----
    blacklist_threshold: int = 3           # 累计失败多少次后拉黑
    blacklist_ttl_days: int = 7            # 黑名单有效期（天），过期自动重试

    # ---- 元数据 ----
    epg_url: str = (
        "https://gh-proxy.com/https://raw.githubusercontent.com/"
        "adminouyang/231006/refs/heads/main/py/TV/EPG/epg.xml"
    )
    logo_base: str = "https://codeberg.org/ou-yang/TV/raw/branch/main/LOGO/"

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
        description="IPTV 直播源检测脚本：拉取订阅 -> 校正频道名 -> 测速 -> 输出 txt/m3u"
    )
    parser.add_argument("--workers", type=int, default=None, help="并发线程数，默认 96")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="强制统一速度阈值 KB/s（默认按分辨率判定：8K/2048 4K/1900 1080p/465 720p/282 …）",
    )
    parser.add_argument("--timeout", type=float, default=None, help="单源总超时（秒），默认 20")
    parser.add_argument(
        "--max-per-channel", type=int, default=None, help="每频道保留地址数，默认 8"
    )
    parser.add_argument(
        "--tier-quota",
        default=None,
        help="每档位名额，默认 1080p:4,720p:4（按分辨率优先级依次填充，总数见 --max-per-channel）",
    )
    parser.add_argument(
        "--no-tier-fill",
        action="store_true",
        help="档位名额不足时不补满（默认 1080p 不够会用 720p 补到总数）",
    )
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
    parser.add_argument(
        "--no-weak",
        action="store_true",
        help="关闭临界源输出（只输出确实达到阈值的源）",
    )
    parser.add_argument(
        "--weak-ratio",
        type=float,
        default=None,
        help="临界源门槛系数，默认 0.6（达到目标的 60%% 就标为临界可用）",
    )
    parser.add_argument(
        "--keep-drm", action="store_true", help="保留 DRM 加密源（默认剔除，播放器放不出画面）"
    )
    parser.add_argument(
        "--keep-audio", action="store_true", help="保留纯音频源（默认剔除，电台不是电视频道）"
    )
    parser.add_argument(
        "--no-static", action="store_true", help="保留静止画面源（默认剔除）"
    )
    parser.add_argument(
        "--min-live",
        type=float,
        default=None,
        help="点播列表最短时长（秒），低于此值视为短片，默认 600；0 表示不限制",
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
        s.max_urls_per_channel = max(args.max_per_channel, 1)
    if args.tier_quota:
        quota: dict[str, int] = {}
        for part in args.tier_quota.replace("，", ",").split(","):
            name, _, value = part.partition(":")
            name, value = name.strip(), value.strip()
            if name and value.isdigit():
                quota[name] = int(value)
        if quota:
            s.tier_quota = quota
    if args.no_tier_fill:
        s.tier_fill = False
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
    if args.no_weak:
        s.weak_enabled = False
    if args.weak_ratio is not None:
        s.weak_ratio = min(max(args.weak_ratio, 0.0), 1.0)
    if args.keep_drm:
        s.reject_drm = False
    if args.keep_audio:
        s.reject_audio = False
    if args.no_static:
        s.static_detect = False
    if args.min_live is not None:
        s.min_live_seconds = max(args.min_live, 0.0)
    if args.strict:
        # 一次性回到旧行为：不剔慢启动、不按码率放宽、不重测、短窗口、不要临界源
        s.strict = True
        s.warmup = 0.0
        s.bitrate_aware = False
        s.retest = False
        s.weak_enabled = False
        s.soft_window = 1.0
    return s
