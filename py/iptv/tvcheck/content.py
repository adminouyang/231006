# -*- coding: utf-8 -*-
"""内容合规判断：这条地址「拿到数据」不等于「能播出画面」。

测速只看吞吐，会被三类源骗过去：

    1. DRM 加密流
       分片是合法的 HTTP 200、字节数也够，但载荷是私有加密容器。
       实测某电视台的 /drm/ 源，分片开头是 ASCII 头 "ARCVIDEO-PROTECTED"，
       整段熵 8.00 bit/byte（纯随机），TS 同步字节完全对不上——播放器解不出任何画面。

    2. 点播短片
       播放列表带 #EXT-X-ENDLIST 且总时长只有两分钟，本质是个视频文件，
       轮播几次就断了，不能当直播源。

    3. 静止画面
       1080p 分辨率、码率几十 KB/s，帧率正常但每一帧都是跳过帧，
       播放器显示一张不动的图。具体判定在 videoprobe.analyze_stream。
"""

from __future__ import annotations

import math
import re

from .resolution import UNKNOWN

# 已知的私有/商用 DRM 载荷头。命中即视为加密，播放器没有对应 SDK 就放不出画面。
DRM_MAGIC: tuple[tuple[bytes, str], ...] = (
    (b"ARCVIDEO-PROTECTED", "ARCVIDEO 私有加密"),
    (b"WMDRM", "Windows Media DRM"),
    (b"PIFF", "PIFF 加密（PlayReady）"),
    (b"mrci", "Marlin IPMP"),
    (b"#EXT-X-FAXS-CM", "FairPlay 流密钥"),
)

# 这些箱类型说明是标准可播放容器（fMP4 / MP4）
_MP4_BOXES = (b"ftyp", b"styp", b"moof", b"moov", b"mdat", b"sidx", b"free", b"skip")


def _entropy(data: bytes) -> float:
    """一阶信息熵（bit/byte）。加密数据接近 8，正常 TS 一般 7.2 以下。"""
    if not data:
        return 0.0
    counts = [0] * 256
    for byte in data:
        counts[byte] += 1
    total = len(data)
    value = 0.0
    for count in counts:
        if count:
            p = count / total
            value -= p * math.log2(p)
    return value


def payload_kind(data: bytes) -> str:
    """识别载荷类型：ts / ps / flv / mp4 / adts / mpeg-audio / encrypted / unknown。"""
    if not data or len(data) < 32:
        return "empty"

    for magic, _label in DRM_MAGIC:
        if data.startswith(magic):
            return "encrypted"

    head = data[:16]
    if head[0] == 0x47:
        return "ts"
    if head[:4] == b"\x00\x00\x01\xba":
        return "ps"
    if head[:3] == b"FLV":
        return "flv"
    if head[4:8] in _MP4_BOXES:
        return "mp4"
    if head[0] == 0xFF and (head[1] & 0xF6) == 0xF0:
        return "adts"
    if head[:3] == b"ID3" or (head[0] == 0xFF and (head[1] & 0xE0) == 0xE0):
        return "mpeg-audio"

    # 认不出容器：再看是不是纯随机数据（加密/混淆），
    # 正常码流即使容器奇特也会有明显结构，熵不会顶到 8。
    sample = data[:64 * 1024]
    if len(sample) >= 4096 and _entropy(sample) >= 7.95:
        return "encrypted"
    return "unknown"


def drm_label(data: bytes) -> str:
    """命中已知 DRM 头时返回可读名称，否则空串。"""
    for magic, label in DRM_MAGIC:
        if data.startswith(magic):
            return label
    if payload_kind(data) == "encrypted":
        return "加密载荷（无法解码）"
    return ""


# --------------------------------------------------------------------------- #
# 播放列表级校验
# --------------------------------------------------------------------------- #
# 这些 HLS 加密方式需要专用密钥服务器，普通播放器/检测脚本都解不开
_UNPLAYABLE_KEY = ("SAMPLE-AES", "SAMPLE-AES-CTR", "SAMPLE-AES-CENC")


def playlist_drm(text: str) -> str:
    """播放列表里声明了不可解的加密方式时返回说明。"""
    for line in text.splitlines():
        if "#EXT-X-KEY" not in line and "#EXT-X-SESSION-KEY" not in line:
            continue
        upper = line.upper()
        for method in _UNPLAYABLE_KEY:
            if method in upper:
                return f"HLS 加密（{method}）"
        if "FAXS" in upper or "WIDEVINE" in upper or "PLAYREADY" in upper:
            return "HLS DRM 密钥（FairPlay/Widevine）"
    return ""


def playlist_duration(text: str) -> tuple[float, bool]:
    """返回 (总时长秒, 是否点播)。

    #EXT-X-ENDLIST 表示播放列表已经完结、不会再有新分片——直播流不会这样，
    除了「伪直播」把一段视频循环切出来。
    """
    total = 0.0
    for m in re.finditer(r"#EXTINF:\s*([\d.]+)", text):
        try:
            total += float(m.group(1))
        except ValueError:
            continue
    vod = "#EXT-X-ENDLIST" in text or "#EXT-X-PLAYLIST-TYPE:VOD" in text
    return total, vod


def _media_sequence(text: str) -> int:
    m = re.search(r"#EXT-X-MEDIA-SEQUENCE:\s*(\d+)", text)
    return int(m.group(1)) if m else 0


def short_vod_reason(text: str, min_seconds: float) -> str:
    """点播且总时长不足时给出拒绝原因。

    只认「ENDLIST + 短时长」会误杀一类源：少数直播编码器会给滑动窗口列表也加上
    ENDLIST。这类列表的 MEDIA-SEQUENCE 通常已经涨到很大（节目播了很久），
    而真正的点播文件从 0 开始，所以拿它做二次确认。
    """
    total, vod = playlist_duration(text)
    if not vod or min_seconds <= 0:
        return ""
    explicit = "#EXT-X-PLAYLIST-TYPE:VOD" in text
    if not explicit and _media_sequence(text) > 0:
        return ""  # 列表已滚动很久，判定为直播列表误带 ENDLIST，放行
    if total <= 0:
        return "点播列表（无直播分片）"
    if total < min_seconds:
        return f"点播短片（总时长 {total:.0f}s，非直播）"
    return ""


def static_reason(stats, bucket: str = UNKNOWN) -> str:
    """静止画面判定。stats 是 videoprobe.VideoStats。"""
    if stats is None or not stats.static:
        return ""
    size = f"{stats.width}x{stats.height}" if stats.width else bucket
    return (
        f"静止画面（{size}，{stats.frames} 帧中位 {stats.median_frame}B、"
        f"最大 {stats.max_frame}B，帧率 {stats.fps:.0f}fps）"
    )
