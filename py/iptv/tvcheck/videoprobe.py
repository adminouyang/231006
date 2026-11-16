# -*- coding: utf-8 -*-
"""从码流本身探测分辨率。

思路：
    1. TS（0x47 同步，188 字节包）：PAT -> PMT -> 视频 PID -> PES 载荷
    2. 在 PES 里找 H.264 SPS(NAL 7) 或 HEVC SPS(NAL 33)
    3. 解指数哥伦布，算出宽高（含 frame_cropping）

拿不到就返回空串，由调用方回退到“频道名”或 unknown。
"""

from __future__ import annotations

from dataclasses import dataclass

from .resolution import bucket_from_size

_TS_PACKET = 188
_STREAM_TYPES = (0x01, 0x02, 0x10, 0x1B, 0x24, 0x42, 0xD1, 0xEA)
_MAX_SCAN = 700 * 1024


class _Bits:
    """极简位读取器（指数哥伦布）。"""

    __slots__ = ("data", "pos", "nbits")

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0
        self.nbits = len(data) * 8

    def bit(self) -> int:
        if self.pos >= self.nbits:
            raise ValueError("eof")
        byte = self.data[self.pos >> 3]
        val = (byte >> (7 - (self.pos & 7))) & 1
        self.pos += 1
        return val

    def bits(self, n: int) -> int:
        val = 0
        for _ in range(n):
            val = (val << 1) | self.bit()
        return val

    def skip(self, n: int) -> None:
        if self.pos + n > self.nbits:
            raise ValueError("eof")
        self.pos += n

    def ue(self) -> int:
        zeros = 0
        while self.bit() == 0:
            zeros += 1
            if zeros > 31:
                raise ValueError("ue overflow")
        val = 1
        for _ in range(zeros):
            val = (val << 1) | self.bit()
        return val - 1

    def se(self) -> int:
        code = self.ue()
        return (code + 1) // 2 if code & 1 else -(code // 2)


# --------------------------------------------------------------------------- #
# TS 拆包
# --------------------------------------------------------------------------- #
def _iter_packets(data: bytes):
    for offset in range(0, len(data) - (_TS_PACKET - 1), _TS_PACKET):
        if data[offset] != 0x47:
            continue
        yield offset


def _payload(data: bytes, offset: int) -> tuple[int, bool, bytes]:
    b1 = data[offset + 1]
    pusi = bool(b1 & 0x40)
    pid = ((b1 & 0x1F) << 8) | data[offset + 2]
    afc = (data[offset + 3] >> 4) & 0x03
    end = offset + _TS_PACKET
    pos = offset + 4
    if afc & 0x02:
        if pos >= end:
            return pid, pusi, b""
        pos += 1 + data[pos]
    if not afc & 0x01 or pos >= end:
        return pid, pusi, b""
    # 注意：pointer_field 只存在于 PSI（PAT/PMT）的包首，PES 包首是 start code，
    # 所以这里原样返回，由各自的解析逻辑处理。
    return pid, pusi, data[pos:end]


def _section(data: bytes, pid: int, max_len: int = 1024) -> bytes:
    """把某个 PID 上的 PSI 段拼起来（一个段可能跨多个 TS 包）。"""
    parts: list[bytes] = []
    started = False
    total = 0
    for offset in _iter_packets(data):
        p, pusi, body = _payload(data, offset)
        if p != pid or not body:
            continue
        if pusi:
            body = body[1 + body[0]:]  # pointer_field
            parts = [body]
            started = True
            total = len(body)
        elif started:
            parts.append(body)
            total += len(body)
        else:
            continue
        if total >= max_len:
            break
    return b"".join(parts)


def _pmt_pid(data: bytes) -> int | None:
    pat = _section(data, 0)
    if len(pat) < 12 or pat[0] != 0x00:
        return None
    section_length = ((pat[1] & 0x0F) << 8) | pat[2]
    end = min(3 + section_length - 4, len(pat))
    pos = 8
    while pos + 4 <= end:
        program = (pat[pos] << 8) | pat[pos + 1]
        ppid = ((pat[pos + 2] & 0x1F) << 8) | pat[pos + 3]
        if program:
            return ppid
        pos += 4
    return None


def _video_pids(data: bytes, pmt_pid: int) -> list[int]:
    pmt = _section(data, pmt_pid)
    if len(pmt) < 12 or pmt[0] != 0x02:
        return []
    pids: list[int] = []
    section_length = ((pmt[1] & 0x0F) << 8) | pmt[2]
    end = min(3 + section_length - 4, len(pmt))
    program_info_length = ((pmt[10] & 0x0F) << 8) | pmt[11]
    pos = 12 + program_info_length
    while pos + 5 <= end:
        stream_type = pmt[pos]
        epid = ((pmt[pos + 1] & 0x1F) << 8) | pmt[pos + 2]
        es_info_length = ((pmt[pos + 3] & 0x0F) << 8) | pmt[pos + 4]
        if stream_type in _STREAM_TYPES and epid not in pids:
            pids.append(epid)
        pos += 5 + es_info_length
    return pids


def _es_bytes(data: bytes, pid: int) -> bytes:
    out = bytearray()
    for offset in _iter_packets(data):
        p, pusi, body = _payload(data, offset)
        if p != pid or not body:
            continue
        if pusi:
            # PES 起始码可能是 3 字节（00 00 01）或 4 字节（00 00 00 01）
            sp = body.find(b"\x00\x00\x01", 0, 8)
            if sp < 0 or len(body) < sp + 9:
                continue
            body = body[sp + 9 + body[sp + 8]:]
        out += body
        if len(out) >= _MAX_SCAN:
            break
    return bytes(out)


# --------------------------------------------------------------------------- #
# NAL / SPS
# --------------------------------------------------------------------------- #
def _unescape(data: bytes) -> bytes:
    out = bytearray()
    i, n = 0, len(data)
    while i < n:
        if i + 2 < n and data[i] == 0 and data[i + 1] == 0 and data[i + 2] == 3:
            out += data[i:i + 2]
            i += 3
        else:
            out.append(data[i])
            i += 1
    return bytes(out)


def _find_nal(es: bytes, nal_type: int, hevc: bool = False) -> bytes | None:
    idx = 0
    step = 3
    while True:
        idx = es.find(b"\x00\x00\x01", idx)
        if idx < 0:
            return None
        hdr_pos = idx + 3
        if hdr_pos + (2 if hevc else 1) > len(es):
            return None
        if hevc:
            got = (es[hdr_pos] >> 1) & 0x3F
            body_start = hdr_pos + 2
        else:
            got = es[hdr_pos] & 0x1F
            body_start = hdr_pos + 1
        if got == nal_type:
            nxt = es.find(b"\x00\x00\x01", body_start)
            return es[body_start: nxt if nxt > 0 else len(es)]
        idx += step


def _skip_scaling_list(bits: _Bits, size: int) -> None:
    last = 8
    nxt = 8
    for _ in range(size):
        if nxt != 0:
            nxt = (last + bits.se() + 256) % 256
        if nxt != 0:
            last = nxt


def _h264_size(rbsp: bytes) -> tuple[int, int] | None:
    bits = _Bits(rbsp)
    profile_idc = bits.bits(8)
    bits.bits(8)          # constraint flags
    bits.bits(8)          # level_idc
    bits.ue()             # sps_id
    chroma_format_idc = 1
    if profile_idc in (100, 110, 122, 244, 44, 83, 86, 118, 128, 138, 139, 134, 135):
        chroma_format_idc = bits.ue()
        if chroma_format_idc == 3:
            bits.skip(1)  # separate_colour_plane_flag
        bits.ue()         # bit_depth_luma_minus8
        bits.ue()         # bit_depth_chroma_minus8
        bits.skip(1)      # qpprime_y_zero_transform_bypass_flag
        if bits.bit():    # seq_scaling_matrix_present_flag
            count = 8 if chroma_format_idc != 3 else 12
            for i in range(count):
                if bits.bit():
                    _skip_scaling_list(bits, 16 if i < 6 else 64)

    bits.ue()             # log2_max_frame_num_minus4
    pic_order_cnt_type = bits.ue()
    if pic_order_cnt_type == 0:
        bits.ue()
    elif pic_order_cnt_type == 1:
        bits.skip(1)
        bits.se()
        bits.se()
        for _ in range(bits.ue()):
            bits.se()
    bits.ue()             # max_num_ref_frames
    bits.skip(1)          # gaps_in_frame_num_value_allowed_flag
    width_mbs = bits.ue() + 1
    height_units = bits.ue() + 1
    frame_mbs_only = bits.bit()
    if not frame_mbs_only:
        bits.skip(1)
    bits.skip(1)          # direct_8x8_inference_flag
    width = width_mbs * 16
    height = (2 - frame_mbs_only) * height_units * 16

    if bits.bit():        # frame_cropping_flag
        left, right, top, bottom = bits.ue(), bits.ue(), bits.ue(), bits.ue()
        sub_w = 2 if chroma_format_idc in (1, 2) else 1
        sub_h = 2 if chroma_format_idc == 1 else 1
        width -= (left + right) * sub_w
        height -= (top + bottom) * sub_h * (2 - frame_mbs_only)
    return width, height


def _hevc_size(rbsp: bytes) -> tuple[int, int] | None:
    bits = _Bits(rbsp)
    bits.skip(4)                       # sps_video_parameter_set_id
    max_sub_layers = bits.bits(3)
    bits.skip(1)                       # sps_temporal_id_nesting_flag
    # profile_tier_level
    bits.skip(2 + 1 + 5)               # profile_space / tier / profile_idc
    bits.skip(32)                      # compatibility flags
    bits.skip(4)                       # progressive/interlaced/non_packed/frame_only
    bits.skip(44)                      # reserved
    bits.skip(8)                       # general_level_idc
    if max_sub_layers > 0:
        profile_present = [bits.bit() for _ in range(max_sub_layers)]
        level_present = [bits.bit() for _ in range(max_sub_layers)]
        if max_sub_layers < 8:
            bits.skip(2 * (8 - max_sub_layers))
        for i in range(max_sub_layers):
            if profile_present[i]:
                bits.skip(88)
            if level_present[i]:
                bits.skip(8)

    bits.ue()                          # sps_seq_parameter_set_id
    chroma_format_idc = bits.ue()
    if chroma_format_idc == 3:
        bits.skip(1)
    width = bits.ue()
    height = bits.ue()
    if bits.bit():                     # conformance_window_flag
        left, right, top, bottom = bits.ue(), bits.ue(), bits.ue(), bits.ue()
        sub_w = 2 if chroma_format_idc in (1, 2) else 1
        sub_h = 2 if chroma_format_idc == 1 else 1
        width -= (left + right) * sub_w
        height -= (top + bottom) * sub_h
    return width, height


def _sane(width: int, height: int) -> bool:
    return 160 <= width <= 8192 and 120 <= height <= 4320


def size_from_es(es: bytes) -> tuple[int, int] | None:
    """从裸流里找 SPS 并解出宽高。"""
    for nal_type, parser, hevc in ((7, _h264_size, False), (33, _hevc_size, True)):
        raw = _find_nal(es, nal_type, hevc=hevc)
        if not raw:
            continue
        try:
            size = parser(_unescape(raw))
        except (ValueError, IndexError):
            continue
        if size and _sane(*size):
            return size
    return None


def probe_resolution(data: bytes) -> str:
    """输入一段裸码流（TS / 裸 ES），返回分辨率档位；判定不出来返回空串。"""
    if not data or len(data) < 400:
        return ""

    candidates: list[bytes] = []
    if len(data) > _TS_PACKET and data[0] == 0x47:
        pmt_pid = _pmt_pid(data)
        if pmt_pid is not None:
            for pid in _video_pids(data, pmt_pid)[:3]:
                candidates.append(_es_bytes(data, pid))
    candidates.append(data)  # 兜底：直接在原始数据里找 SPS

    for es in candidates:
        size = size_from_es(es)
        if size:
            return bucket_from_size(size[0], size[1])
    return ""


# --------------------------------------------------------------------------- #
# 画面活跃度
# --------------------------------------------------------------------------- #
@dataclass
class VideoStats:
    """一段码流里的视频帧统计，用于识别「静止画面」。"""

    width: int = 0
    height: int = 0
    frames: int = 0            # 带 PTS 的视频 PES 数（TS 里通常 1 PES = 1 帧）
    video_bytes: int = 0       # 该帧序列的 ES 总字节
    median_frame: int = 0      # 帧大小中位数（字节）
    max_frame: int = 0
    span: float = 0.0          # 首末 PTS 跨度（秒）

    @property
    def fps(self) -> float:
        if self.span <= 0 or self.frames < 2:
            return 0.0
        return (self.frames - 1) / self.span

    @property
    def bpp(self) -> float:
        """每像素每帧的比特数。静止画面会低到 0.001 量级（正常 1080p 约 0.05~0.1）。"""
        if not (self.width and self.height and self.frames):
            return 0.0
        return self.median_frame * 8.0 / (self.width * self.height)

    @property
    def static(self) -> bool:
        """是否静止画面。

        判据是「帧大小中位数极低」而不是总码率：静止画面里每一帧都是跳过的 P 帧，
        普遍只有一两百字节（实测 500 帧全部 148~176 字节）；哪怕偶尔夹一个 IDR 也不影响中位数。
        正常视频单帧通常在几 KB 到几十 KB，最低码率的直播也不会中位到 500 字节。
        """
        return self.frames >= 30 and 0 < self.median_frame < 500


def _pts_of(pes: bytes) -> int | None:
    """pes 从 stream_id 开始。返回 PTS（90kHz），没有则 None。"""
    if len(pes) < 11:
        return None
    if (pes[3] >> 6) & 0x03 == 0:  # PTS_DTS_flags
        return None
    p = pes[6:11]
    return (
        (((p[0] >> 1) & 0x07) << 30)
        | (p[1] << 22)
        | (((p[2] >> 1) & 0x7F) << 15)
        | (p[3] << 7)
        | (p[4] >> 1)
    )


def _video_pid_by_pes(data: bytes) -> int | None:
    """PMT 缺失时，按「视频 PES 起始最多」猜一个视频 PID。"""
    counter: dict[int, int] = {}
    for offset in _iter_packets(data):
        pid, pusi, body = _payload(data, offset)
        if not pusi or len(body) < 4:
            continue
        sp = body.find(b"\x00\x00\x01", 0, 8)
        if sp >= 0 and 0xE0 <= body[sp + 3] <= 0xEF:
            counter[pid] = counter.get(pid, 0) + 1
    if not counter:
        return None
    return max(counter.items(), key=lambda kv: kv[1])[0]


def _pid_frames(data: bytes, pid: int) -> tuple[list[int], float]:
    """返回 (每个 PES 的 ES 字节列表, 首末 PTS 跨度秒)。"""
    sizes: list[int] = []
    pending = 0
    pts_lo = -1
    pts_hi = -1
    for offset in _iter_packets(data):
        p, pusi, body = _payload(data, offset)
        if p != pid or not body:
            continue
        if not pusi:
            if pending:
                pending += len(body)
            continue
        if pending:
            sizes.append(pending)
            pending = 0
        sp = body.find(b"\x00\x00\x01", 0, 8)
        if sp < 0 or len(body) < sp + 9:
            continue
        sid = body[sp + 3]
        if not 0xE0 <= sid <= 0xEF:  # 0xBE 填充、音频等都跳过
            continue
        pes = body[sp + 3:]
        es_start = sp + 9 + body[sp + 8]
        if es_start > len(body):
            continue
        pending = len(body) - es_start
        t = _pts_of(pes)
        if t is not None:
            if pts_lo < 0 or t < pts_lo:
                pts_lo = t
            if t > pts_hi:
                pts_hi = t
    if pending:
        sizes.append(pending)
    span = (pts_hi - pts_lo) / 90000.0 if pts_lo >= 0 and pts_hi > pts_lo else 0.0
    return sizes, span


def analyze_stream(data: bytes) -> VideoStats:
    """分析一段 TS 的视频帧大小分布，用于判断静止画面 / 低活跃度。"""
    stats = VideoStats()
    if not data or len(data) < _TS_PACKET * 8 or data[0] != 0x47:
        return stats

    pids: list[int] = []
    pmt_pid = _pmt_pid(data)
    if pmt_pid is not None:
        pids = _video_pids(data, pmt_pid)
    if not pids:
        guess = _video_pid_by_pes(data)
        if guess is not None:
            pids = [guess]
    if not pids:
        return stats

    pid = pids[0]
    sizes, span = _pid_frames(data, pid)
    if not sizes:
        return stats

    ordered = sorted(sizes)
    mid = len(ordered) // 2
    stats.frames = len(ordered)
    stats.video_bytes = sum(ordered)
    stats.median_frame = ordered[mid]
    stats.max_frame = ordered[-1]
    stats.span = span

    size = size_from_es(_es_bytes(data, pid))
    if size:
        stats.width, stats.height = size
    return stats
