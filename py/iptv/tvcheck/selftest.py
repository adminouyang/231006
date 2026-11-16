# -*- coding: utf-8 -*-
"""离线自检：不联网，验证解析 / 改名 / 分组 / 阈值 / 输出逻辑。

运行： python py/TV/main.py --self-test
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from .blacklist import Blacklist, is_dead_status
from .content import (
    drm_label,
    payload_kind,
    playlist_drm,
    short_vod_reason,
    static_reason,
)
from .models import Candidate
from .names import ChannelDB, clean_name
from .resolution import SPEED_THRESHOLD_KBPS, bucket_from_size, from_text, threshold_for
from .settings import Settings
from .sources import classify_ipver, normalize_url, parse_m3u, parse_txt
from .speedtest import SpeedTester, TestResult, _Meter, _Pumped
from .videoprobe import analyze_stream
from .writer import build_groups, truncation_report, write_m3u, write_txt

DEMO = """主频道名|别名1|别名2|
央视频道,#genre#
CCTV1|CCTV-1综合|CCTV1综合|CCTV-1|
CCTV2|CCTV-2财经|CCTV2财经|CCTV-2|
卫视频道,#genre#
湖南卫视|湖南|
其它,#genre#
求索纪录|
"""

TXT = """央视频道,#genre#
CCTV1,http://1.1.1.1:8080/live/cctv1.m3u8#http://1.1.1.2/live/cctv1.m3u8
CCTV-1 综合 高清,http://1.1.1.3/live/cctv1.m3u8
卫视频道,#genre#
湖南卫视高清,http://2.2.2.2/live/hunan.m3u8
"""

M3U = """#EXTM3U x-tvg-url="http://epg.example.com/epg.xml"
#EXTINF:-1 tvg-name="CCTV2" tvg-logo="http://logo/cctv2.png" group-title="央视", CCTV2
http://3.3.3.3/live/cctv2.m3u8
#EXTINF:-1 group-title="港台",翡翠台
http://4.4.4.4/live/jade.m3u8
"""


def _check(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)
    print(f"  [OK] {msg}")


def _ramp(
    warm_kbps: float, steady_kbps: float, warm_s: float, steady_s: float, t0: float = 1000.0
) -> _Pumped:
    """造一段下行采样：前 warm_s 秒从 0 线性爬到 warm_kbps（模拟 TCP 慢启动），之后稳定。"""
    t = t0
    n = 0
    marks: list[tuple[float, int]] = []
    step = 0.1
    count = max(int(round(warm_s / step)), 1)
    for i in range(1, count + 1):
        t += step
        n += int(warm_kbps * i / count * 1024 * step)
        marks.append((t, n))
    for _ in range(max(int(round(steady_s / step)), 1)):
        t += step
        n += int(steady_kbps * 1024 * step)
        marks.append((t, n))
    return _Pumped(buf=b"", total=n, t_first=marks[0][0], t_last=t, marks=marks)


def run_selftest() -> int:
    steps = 0

    print("[1/10] demo.txt 别名校正与兜底分组")
    db = ChannelDB()
    db.feed(DEMO)
    _check(db.match("CCTV-1 综合 高清") is not None, "CCTV-1 综合 高清 命中别名")
    _check(db.match("CCTV-1 综合 高清").name == "CCTV1", "别名统一成主名 CCTV1")
    _check(db.match("cctv1超清").group == "央视频道", "命中后归入模板分组")
    _check(db.match("湖南卫视高清").name == "湖南卫视", "画质后缀被剥离后仍能命中")
    _check(db.match("完全不存在的台") is None, "模板里没有的频道不会被误匹配")
    _check(db.default_group == "其它", "兜底分组沿用模板里的 其它")
    _check(db.group_for("央视") == db.default_group, "源于分组不再参与输出分组")
    _check(clean_name("CCTV1高清") == "CCTV1", "展示名去掉画质后缀")
    steps += 1

    print("[2/10] txt 解析")
    entries = parse_txt(TXT)
    _check(len(entries) == 4, f"共解析出 4 条地址（实际 {len(entries)}）")
    _check(entries[0].group == "央视频道", "继承 #genre# 分组")
    _check(entries[1].url == "http://1.1.1.2/live/cctv1.m3u8", "一个频道多地址按 # 拆分")
    steps += 1

    print("[3/10] m3u 解析")
    m3u_entries = parse_m3u(M3U)
    _check(len(m3u_entries) == 2, f"共解析出 2 条（实际 {len(m3u_entries)}）")
    _check(m3u_entries[0].name == "CCTV2", "EXTINF 名称解析正确（忽略属性里的逗号）")
    _check(m3u_entries[0].logo.endswith("cctv2.png"), "tvg-logo 解析正确")
    _check(m3u_entries[1].group == "港台", "group-title 解析正确")
    steps += 1

    print("[4/10] 地址清洗与协议族判定")
    _check(normalize_url("1.2.3.4:8080/a.m3u8") == "http://1.2.3.4:8080/a.m3u8", "缺失协议自动补 http://")
    _check(normalize_url("http://a.com/x.m3u8$User-Agent=1") == "http://a.com/x.m3u8", "去掉 $ 后缀参数")
    _check(normalize_url("token") == "", "碎片文本不会当成地址")
    _check(classify_ipver("http://[2408:8207:1234::1]:8080/live.m3u8") == "ipv6", "IPv6 字面量归入 ipv6")
    _check(classify_ipver("http://1.2.3.4:8080/live.m3u8") == "ipv4", "IPv4 归入 ipv4")
    steps += 1

    print("[5/10] 分辨率档位与阈值")
    _check(SPEED_THRESHOLD_KBPS["unknown"] == 1024, "unknown 兜底阈值 1024KB/s")
    _check(bucket_from_size(1920, 1080) == "1080p", "1920x1080 -> 1080p")
    _check(bucket_from_size(3840, 2160) == "4K", "3840x2160 -> 4K")
    _check(bucket_from_size(1280, 720) == "720p", "1280x720 -> 720p")
    _check(from_text("CCTV1超清") == "1080p", "名称带“超清”判为 1080p")
    _check(from_text("湖南卫视高清") == "720p", "名称带“高清”判为 720p")
    _check(from_text("北京卫视4K") == "4K", "名称带 4K 判为 4K")
    _check(from_text("CCTV1") == "", "无分辨率线索返回空")
    _check(threshold_for("4K") == 1900, "4K 阈值 1900KB/s")
    _check(threshold_for("720p", 300) == 300, "统一阈值可覆盖档位阈值")
    _check(is_dead_status(404) and is_dead_status(503), "4xx/5xx 视为失效")
    _check(not is_dead_status(429) and not is_dead_status(200), "429 与 200 不拉黑")
    steps += 1

    print("[6/10] 排序与文件输出")
    settings = Settings()
    cands = [
        Candidate(name="CCTV2", name_key="cctv2", group="央视频道", resolution="1080p",
                  threshold=465, url="http://3.3.3.3/cctv2.m3u8", ok=True, speed=800.0, ts="now"),
        Candidate(name="CCTV1", name_key="cctv1", group="央视频道", resolution="1080p",
                  threshold=465, url="http://1.1.1.1/cctv1.m3u8", ok=True, speed=600.0, ts="now"),
        Candidate(name="湖南卫视", name_key="湖南卫视", group="卫视频道", resolution="720p",
                  threshold=282, url="http://2.2.2.2/hunan.m3u8", ok=True, speed=350.0, ts="now"),
        Candidate(name="某未知台", name_key="某未知台", group="其它", resolution="unknown",
                  threshold=1024, url="http://5.5.5.5/xx.m3u8", ok=True, speed=1200.0, ts="now"),
    ]
    groups = build_groups(cands, db, settings)
    names = [ch["name"] for ch in groups["ipv4"][0][1]]
    _check(names == ["CCTV1", "CCTV2"], f"组内按 demo.txt 顺序排序（实际 {names}）")
    _check(groups["ipv4"][-1][0] == "其它", "未命中频道落到模板的兜底分组")

    with tempfile.TemporaryDirectory() as tmp:
        txt_path = Path(tmp) / "tv.txt"
        m3u_path = Path(tmp) / "tv.m3u"
        write_txt(txt_path, groups["ipv4"])
        write_m3u(m3u_path, groups["ipv4"], settings)
        txt = txt_path.read_text(encoding="utf-8")
        m3u = m3u_path.read_text(encoding="utf-8")
        _check(txt.startswith("央视频道,#genre#"), "txt 首行为分组标记")
        _check("某未知台,http://5.5.5.5/xx.m3u8" in txt, "未命中频道被输出到 其它")
        _check(m3u.startswith("#EXTM3U x-tvg-url="), "m3u 头部带 EPG 地址")
        _check(
            'tvg-logo="https://codeberg.org/ou-yang/TV/raw/branch/main/LOGO/CCTV1.png"' in m3u,
            "m3u 自动补台标地址",
        )
        _check('group-title="央视频道",CCTV1' in m3u, "m3u 分组与名称正确")
    steps += 1

    print("[7/10] 测速口径（稳态速度 / 码率基准）")
    # 模拟一条「前 1 秒慢启动爬升到 200KB/s，之后稳定跑 800KB/s」的源
    meter = _Meter()
    meter.feed(_ramp(200, 800, warm_s=1.0, steady_s=3.0))
    avg = meter.average_kbps(4.0)
    steady = meter.steady_kbps(4.0, warmup=1.0)
    _check(steady > avg * 1.2, f"剔掉慢启动后速度明显高于平均（均 {avg:.0f} → 稳 {steady:.0f}）")
    _check(abs(steady - 800) < 60, f"稳态速度回到真实水平附近（{steady:.0f}KB/s）")
    _check(meter.steady_kbps(4.0, warmup=0.0) == avg, "关闭剔除时退回全程平均速度")

    # 两个请求之间有 5 秒空档，末段突发不能被当成稳态（曾出现 稳态 2761 / 均速 314 的鬼数据）
    gap_meter = _Meter()
    gap_meter.feed(_ramp(200, 200, warm_s=0.1, steady_s=1.0))
    gap_meter.feed(_ramp(2000, 2000, warm_s=0.1, steady_s=0.5, t0=1006.0))
    gap_steady = gap_meter.steady_kbps(8.0, warmup=1.0)
    _check(
        gap_steady < 600,
        f"请求间空档计入时间，末段突发不会虚报稳态（{gap_steady:.0f}KB/s）",
    )

    tester = SpeedTester(Settings())
    r = TestResult(url="x", valid=True, speed_kbps=420, bitrate_kbps=300, resolution="unknown")
    tester._finalize(r, "unknown")
    _check(r.ok and r.threshold < 1024, "无分辨率元数据的源按码率基准放宽后可通过")
    _check(r.basis.startswith("码率基准"), f"日志能看出用的是码率基准（{r.basis}）")

    r2 = TestResult(url="x", valid=True, speed_kbps=500, bitrate_kbps=400, resolution="1080p")
    tester._finalize(r2, "1080p")
    _check(r2.threshold == 465 and r2.ok, "高码率 1080p 仍按分辨率阈值 465 判定")

    r3 = TestResult(url="x", valid=True, speed_kbps=60, bitrate_kbps=30, resolution="unknown")
    tester._finalize(r3, "unknown")
    _check(
        not r3.ok and abs(r3.threshold - 1024 * 0.2) < 1,
        f"极低码率劣质源被「档位阈值×0.2」下限挡住（目标 {r3.threshold:.0f}）",
    )

    segs = SpeedTester._segments("#EXTM3U\n#EXTINF:9.0,\na.ts\n#EXTINF:6.5,\nb.ts\n",
                                 "http://h/x.m3u8")
    _check(len(segs) == 2 and segs[0][1] == 9.0, "EXTINF 时长被解析出来（用于算码率）")
    _check(segs[1][0] == "http://h/b.ts", "分片地址相对路径解析正确")
    steps += 1

    print("[8/10] 黑名单计数口径")
    with tempfile.TemporaryDirectory() as tmp:
        bl = Blacklist(Path(tmp) / "bl.txt", ttl_days=7, threshold=3)
        # 同一台主机下 5 个频道同轮全挂，只能算 1 次失败
        for i in range(5):
            bl.record_fail(f"http://1.2.3.4:8080/live/ch{i}.m3u8", "HTTP 404")
        _check(bl.entries["1.2.3.4:8080"].count == 1, "同一轮同一主机只计一次失败")
        _check(not bl.is_bad("http://1.2.3.4:8080/live/x.m3u8"), "一轮失败不足以拉黑")
        for _ in range(2):
            bl._struck.clear()
            bl.record_fail("http://1.2.3.4:8080/live/x.m3u8", "HTTP 404")
        _check(bl.entries["1.2.3.4:8080"].count == 3, "跨轮继续失败才累加")
        _check(bl.is_bad("http://1.2.3.4:8080/live/x.m3u8"), "连续 3 轮失败才跳过")
        bl.record_ok("http://1.2.3.4:8080/live/x.m3u8")
        _check(not bl.is_bad("http://1.2.3.4:8080/live/x.m3u8"), "一次成功即解除")
    steps += 1

    print("[9/10] 临界分级与每频道截断")
    # 用户反馈的真实场景：unknown 档目标 1024，实测 672KB/s / 峰值 760，实际能流畅播放
    tester_w = SpeedTester(Settings())
    rw = TestResult(
        url="x", valid=True, speed_kbps=672, speed_peak=760,
        bitrate_kbps=1098, resolution="unknown",
    )
    tester_w._finalize(rw, "unknown")
    _check(rw.threshold == 1024, f"该源仍按 unknown 阈值 1024 判定（{rw.threshold:g}）")
    _check(not rw.ok and rw.weak_ok, "达不到硬阈值的可用源被判为临界，不再直接丢弃")

    rw2 = TestResult(url="x", valid=True, speed_kbps=280, speed_peak=300, resolution="unknown")
    tester_w._finalize(rw2, "unknown")
    _check(not rw2.weak_ok, "连临界线都不到的源仍然淘汰")

    s_off = Settings()
    s_off.weak_enabled = False
    rw3 = TestResult(url="x", valid=True, speed_kbps=672, speed_peak=760, resolution="unknown")
    SpeedTester(s_off)._finalize(rw3, "unknown")
    _check(not rw3.weak_ok, "--no-weak 时退回单一的硬阈值判定")

    # 峰值窗口：整段匀速 600KB/s 时，峰值不应明显偏离稳态
    meter_p = _Meter()
    meter_p.feed(_ramp(600, 600, warm_s=0.2, steady_s=4.0))
    peak = meter_p.peak_kbps(2.0)
    _check(abs(peak - 600) < 120, f"匀速源的峰值速度与稳态一致（{peak:.0f}KB/s）")

    # 排序与截断：达标源按速度降序占满 6 个名额，临界源/本地源不得挤占
    cap = Settings()
    batch: list[Candidate] = []
    for sp in (100.0, 250.0, 400.0, 550.0, 700.0, 850.0, 950.0, 1100.0):
        batch.append(
            Candidate(name="CCTV1", name_key="cctv1", group="央视频道", ok=True,
                      speed=sp, url=f"http://1.1.1.1/{int(sp)}.m3u8", ts="now")
        )
    batch.append(
        Candidate(name="CCTV1", name_key="cctv1", group="央视频道", weak=True,
                  speed=5000.0, url="http://9.9.9.9/weak.m3u8", ts="now")
    )
    batch.append(
        Candidate(name="CCTV1", name_key="cctv1", group="央视频道", local=True,
                  testable=False, url="http://8.8.8.8/local.m3u8")
    )
    g = build_groups(batch, db, cap)
    chan = next(ch for ch in g["ipv4"][0][1] if ch["key"] == "cctv1")
    speeds = [c.speed for c in chan["items"]]
    _check(len(chan["items"]) == cap.max_urls_per_channel, "每频道最多保留 6 个地址")
    _check(speeds == sorted(speeds, reverse=True), f"频道内按速度降序输出（{[int(s) for s in speeds]}）")
    _check(
        all(c.ok and not c.weak and not c.local for c in chan["items"]),
        "未测速的本地源与临界源都不挤占达标源的名额",
    )
    _check(speeds[0] == 1100.0, "最快的地址一定排在第一位")
    rep = truncation_report(batch, cap)
    _check(bool(rep) and "CCTV1" in rep[1], "日志会说明某频道被上限截掉了多少地址")
    steps += 1

    print("[10/10] 内容校验（DRM / 静止画面 / 点播短片）")
    _check(payload_kind(b"\x47\x40\x00\x10" + b"\x00" * 400) == "ts", "TS 载荷识别正确")
    arc = b"ARCVIDEO-PROTECTED" + bytes(range(256)) * 40
    _check(payload_kind(arc) == "encrypted", "私有加密头被判为加密载荷")
    _check("ARCVIDEO" in drm_label(arc), f"能说出是哪家的 DRM（{drm_label(arc)}）")
    _check(drm_label(b"\x47\x00\x00\x10" + b"\x00" * 400) == "", "正常 TS 不会被误判成 DRM")

    lock = '#EXTM3U\n#EXT-X-KEY:METHOD=SAMPLE-AES,URI="skd://x"\n#EXTINF:6,\na.ts\n'
    _check("SAMPLE-AES" in playlist_drm(lock), "SAMPLE-AES 加密列表被拦下")
    _check(playlist_drm("#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI=\"k\"\n") == "",
           "AES-128 是标准可播加密，不拦")

    vod = "#EXTM3U\n" + "#EXTINF:16.666667,\na.ts\n" * 8 + "#EXT-X-ENDLIST\n"
    _check(bool(short_vod_reason(vod, 600)), "带 ENDLIST 的短列表被识别为点播短片")
    _check(short_vod_reason("#EXTM3U\n#EXTINF:3,\na.ts\n" * 20, 600) == "",
           "没有 ENDLIST 的直播列表不会误判")
    rolled = "#EXTM3U\n#EXT-X-MEDIA-SEQUENCE:1794709948\n" + "#EXTINF:3,\na.ts\n" * 10 + "#EXT-X-ENDLIST\n"
    _check(short_vod_reason(rolled, 600) == "",
           "直播列表误带 ENDLIST（序列号已滚动）不被误判为短片")
    _check(short_vod_reason(vod, 0) == "", "--min-live 0 关闭时长限制")

    # 造一段 TS：静止画面每帧只有一百多字节，正常视频每帧几 KB（长帧要跨多个 TS 包）
    def _ts(frames: list[int]) -> bytes:
        out = bytearray()
        for i, size in enumerate(frames):
            pts = 90000 + i * 3000
            p = bytes([
                0x21 | ((pts >> 29) & 0x0E),
                (pts >> 22) & 0xFF,
                0x01 | ((pts >> 14) & 0xFE),
                (pts >> 7) & 0xFF,
                0x01 | ((pts << 1) & 0xFE),
            ])
            body = bytes([size & 0xFF]) * size
            pes = b"\x00\x00\x01\xe0" + len(body).to_bytes(2, "big") + b"\x80\x80\x05" + p + body
            for k in range(0, len(pes), 184):
                chunk = pes[k: k + 184].ljust(184, b"\xff")
                pusi = 0x40 if k == 0 else 0x00
                out += bytes([0x47, pusi | 0x01, 0x00, 0x10]) + chunk
        return bytes(out)

    still = analyze_stream(_ts([140] * 60))
    _check(still.static, f"全为小帧的码流判为静止画面（中位 {still.median_frame}B）")
    _check("静止画面" in static_reason(still), "拒绝原因里写明静止画面")

    live = analyze_stream(_ts([9000] * 60))
    _check(not live.static, f"正常帧大小的码流不会被误判（中位 {live.median_frame}B）")
    _check(static_reason(live) == "", "正常码流不产生拒绝原因")
    steps += 1

    print(f"\n自检通过（{steps} 组用例全部正常）。")
    return 0