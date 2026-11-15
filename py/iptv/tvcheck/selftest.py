# -*- coding: utf-8 -*-
"""离线自检：不联网，验证解析 / 改名 / 分组 / 阈值 / 输出逻辑。

运行： python py/TV/main.py --self-test
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from .blacklist import Blacklist, is_dead_status
from .models import Candidate
from .names import ChannelDB, clean_name
from .resolution import SPEED_THRESHOLD_KBPS, bucket_from_size, from_text, threshold_for
from .settings import Settings
from .sources import classify_ipver, normalize_url, parse_m3u, parse_txt
from .speedtest import SpeedTester, TestResult, _Meter, _Pumped
from .writer import build_groups, write_m3u, write_txt

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


def _ramp(warm_kbps: float, steady_kbps: float, warm_s: float, steady_s: float) -> _Pumped:
    """造一段下行采样：前 warm_s 秒从 0 线性爬到 warm_kbps（模拟 TCP 慢启动），之后稳定。"""
    t = 1000.0
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

    print("[1/8] demo.txt 别名校正与兜底分组")
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

    print("[2/8] txt 解析")
    entries = parse_txt(TXT)
    _check(len(entries) == 4, f"共解析出 4 条地址（实际 {len(entries)}）")
    _check(entries[0].group == "央视频道", "继承 #genre# 分组")
    _check(entries[1].url == "http://1.1.1.2/live/cctv1.m3u8", "一个频道多地址按 # 拆分")
    steps += 1

    print("[3/8] m3u 解析")
    m3u_entries = parse_m3u(M3U)
    _check(len(m3u_entries) == 2, f"共解析出 2 条（实际 {len(m3u_entries)}）")
    _check(m3u_entries[0].name == "CCTV2", "EXTINF 名称解析正确（忽略属性里的逗号）")
    _check(m3u_entries[0].logo.endswith("cctv2.png"), "tvg-logo 解析正确")
    _check(m3u_entries[1].group == "港台", "group-title 解析正确")
    steps += 1

    print("[4/8] 地址清洗与协议族判定")
    _check(normalize_url("1.2.3.4:8080/a.m3u8") == "http://1.2.3.4:8080/a.m3u8", "缺失协议自动补 http://")
    _check(normalize_url("http://a.com/x.m3u8$User-Agent=1") == "http://a.com/x.m3u8", "去掉 $ 后缀参数")
    _check(normalize_url("token") == "", "碎片文本不会当成地址")
    _check(classify_ipver("http://[2408:8207:1234::1]:8080/live.m3u8") == "ipv6", "IPv6 字面量归入 ipv6")
    _check(classify_ipver("http://1.2.3.4:8080/live.m3u8") == "ipv4", "IPv4 归入 ipv4")
    steps += 1

    print("[5/8] 分辨率档位与阈值")
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

    print("[6/8] 排序与文件输出")
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

    print("[7/8] 测速口径（稳态速度 / 码率基准）")
    # 模拟一条「前 1 秒慢启动爬升到 200KB/s，之后稳定跑 800KB/s」的源
    meter = _Meter()
    meter.feed(_ramp(200, 800, warm_s=1.0, steady_s=3.0))
    avg = meter.average_kbps(4.0)
    steady = meter.steady_kbps(4.0, warmup=1.0)
    _check(steady > avg * 1.2, f"剔掉慢启动后速度明显高于平均（均 {avg:.0f} → 稳 {steady:.0f}）")
    _check(abs(steady - 800) < 60, f"稳态速度回到真实水平附近（{steady:.0f}KB/s）")
    _check(meter.steady_kbps(4.0, warmup=0.0) == avg, "关闭剔除时退回全程平均速度")

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

    print("[8/8] 黑名单计数口径")
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

    print(f"\n自检通过（{steps} 组用例全部正常）。")
    return 0
