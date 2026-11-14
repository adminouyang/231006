# -*- coding: utf-8 -*-
"""测速模块：兼容 m3u8(HLS) / 直连 TS / FLV / MP4 等各类源，并按分辨率判定阈值。

为什么会出现「明明能流畅播放，却判为未达标」——四个叠加原因，这里逐个修正：

    1. 短窗口 + 慢启动
       TCP 从 0 爬到满速要 0.5~2s，1 秒窗口里算出来的平均速度只有稳态的一半左右。
       -> 记录「时间-累计字节」采样点，丢掉 warmup 那一段，只用稳态窗口算速度。

    2. 判定基准错位
       拿「人眼需要多少带宽」当门槛，但能不能播的定义是「下载速度 ≥ 流自身码率」。
       一个 480p 的源码率可能只有 300KB/s，却要求它跑 1024KB/s（unknown 档），必死。
       -> 从 #EXTINF 时长与分片字节算出真实码率，用 max(码率 × 冗余, 保底) 作为目标，
          并且只在与分辨率阈值取较宽松者，绝不收紧对已知高分辨率源的要求。

    3. 并发自己打满带宽
       96 个线程同时下载，每条只分到总带宽的零头。-> 临界源交给上层低并发重测。

    4. 单次测量无容错
       源本身在波动，一次不达标就淘汰。-> 同上，重测取最好成绩。
"""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field
from typing import Iterator
from urllib.parse import urljoin, urlparse

import requests
import urllib3
from requests.adapters import HTTPAdapter

from .resolution import UNKNOWN, bucket_from_size, threshold_for
from .settings import Settings
from .videoprobe import probe_resolution

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

UA_LIST = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "okhttp/3.12.12",
    "VLC/3.0.20 LibVLC/3.0.20",
)

BASE_HEADERS = {"Accept": "*/*", "Accept-Encoding": "identity", "Connection": "keep-alive"}

PLAYLIST_TAG = b"#EXTM3U"

# 这些状态码属于临时抖动，允许换一套请求头重试
RETRY_STATUS = (403, 408, 425, 429, 500, 502, 503, 504)


@dataclass
class TestResult:
    url: str
    ok: bool = False          # 是否达到该源的判定目标
    valid: bool = False       # 是否拿到了可用的测速数据
    speed_kbps: float = 0.0   # 稳态速度（去掉慢启动），判定依据
    speed_avg: float = 0.0    # 全程平均速度，仅用于日志对照
    total_bytes: int = 0
    elapsed: float = 0.0
    reason: str = ""
    method: str = "HTTP测速"
    retry: bool = False
    status: int = 0           # 最近一次 HTTP 状态码，0 表示没拿到响应
    resolution: str = ""      # 解析出的档位
    threshold: float = 0.0    # 实际使用的判定目标 KB/s
    bitrate_kbps: float = 0.0  # 流自身码率 KB/s（实测优先，其次 BANDWIDTH 声明）
    basis: str = ""           # 判定依据：分辨率阈值 / 码率基准


@dataclass
class _Pumped:
    """一次连续读取的结果。"""

    buf: bytes = b""
    total: int = 0
    t_first: float = 0.0
    t_last: float = 0.0
    complete: bool = False                     # 是否读到了流末尾（而非被 limit 截断）
    marks: list[tuple[float, int]] = field(default_factory=list)  # (时间, 局部累计字节)


@dataclass
class _Fetched:
    """一个分片的抓取结果。"""

    n: int = 0
    status: int = 0
    tap: bytes = b""
    complete: bool = False
    size: int = 0        # Content-Length 声明的总长；0 表示未知


class _Meter:
    """累计下载字节与采样点，用于算「稳态吞吐」。

    多个响应（播放列表、各个分片）会依次 feed 进同一个 meter，
    采样点的累计字节要换算成全局值，这样跨分片也能正确剔除预热段。
    """

    __slots__ = ("nbytes", "first", "last", "marks")

    def __init__(self) -> None:
        self.nbytes = 0
        self.first = 0.0
        self.last = 0.0
        self.marks: list[tuple[float, int]] = []

    def feed(self, pumped: _Pumped) -> None:
        if pumped.total <= 0:
            return
        base = self.nbytes
        self.nbytes += pumped.total
        if self.first <= 0 or pumped.t_first < self.first:
            self.first = pumped.t_first
        if pumped.t_last > self.last:
            self.last = pumped.t_last
        cap = 4096
        for t, n in pumped.marks:
            if len(self.marks) >= cap:
                break
            self.marks.append((t, base + n))

    # -- 速度 ---------------------------------------------------------- #
    def average_kbps(self, elapsed: float) -> float:
        span = self.last - self.first
        if span <= 0.05:
            span = max(elapsed, 0.001)
        return self.nbytes / 1024.0 / span if span > 0 else 0.0

    def steady_kbps(self, elapsed: float, warmup: float = 0.0) -> float:
        """丢掉前 warmup 秒的慢启动阶段，用剩余窗口算速度。

        窗口本来就短于预热期时无法剔除，退回平均速度（否则会因为没有采样点算出 0）。
        """
        avg = self.average_kbps(elapsed)
        span = self.last - self.first
        if warmup <= 0 or span <= warmup * 1.4 or len(self.marks) < 3:
            return avg

        cut = self.first + warmup
        base_t = 0.0
        base_b = 0
        for t, n in self.marks:
            if t >= cut:
                base_t, base_b = t, n
                break
        if base_t <= 0:
            return avg

        sspan = self.last - base_t
        sbytes = self.nbytes - base_b
        if sspan < 0.5 or sbytes <= 0:
            # 稳态窗口太短，噪声大，宁可退回平均速度
            return avg
        return sbytes / 1024.0 / sspan


class SpeedTester:
    def __init__(self, settings: Settings) -> None:
        self.s = settings
        self._local = threading.local()
        self._host_sem: dict[str, threading.Semaphore] = {}
        self._host_lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # 基础设施
    # ------------------------------------------------------------------ #
    def _session(self) -> requests.Session:
        session = getattr(self._local, "session", None)
        if session is None:
            session = requests.Session()
            adapter = HTTPAdapter(pool_connections=8, pool_maxsize=16, max_retries=0)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            self._local.session = session
        return session

    def _sem(self, url: str) -> threading.Semaphore:
        key = urlparse(url).netloc.lower() or "unknown"
        with self._host_lock:
            sem = self._host_sem.get(key)
            if sem is None:
                sem = threading.Semaphore(self.s.per_host_workers)
                self._host_sem[key] = sem
            return sem

    def _plans(self, url: str) -> Iterator[tuple[dict, bool]]:
        """多套请求头/证书策略，覆盖需要 UA、防盗链、自签证书的源。"""
        origin = "{0.scheme}://{0.netloc}/".format(urlparse(url))
        yield ({**BASE_HEADERS, "User-Agent": UA_LIST[0]}, self.s.https_verify)
        yield ({**BASE_HEADERS, "User-Agent": UA_LIST[1]}, False)
        yield ({**BASE_HEADERS, "User-Agent": UA_LIST[0], "Referer": origin}, False)
        yield ({**BASE_HEADERS, "User-Agent": UA_LIST[2], "Referer": origin}, False)

    def test(self, url: str, fallback_resolution: str = UNKNOWN) -> TestResult:
        start = time.monotonic()
        result = TestResult(url=url, reason="未知错误")
        for headers, verify in self._plans(url):
            remaining = self.s.test_timeout - (time.monotonic() - start)
            if remaining <= 1.0:
                break
            try:
                with self._sem(url):
                    result = self._attempt(url, headers, verify, start, remaining)
            except requests.exceptions.SSLError:
                result = TestResult(
                    url=url, reason="SSL证书错误", retry=True, elapsed=time.monotonic() - start
                )
            except requests.exceptions.ConnectTimeout:
                result = TestResult(url=url, reason="连接超时", elapsed=time.monotonic() - start)
            except requests.exceptions.ReadTimeout:
                result = TestResult(url=url, reason="读取超时", elapsed=time.monotonic() - start)
            except requests.exceptions.ConnectionError:
                result = TestResult(
                    url=url, reason="连接失败", retry=True, elapsed=time.monotonic() - start
                )
            except requests.exceptions.RequestException as exc:
                result = TestResult(
                    url=url, reason=type(exc).__name__, elapsed=time.monotonic() - start
                )
            except Exception as exc:  # noqa: BLE001
                result = TestResult(
                    url=url, reason=f"异常:{type(exc).__name__}", elapsed=time.monotonic() - start
                )
            if result.valid or not result.retry:
                break

        if result.valid:
            self._finalize(result, fallback_resolution)
        result.elapsed = time.monotonic() - start
        return result

    def _finalize(self, result: TestResult, fallback_resolution: str) -> None:
        """决定判定目标：分辨率阈值 与 流码率需求 取较宽松者。

        - 码率基准只在「显式指定了统一阈值」或「关掉 bitrate_aware」时失效。
        - 默认取 min() 而不是替换：只放宽、绝不收紧已知高分辨率源的门槛，
          避免修误杀的同时引入新的误杀。需要双向精确判定时用 --bitrate-strict。
        - 三重下限：绝对保底、以及「档位阈值 × bitrate_min_ratio」，
          防止 EXTINF 与实际时长不符之类算出的错误码率把门槛放得过松。
        """
        bucket = result.resolution or fallback_resolution or UNKNOWN
        result.resolution = bucket
        tabled = threshold_for(bucket, self.s.threshold_kbps)
        target = tabled
        basis = f"{bucket} 阈值"

        if (
            self.s.bitrate_aware
            and self.s.threshold_kbps is None
            and result.bitrate_kbps > 0
        ):
            need = max(
                result.bitrate_kbps * self.s.bitrate_margin,
                self.s.min_floor_kbps,
                tabled * self.s.bitrate_min_ratio,
            )
            if self.s.bitrate_strict:
                target = need
                basis = f"码率基准 {result.bitrate_kbps:.0f}×{self.s.bitrate_margin:g}"
            elif need < tabled:
                target = need
                basis = f"码率基准 {result.bitrate_kbps:.0f}×{self.s.bitrate_margin:g}"
            else:
                basis = f"{bucket} 阈值（码率 {result.bitrate_kbps:.0f}）"

        result.threshold = target
        result.basis = basis
        result.ok = result.speed_kbps >= target
        if result.ok:
            result.reason = ""
        else:
            result.reason = f"速度 {result.speed_kbps:.2f}KB/s 低于 {basis} 的 {target:g}KB/s"

    # ------------------------------------------------------------------ #
    # 单次请求
    # ------------------------------------------------------------------ #
    def _attempt(
        self, url: str, headers: dict, verify: bool, start: float, budget: float
    ) -> TestResult:
        deadline = start + budget
        timeout = (min(self.s.connect_timeout, budget), min(self.s.read_timeout, budget))
        resp = self._session().get(
            url,
            headers=headers,
            stream=True,
            verify=verify,
            timeout=timeout,
            allow_redirects=True,
        )
        status = 0
        meter = _Meter()
        try:
            status = resp.status_code
            if status >= 400:
                return TestResult(
                    url=url,
                    reason=f"HTTP {status}",
                    elapsed=time.monotonic() - start,
                    retry=status in RETRY_STATUS,
                    status=status,
                )

            head = self._pump(resp, deadline, 16 * 1024, keep=16 * 1024)
            meter.feed(head)

            if not head.buf:
                return TestResult(
                    url=url, reason="无响应数据", elapsed=time.monotonic() - start, status=status
                )

            if head.buf.lstrip(b"\xef\xbb\xbf \t\r\n").startswith(PLAYLIST_TAG):
                return self._test_playlist(
                    url, resp.url, head, resp, meter, headers, verify, start, deadline, status
                )

            if self._is_error_body(head.buf):
                return TestResult(
                    url=url,
                    reason="返回网页/错误内容",
                    elapsed=time.monotonic() - start,
                    total_bytes=meter.nbytes,
                    status=status,
                )

            # 直连流（ts / flv / mp4 / mp3 …），继续读到上限
            remain = self.s.max_bytes - meter.nbytes
            probe = head.buf
            if remain > 0:
                tap = self._pump(
                    resp,
                    deadline,
                    remain,
                    keep=1024 * 1024,  # 直连流/组播常是长 GOP，多留一点才可能碰到关键帧里的 SPS
                    soft_bytes=self.s.soft_bytes,
                    soft_window=self.s.soft_window,
                )
                meter.feed(tap)
                probe = head.buf + tap.buf
        finally:
            resp.close()

        return self._measure(url, meter, start, "", status, probe)

    # ------------------------------------------------------------------ #
    # HLS
    # ------------------------------------------------------------------ #
    def _test_playlist(
        self,
        url: str,
        final_url: str,
        head: _Pumped,
        resp: requests.Response,
        meter: _Meter,
        headers: dict,
        verify: bool,
        start: float,
        deadline: float,
        status: int,
    ) -> TestResult:
        # 首包不足 16KB 且已读到流末尾，基本可判定整份播放列表已读完，避免服务端不关连接时白等
        remain = 0 if head.complete else max(self.s.playlist_max_bytes - len(head.buf), 0)
        rest = b""
        if remain:
            tail = self._pump(resp, deadline, remain, keep=remain)
            meter.feed(tail)
            rest = tail.buf

        base = final_url or url
        playlist = (head.buf + rest).decode("utf-8", "ignore").lstrip("\ufeff")

        resolution = ""
        declared_bps = 0
        if "#EXT-X-STREAM-INF" in playlist:
            for bandwidth, variant, bucket in self._variants(playlist, base)[: self.s.max_variants]:
                sub, sub_status = self._fetch_text(variant, headers, verify, deadline, meter)
                if sub and "#EXTINF" in sub:
                    playlist, base, resolution = sub, variant, bucket
                    declared_bps = bandwidth
                    break
                status = sub_status or status
            else:
                return TestResult(
                    url=url,
                    reason="清晰度列表无效",
                    elapsed=time.monotonic() - start,
                    total_bytes=meter.nbytes,
                    status=status,
                )

        segments = self._segments(playlist, base)
        if not segments:
            return TestResult(
                url=url,
                reason="播放列表为空",
                elapsed=time.monotonic() - start,
                total_bytes=meter.nbytes,
                status=status,
            )

        got = 0
        probe = b""
        bit_bytes = 0            # 只用「完整下载」的分片算码率
        bit_seconds = 0.0
        base_query = urlparse(base).query
        for seg, duration in segments[: self.s.max_segments]:
            if meter.nbytes >= self.s.max_bytes or time.monotonic() >= deadline:
                break
            limit = self.s.max_bytes - meter.nbytes
            part = self._fetch_to_meter(seg, headers, verify, deadline, meter, limit)
            if part.n <= 0 and base_query and "?" not in seg:
                # 部分源要求分片继承播放列表的 token
                part = self._fetch_to_meter(
                    f"{seg}?{base_query}", headers, verify, deadline, meter, limit
                )
            if part.n > 0:
                got += part.n
                if not probe:
                    probe = part.tap
                if duration > 0:
                    # 算码率优先用 Content-Length——不必把整个分片下完，省时间也更准
                    if part.size > 0:
                        bit_bytes += part.size
                        bit_seconds += duration
                    elif part.complete:
                        bit_bytes += part.n
                        bit_seconds += duration
            else:
                status = part.status or status
                if got > 0:
                    break
        if got <= 0:
            reason = "分片下载失败" + (f"（HTTP {status}）" if status >= 400 else "")
            return TestResult(
                url=url,
                reason=reason,
                elapsed=time.monotonic() - start,
                total_bytes=meter.nbytes,
                status=status,
            )

        bitrate = 0.0
        if bit_seconds > 0 and bit_bytes > 0:
            bitrate = bit_bytes / 1024.0 / bit_seconds
        elif declared_bps > 0:
            bitrate = declared_bps / 8.0 / 1024.0
        return self._measure(url, meter, start, resolution, status, probe, bitrate)

    @staticmethod
    def _variants(playlist: str, base: str) -> list[tuple[int, str, str]]:
        """解析主播放列表：(带宽, 地址, 分辨率档位)。"""
        out: list[tuple[int, str, str]] = []
        bandwidth = 0
        bucket = ""
        for raw in playlist.splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith("#EXT-X-STREAM-INF"):
                m = re.search(r"BANDWIDTH=(\d+)", line)
                bandwidth = int(m.group(1)) if m else 0
                r = re.search(r"RESOLUTION=(\d+)\s*[xX]\s*(\d+)", line)
                bucket = bucket_from_size(int(r.group(1)), int(r.group(2))) if r else ""
                continue
            if line.startswith("#"):
                continue
            out.append((bandwidth, urljoin(base, line), bucket))
            bandwidth = 0
            bucket = ""
        out.sort(key=lambda item: item[0], reverse=True)
        return out

    @staticmethod
    def _segments(playlist: str, base: str) -> list[tuple[str, float]]:
        """解析媒体播放列表：(地址, 时长秒)。#EXT-X-MAP 的初始化段时长为 0。"""
        out: list[tuple[str, float]] = []
        duration = 0.0
        for raw in playlist.splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith("#EXTINF"):
                m = re.search(r"#EXTINF:\s*([\d.]+)", line)
                duration = float(m.group(1)) if m else 0.0
                continue
            if line.startswith("#EXT-X-MAP"):
                m = re.search(r'URI="([^"]+)"', line)
                if m:
                    out.append((urljoin(base, m.group(1)), 0.0))
                continue
            if line.startswith("#"):
                continue
            out.append((urljoin(base, line), duration))
            duration = 0.0
        return out

    def _fetch_text(
        self, url: str, headers: dict, verify: bool, deadline: float, meter: _Meter
    ) -> tuple[str, int]:
        status = 0
        try:
            with self._session().get(
                url,
                headers=headers,
                stream=True,
                verify=verify,
                timeout=(self.s.connect_timeout, self.s.read_timeout),
                allow_redirects=True,
            ) as resp:
                status = resp.status_code
                if status >= 400:
                    return "", status
                pumped = self._pump(
                    resp, deadline, self.s.playlist_max_bytes, keep=self.s.playlist_max_bytes
                )
                meter.feed(pumped)
                return pumped.buf.decode("utf-8", "ignore").lstrip("\ufeff"), status
        except Exception:  # noqa: BLE001 - 单个变体失败不影响整体判定
            return "", status

    def _fetch_to_meter(
        self,
        url: str,
        headers: dict,
        verify: bool,
        deadline: float,
        meter: _Meter,
        limit: int,
    ) -> _Fetched:
        """抓一个分片。Content-Length 会被带回来——算码率时比下完整个分片省时间。"""
        if limit <= 0:
            return _Fetched()
        status = 0
        try:
            with self._session().get(
                url,
                headers=headers,
                stream=True,
                verify=verify,
                timeout=(self.s.connect_timeout, self.s.read_timeout),
                allow_redirects=True,
            ) as resp:
                status = resp.status_code
                if status >= 400:
                    return _Fetched(status=status)
                size = 0
                raw_len = resp.headers.get("Content-Length")
                if raw_len and raw_len.isdigit():
                    size = int(raw_len)
                pumped = self._pump(
                    resp,
                    deadline,
                    limit,
                    keep=256 * 1024,  # 分片一般从 IDR 开始，前 256KB 足够拿到 SPS
                    soft_bytes=self.s.soft_bytes,
                    soft_window=self.s.soft_window,
                )
                meter.feed(pumped)
                return _Fetched(
                    n=pumped.total,
                    status=status,
                    tap=pumped.buf,
                    complete=pumped.complete,
                    size=size,
                )
        except Exception:  # noqa: BLE001 - 单个分片失败按 0 处理
            return _Fetched(status=status)

    # ------------------------------------------------------------------ #
    # 工具
    # ------------------------------------------------------------------ #
    def _pump(
        self,
        resp: requests.Response,
        deadline: float,
        limit: int,
        keep: int = 0,
        soft_bytes: int = 0,
        soft_window: float = 0.0,
    ) -> _Pumped:
        """读数据直到 limit / deadline / 软阈值，并记录采样点。

        complete 只在流自然读完时为 True——被 limit 或软阈值截断都算不完整，
        这样算码率时只用真正下完的分片，避免把半截数据当成整段。
        """
        out = _Pumped()
        if limit <= 0:
            return out
        buf = bytearray()
        total = 0
        t_first = 0.0
        t_last = 0.0
        marks: list[tuple[float, int]] = []
        broken = False
        try:
            for chunk in resp.iter_content(chunk_size=65536):
                if not chunk:
                    continue
                now = time.monotonic()
                if t_first <= 0:
                    t_first = now
                t_last = now
                total += len(chunk)
                marks.append((now, total))
                if keep and len(buf) < keep:
                    buf.extend(chunk[: keep - len(buf)])
                if total >= limit or now >= deadline:
                    broken = True
                    break
                # 快源不必读满上限：攒够 soft_bytes 且窗口够长就收手
                if soft_bytes and total >= soft_bytes and (now - t_first) >= soft_window:
                    broken = True
                    break
        except (requests.exceptions.RequestException, OSError, ValueError):
            broken = True
        out.buf = bytes(buf)
        out.total = total
        out.t_first = t_first
        out.t_last = t_last
        out.complete = not broken
        out.marks = marks
        return out

    @staticmethod
    def _is_error_body(head: bytes) -> bool:
        sample = head.lstrip()[:64]
        if not sample:
            return True
        if sample[:1] in (b"<", b"{"):
            return True
        lowered = sample.lower()
        return (
            lowered.startswith(b"<!doctype")
            or lowered.startswith(b"<html")
            or lowered.startswith(b"http/")
        )

    def _measure(
        self,
        url: str,
        meter: _Meter,
        start: float,
        resolution: str,
        status: int,
        probe: bytes = b"",
        bitrate: float = 0.0,
    ) -> TestResult:
        """只负责给出客观测量值；是否达标交给 _finalize 判定。"""
        elapsed = time.monotonic() - start
        avg = meter.average_kbps(elapsed)
        steady = meter.steady_kbps(elapsed, self.s.warmup)
        total = meter.nbytes
        if total < self.s.min_bytes:
            return TestResult(
                url=url,
                reason="数据量不足",
                elapsed=elapsed,
                total_bytes=total,
                status=status,
            )
        if not resolution and probe:
            # 播放列表没写分辨率时，直接从码流 SPS 里读
            resolution = probe_resolution(probe)
        return TestResult(
            url=url,
            valid=True,
            speed_kbps=steady,
            speed_avg=avg,
            total_bytes=total,
            elapsed=elapsed,
            status=status,
            resolution=resolution,
            bitrate_kbps=bitrate,
        )
