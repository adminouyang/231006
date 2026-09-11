#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP 扫描检测脚本（完善版 · 按省份分流 + 测速 + 生成频道链接 + 合并）

输入：py/udpxy/test_ip.txt
    格式：ip:port$省份    例：58.37.152.210:4022$上海电信

流程：
  1) 扫描检测有效 IP（/status -> /stat）
  2) 对有效 IP 用 CITY_STREAMS 测速，> SPEED_THRESHOLD_KB 才保留
  3) 用省份模板生成 <省份>.txt / <省份>.m3u（替换 ipipip）
  4) 按 demo.txt 主频道名+别名匹配，合并输出 all.txt / all.m3u（带台标/EPG）

test_ip.txt 维护规则：
  场景                          test_ip.txt 处理
  完全无有效IP(扫描完没找到)     删除（记录到 Invalid_ip_file/）
  有区间 + 无效                  保留（记录到 Invalid_ip_file/，下次继续扫描）
  测速未通过                     保留（留到以后设置区间）
  即：仅「无区间 + 扫描完全无有效IP」才从 test_ip.txt 删除。
  注：C+D段扫描因提前停止(凑满即停)导致测速未通过的情况，不删除原文件。
"""

import asyncio
import os
import re
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

import aiohttp
from aiohttp import ClientTimeout, TCPConnector

# ==================== 可调参数 ====================
BASE_DIR = "py/udpxy"
INPUT_FILE = os.path.join(BASE_DIR, "test_ip.txt")
INVALID_DIR = os.path.join(BASE_DIR, "Invalid_ip_file")
TEMPLATE_DIR = os.path.join(BASE_DIR, "template")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

LOGO_FILE = os.path.join(TEMPLATE_DIR, "logo.txt")
DEMO_FILE = os.path.join(TEMPLATE_DIR, "demo.txt")

HTTP_CONCURRENCY = 300        # 并发数
HTTP_TIMEOUT = 4.0            # 总超时(秒)
HTTP_CONNECT_TIMEOUT = 1.0    # 连接超时(秒)
D_STOP_COUNT = 2              # D 段扫描停止阈值
CD_STOP_COUNT = 1             # C+D / C区间 扫描停止阈值

SPEED_TEST_DURATION = 3.0     # 测速采样时长(秒)
SPEED_THRESHOLD_KB = 300.0    # 最低速率阈值(KB/s)，低于此值丢弃
MAX_LINKS_PER_CHANNEL = 5     # 同一频道最多保留的链接数（按速度降序取前 N）
GROUP_FIRST_USE_UPDATE_TIME = True  # 每个分组第一个频道 group-title 用"更新时间"

# EPG 地址（用于 m3u 文件头部 x-tvg-url）
EPG_URL = "https://gh-proxy.com/https://raw.githubusercontent.com/adminouyang/231006/refs/heads/main/py/TV/EPG/epg.xml"
# =================================================


# ---------------- 测速配置（按省份） ----------------
# 用户维护：每个省份对应若干 rtp/udp 流地址，用于测速
CITY_STREAMS = {
    "安徽电信": ["udp/238.1.78.150:7072"],
    "北京电信": ["rtp/225.1.8.21:8002"],
    "北京联通": ["rtp/239.3.1.241:8000"],
    "江苏电信": ["udp/239.49.8.19:9614"],
    "四川电信": ["udp/239.94.0.59:5140"],
    "四川移动": ["rtp/239.11.0.78:5140"],
    "四川联通": ["rtp/239.0.0.1:5140"],
    "上海电信": ["rtp/233.18.204.51:5140"],
    "云南电信": ["rtp/239.200.200.145:8840"],
    "内蒙古电信": ["rtp/239.29.0.2:5000"],
    "吉林电信": ["rtp/239.37.0.125:5540"],
    "天津电信": ["rtp/239.5.1.1:5000"],
    "天津联通": ["rtp/225.1.1.111:5002"],
    "宁夏电信": ["rtp/239.121.4.94:8538"],
    "山东电信": ["udp/239.21.1.87:5002"],
    "山东联通": ["rtp/239.253.254.78:8000"],
    "山西电信": ["udp/239.1.1.1:8001"],
    "山西联通": ["rtp/226.0.2.152:9128"],
    "广东电信": ["udp/239.77.1.19:5146"],
    "广东移动": ["rtp/239.20.0.101:2000"],
    "广东联通": ["udp/239.0.1.1:5001"],
    "广西电信": ["udp/239.81.0.107:4056"],
    "新疆电信": ["udp/238.125.3.174:5140"],
    "江西电信": ["udp/239.252.220.63:5140"],
    "河北电信": ["rtp/239.254.200.174:6000"],
    "河南电信": ["rtp/239.16.20.21:10210"],    
    "河南联通": ["rtp/225.1.4.98:1127"],
    "浙江电信": ["udp/233.50.201.100:5140"],
    "海南电信": ["rtp/239.253.64.253:5140"],
    "湖北电信": ["rtp/239.254.96.115:8664"],
    "湖北联通": ["rtp/228.0.0.60:6108"],
    "湖南电信": ["udp/239.76.253.101:9000"],
    "甘肃电信": ["udp/239.255.30.249:8231"],
    "福建电信": ["rtp/239.61.2.132:8708"],
    "贵州电信": ["rtp/238.255.2.1:5999"],
    "辽宁联通": ["rtp/232.0.0.126:1234"],
    "重庆电信": ["rtp/235.254.196.249:1268"],
    "重庆联通": ["udp/225.0.4.187:7980"],
    "陕西电信": ["rtp/239.111.205.35:5140"],
    "青海电信": ["rtp/239.120.1.64:8332"],
    "黑龙江联通": ["rtp/229.58.190.150:5000"],
}


# ==================== 输入解析 ====================

def parse_test_ip_line(line):
    line = line.strip()
    if "$" in line:
        addr, province = line.split("$", 1)
    else:
        addr, province = line, ""
    province = province.strip()
    ip_part, port = addr.strip().split(':')
    a, b, c_str, d_str = ip_part.split('.')
    has_range = '-' in c_str
    return a, b, c_str, d_str, port, has_range, province


def read_test_ip(input_file):
    print(f"读取设置文件：{input_file}")
    raw_lines = []
    groups = []
    if not os.path.exists(input_file):
        print(f"  文件不存在：{input_file}")
        return raw_lines, groups

    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if ":" not in stripped:
                continue
            try:
                a, b, c_str, d_str, port, has_range, province = parse_test_ip_line(stripped)
            except Exception as e:
                print(f"第{line_num}行：解析失败，跳过 ({e}) -> {stripped}")
                continue
            if not province:
                print(f"第{line_num}行：缺少省份信息，跳过 -> {stripped}")
                continue
            print(f"第{line_num}行：http://{a}.{b}.{c_str}.{d_str}:{port}/status 添加成功  ({province})")
            raw_lines.append(stripped)
            groups.append((a, b, c_str, d_str, port, has_range, province))
    return raw_lines, groups


# ==================== IP 生成 ====================

def generate_d_only(a, b, c_str, d_str, port):
    c = int(c_str)
    return [f"{a}.{b}.{c}.{y}:{port}" for y in range(1, 256)]


def generate_cd_full(a, b, c_str, d_str, port):
    return [f"{a}.{b}.{x}.{y}:{port}" for x in range(1, 256) for y in range(1, 256)]


def generate_c_range(a, b, c_str, d_str, port):
    c_first, c_last = c_str.split('-')
    c_first, c_last = int(c_first), int(c_last)
    return [f"{a}.{b}.{x}.{y}:{port}" for x in range(c_first, c_last + 1) for y in range(1, 256)]


# ==================== 单 IP 检测 ====================

async def check_one(session, sem, ip_port):
    for path in ["/status", "/stat"]:
        url = f"http://{ip_port}{path}"
        try:
            async with sem:
                async with session.get(
                    url,
                    timeout=ClientTimeout(total=HTTP_TIMEOUT, connect=HTTP_CONNECT_TIMEOUT)
                ) as resp:
                    if resp.status == 200:
                        body = await resp.content.read(2048)
                        text = body.decode('utf-8', errors='ignore')
                        if "Multi stream daemon" in text or "udpxy" in text:
                            return ip_port, path
        except (asyncio.TimeoutError, aiohttp.ClientError, OSError):
            continue
    return None


# ==================== 并发扫描（带提前停止） ====================

async def scan_until(session, sem, ip_ports, stop_count, label):
    valid = []
    if not ip_ports:
        return valid
    tasks = [asyncio.create_task(check_one(session, sem, ip)) for ip in ip_ports]
    try:
        for coro in asyncio.as_completed(tasks):
            result = await coro
            if result is not None:
                ip_port, path = result
                valid.append(ip_port)
                print(f"  有效 IP: http://{ip_port}{path}")
                if len(valid) >= stop_count:
                    print(f"  ({label}) 已凑满 {stop_count} 个有效 IP，停止扫描")
                    break
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()
    return valid


async def scan_group(a, b, c_str, d_str, port, has_range):
    """
    扫描一组配置，返回 (valid_ips, scan_fully_exhausted)
    scan_fully_exhausted:
      - True: 扫描已完全穷尽（D段全部扫完仍0有效，或有区间全部扫完0有效）
      - False: 因提前停止（凑满即停）而未扫完
    用于判断 test_ip.txt 是否删除：未扫完 → 不删除（留到以后设置区间）
    """
    sem = asyncio.Semaphore(HTTP_CONCURRENCY)
    connector = TCPConnector(limit=0, limit_per_host=30, ttl_dns_cache=300)
    timeout = ClientTimeout(total=HTTP_TIMEOUT, connect=HTTP_CONNECT_TIMEOUT)

    all_valid = []
    fully_exhausted = False

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:

        if not has_range:
            # --- 无区间：先扫 D 段 ---
            ip_ports = generate_d_only(a, b, c_str, d_str, port)
            print(f"开始扫描：{a}.{b}.{c_str}.{d_str}:{port}  (D段 共 {len(ip_ports)} 个)")
            valid = await scan_until(session, sem, ip_ports, D_STOP_COUNT, "D段")
            all_valid.extend(valid)

            if all_valid:
                # D段找到了有效IP，但因 stop_count 可能提前停止 → 未完全穷尽
                return sorted(set(all_valid)), False

            # --- D 段 0 个有效，才转扫 C+D ---
            print(f"D段有效 0 个，扩展扫描 C(1-255)+D(1-255)")
            ip_ports_cd = generate_cd_full(a, b, c_str, d_str, port)
            print(f"开始扫描：{a}.{b}.*.{d_str}:{port}  (C+D 共 {len(ip_ports_cd)} 个)")
            valid_cd = await scan_until(session, sem, ip_ports_cd, CD_STOP_COUNT, "C+D段")
            all_valid.extend(valid_cd)

            if valid_cd:
                # C+D段找到了，但因 stop_count=1 提前停止 → 未完全穷尽
                return sorted(set(all_valid)), False
            else:
                # C+D段全部扫完，0 个有效 → 完全穷尽
                fully_exhausted = True

        else:
            # --- 有区间：直接扫 C(区间)+D ---
            ip_ports = generate_c_range(a, b, c_str, d_str, port)
            print(f"开始扫描：{a}.{b}.{c_str}.{d_str}:{port}  (C区间 共 {len(ip_ports)} 个)")
            valid = await scan_until(session, sem, ip_ports, CD_STOP_COUNT, "C区间")
            all_valid.extend(valid)

            if valid:
                # 找到了但因 stop_count 提前停止 → 未完全穷尽
                return sorted(set(all_valid)), False
            else:
                # 有区间全部扫完，0 个有效 → 完全穷尽
                fully_exhausted = True

    return sorted(set(all_valid)), fully_exhausted


# ==================== 测速 ====================

async def speed_test_one(session, sem, ip_port, stream_path):
    url = f"http://{ip_port}/{stream_path}"
    try:
        async with sem:
            async with session.get(url, timeout=ClientTimeout(total=SPEED_TEST_DURATION + 5)) as resp:
                if resp.status != 200:
                    return 0.0
                start = time.time()
                total = 0
                while time.time() - start < SPEED_TEST_DURATION:
                    chunk = await resp.content.read(64 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                elapsed = time.time() - start
                if elapsed <= 0:
                    return 0.0
                return (total / 1024.0) / elapsed   # KB/s
    except (asyncio.TimeoutError, aiohttp.ClientError, OSError):
        return 0.0


async def speed_test_ip(ip_port, stream_paths):
    sem = asyncio.Semaphore(HTTP_CONCURRENCY)
    connector = TCPConnector(limit=0, limit_per_host=30, ttl_dns_cache=300)
    timeout = ClientTimeout(total=SPEED_TEST_DURATION + 5)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [speed_test_one(session, sem, ip_port, sp) for sp in stream_paths]
        results = await asyncio.gather(*tasks, return_exceptions=False)

    max_speed = max(results) if results else 0.0
    return max_speed


async def filter_by_speed(valid_ips, stream_paths):
    """
    对有效 IP 列表并发测速，仅保留速率 > SPEED_THRESHOLD_KB 的 IP
    返回 [(ip_port, speed), ...] 排序（快的在前）
    """
    if not valid_ips:
        return []
    if not stream_paths:
        print("  无 CITY_STREAMS 测速配置，跳过测速，全部保留")
        return [(ip, 0.0) for ip in valid_ips]

    print(f"  测速中（阈值 {SPEED_THRESHOLD_KB} KB/s）...")
    sem = asyncio.Semaphore(HTTP_CONCURRENCY)

    async def _sem_do(ip):
        async with sem:
            return ip, await speed_test_ip(ip, stream_paths)

    results = await asyncio.gather(*[_sem_do(ip) for ip in valid_ips])

    passed = []
    for ip, spd in results:
        flag = "✓" if spd >= SPEED_THRESHOLD_KB else "✗"
        print(f"    {flag} http://{ip}  {spd:.1f} KB/s")
        if spd >= SPEED_THRESHOLD_KB:
            passed.append((ip, spd))

    passed.sort(key=lambda x: x[1], reverse=True)
    return passed


# ==================== 结果回写（省份 config） ====================

def append_to_config(province, valid_ips):
    config_path = os.path.join(BASE_DIR, f"{province}_config.txt")
    existing = set()
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    existing.add(line.split(',')[0].strip())
    new_ips = [ip for ip in valid_ips if ip not in existing]
    if new_ips:
        with open(config_path, 'a', encoding='utf-8') as f:
            for ip in new_ips:
                f.write(ip + "\n")
        print(f"  追加 {len(new_ips)} 个有效 IP 至 {config_path}")
    else:
        print(f"  无新增有效 IP（{config_path} 已包含所有结果）")
    return new_ips


def write_invalid_records(province, invalid_ips):
    if not invalid_ips:
        return
    os.makedirs(INVALID_DIR, exist_ok=True)
    invalid_path = os.path.join(INVALID_DIR, f"{province}_invalid.txt")
    with open(invalid_path, 'a', encoding='utf-8') as f:
        for ip in invalid_ips:
            f.write(ip + "\n")
    print(f"  无效 IP 已记录至 {invalid_path} ({len(invalid_ips)} 条)")


def rewrite_test_ip(kept_raw_lines):
    with open(INPUT_FILE, 'w', encoding='utf-8') as f:
        for line in sorted(set(kept_raw_lines)):
            f.write(line + "\n")


# ==================== 生成频道链接文件（per 省份） ====================

def load_logo_map():
    """读取 logo.txt -> {频道名: logo_url}"""
    logo = {}
    if not os.path.exists(LOGO_FILE):
        return logo
    with open(LOGO_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ',' in line:
                name, url = line.split(',', 1)
                logo[name.strip()] = url.strip()
    return logo


def get_beijing_time_str():
    """返回北京时间字符串：YYYY/MM/DD HH:MM更新"""
    tz_bj = timezone(timedelta(hours=8))
    now = datetime.now(tz_bj)
    return now.strftime("%Y/%m/%d %H:%M更新")


def write_m3u_header(f, group_title):
    """写入 m3u 头部（含 EPG 和分组信息）"""
    f.write(f'#EXTM3U x-tvg-url="{EPG_URL}"\n')


def write_m3u_channel(f, name, url, logo_url, group_title):
    """按标准格式写入单个频道"""
    logo_attr = f' tvg-logo="{logo_url}"' if logo_url else ''
    f.write(f'#EXTINF:-1{logo_attr} group-title="{group_title}",{name}\n')
    f.write(url + "\n")


def parse_template_channels(template_path):
    """
    解析省份模板文件，返回：
      channels: [(name, url), ...]   （url 中 ipipip 未替换）
      genre_lines: 记录分类行位置，用于保持顺序
      structure: [(is_genre, content_or_genre, channels_in_this_genre), ...]
    """
    channels = []
    genres = []  # [(genre_name, [(name, url), ...]), ...]
    current_genre = ""

    with open(template_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.rstrip("\n").strip()
            if not stripped:
                continue
            if stripped.endswith(",#genre#"):
                current_genre = stripped
            elif "," in stripped:
                name, url = stripped.split(",", 1)
                name = name.strip()
                url = url.strip()
                channels.append((name, url))
                if not genres or genres[-1][0] != current_genre:
                    genres.append((current_genre, [(name, url)]))
                else:
                    genres[-1][1].append((name, url))
    return channels, genres


def generate_province_files(province, ip_ports):
    """
    用 ip_ports（该省份通过测速的 IP 列表，按速度降序）替换模板中的 ipipip，
    为每个频道在每个 IP 下生成一条链接 → 同一频道可有多个链接。
    输出 py/udpxy/output/<省份>.txt 与 .m3u（标准格式，带 EPG/台标/分组/更新时间）

    返回该省份的频道列表：[(name, [url, url, ...]), ...]
        每个频道附带「按速度降序、去重、最多 MAX_LINKS_PER_CHANNEL 个」链接，供合并使用
    """
    template_path = os.path.join(TEMPLATE_DIR, f"{province}.txt")
    if not os.path.exists(template_path):
        print(f"  模板不存在，跳过：{template_path}")
        return []

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_txt = os.path.join(OUTPUT_DIR, f"{province}.txt")
    out_m3u = os.path.join(OUTPUT_DIR, f"{province}.m3u")

    logo_map = load_logo_map()
    update_time = get_beijing_time_str()

    # 解析模板，得到分类与频道（url 中 ipipip 未替换）
    _, genres = parse_template_channels(template_path)

    # 构建每个频道的多个链接：按 ip_ports 顺序（已按速度降序），每个 IP 一条，
    # 去重，最多 MAX_LINKS_PER_CHANNEL 个
    def build_urls(tpl_url):
        urls = []
        seen = set()
        for ip_port in ip_ports:
            real_url = tpl_url.replace("ipipip", f"{ip_port}")
            if real_url not in seen:
                seen.add(real_url)
                urls.append(real_url)
            if len(urls) >= MAX_LINKS_PER_CHANNEL:
                break
        return urls

    # channel_links: [(name, [url1, url2, ...]), ...]  保持模板分类/顺序
    channel_links = []
    for genre_line, ch_list in genres:
        for name, tpl_url in ch_list:
            channel_links.append((name, build_urls(tpl_url)))

    # ---- 写 .txt：按分类行 + 每个频道的多条链接 ----
    with open(out_txt, 'w', encoding='utf-8') as f:
        for genre_line, ch_list in genres:
            f.write(genre_line + "\n")
            for name, urls in channel_links:
                if any(tpl_name.strip() == name for tpl_name, _ in ch_list):
                    for u in urls:
                        f.write(f"{name},{u}\n")

    # ---- 写 .m3u（标准格式） ----
    with open(out_m3u, 'w', encoding='utf-8') as f:
        f.write(f'#EXTM3U x-tvg-url="{EPG_URL}"\n')
        first_channel = True
        for genre_line, ch_list in genres:
            group_title = genre_line.replace(",#genre#", "")
            for name, urls in channel_links:
                if not any(tpl_name.strip() == name for tpl_name, _ in ch_list):
                    continue
                logo = logo_map.get(name, "")
                for u in urls:
                    if GROUP_FIRST_USE_UPDATE_TIME and first_channel:
                        gt = update_time
                        first_channel = False
                    else:
                        gt = group_title
                    write_m3u_channel(f, name, u, logo, gt)

    total_links = sum(len(urls) for _, urls in channel_links)
    print(f"  生成频道链接：{out_txt} ({len(channel_links)} 个频道, {total_links} 条链接)")
    print(f"  生成播放列表：{out_m3u}（标准格式，EPG + 台标 + 分组 + 更新时间）")
    return channel_links


# ==================== 合并（按 demo.txt 排序/分类，别名匹配） ====================

def parse_demo(demo_path):
    """
    解析 demo.txt，返回：
      groups: [(分类名, [主频道名, [别名...]]), ...]
      顺序严格按 demo.txt
    """
    groups = []
    current_genre = ""
    current_list = []
    with open(demo_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip("\n").strip()
            if not line:
                continue
            if line.endswith(",#genre#"):
                if current_genre and current_list:
                    groups.append((current_genre, current_list))
                current_genre = line
                current_list = []
            else:
                parts = [p.strip() for p in line.split("|")]
                primary = parts[0]
                aliases = [p for p in parts[1:] if p]
                current_list.append((primary, aliases))
        if current_genre and current_list:
            groups.append((current_genre, current_list))
    return groups


def build_alias_index(all_channels):
    """
    all_channels: {province: [(name, [(url, speed), ...]), ...]}
    返回 {name_lower: [(url, speed), ...]}  聚合所有省份的同名频道链接
    """
    index = {}
    for prov, ch_list in all_channels.items():
        for name, url_speed_list in ch_list:
            key = name.strip().lower()
            index.setdefault(key, []).extend(url_speed_list)
    return index


def match_channel_links(primary, aliases, alias_index):
    """返回该频道（主名+别名）聚合后的 [(url, speed), ...]"""
    candidates = [primary] + aliases
    collected = []
    seen_urls = set()
    for c in candidates:
        if not c:
            continue
        key = c.strip().lower()
        if key in alias_index:
            for url, spd in alias_index[key]:
                if url not in seen_urls:
                    seen_urls.add(url)
                    collected.append((url, spd))
    return collected


def merge_and_output(all_channels, demo_path, logo_map, output_dir):
    """
    all_channels: {province: [(name, [(url, speed), ...]), ...]}
    按 demo.txt 的分类与顺序，用别名匹配，同一频道聚合多省份/多IP链接，
    按速度降序、去重、最多保留 MAX_LINKS_PER_CHANNEL 个，
    输出 all.txt / all.m3u（标准格式）
    """
    os.makedirs(output_dir, exist_ok=True)
    groups = parse_demo(demo_path)
    alias_index = build_alias_index(all_channels)

    out_txt = os.path.join(output_dir, "all.txt")
    out_m3u = os.path.join(output_dir, "all.m3u")
    update_time = get_beijing_time_str()

    txt_lines = []
    m3u_lines = []

    matched_any = False
    first_channel = True

    for genre, ch_list in groups:
        group_title = genre.replace(",#genre#", "")
        group_items = []  # [(name, [url, ...])]

        for primary, aliases in ch_list:
            links = match_channel_links(primary, aliases, alias_index)
            if not links:
                continue
            # 按速度降序，取前 MAX_LINKS_PER_CHANNEL
            links.sort(key=lambda x: x[1], reverse=True)
            top_urls = [url for url, _ in links[:MAX_LINKS_PER_CHANNEL]]
            group_items.append((primary, top_urls))

        if not group_items:
            continue

        matched_any = True

        # ---- txt 输出：分类行 + 频道多链接 ----
        txt_lines.append(f"{genre}")
        for name, urls in group_items:
            for u in urls:
                txt_lines.append(f"{name},{u}")

        # ---- m3u 输出（标准格式） ----
        for name, urls in group_items:
            logo = logo_map.get(name, "")
            for u in urls:
                if GROUP_FIRST_USE_UPDATE_TIME and first_channel:
                    gt = update_time
                    first_channel = False
                else:
                    gt = group_title
                logo_attr = f' tvg-logo="{logo}"' if logo else ''
                m3u_lines.append(f'#EXTINF:-1{logo_attr} group-title="{gt}",{name}')
                m3u_lines.append(u)

    # 写 all.txt
    with open(out_txt, 'w', encoding='utf-8') as f:
        f.write("\n".join(txt_lines) + "\n")

    # 写 all.m3u（标准格式，头部含 EPG）
    with open(out_m3u, 'w', encoding='utf-8') as f:
        f.write(f'#EXTM3U x-tvg-url="{EPG_URL}"\n')
        if m3u_lines:
            f.write("\n".join(m3u_lines) + "\n")

    if matched_any:
        total_channels = sum(
            1 for _, ch_list in groups
            for primary, aliases in ch_list
            if match_channel_links(primary, aliases, alias_index)
        )
        total_links = sum(
            min(len(match_channel_links(primary, aliases, alias_index)), MAX_LINKS_PER_CHANNEL)
            for _, ch_list in groups
            for primary, aliases in ch_list
        )
        print(f"  合并：匹配 {total_channels} 个频道，共 {total_links} 条链接（每频道最多 {MAX_LINKS_PER_CHANNEL} 个，按速度降序）")
    else:
        print("  合并：demo.txt 中未匹配到任何频道，all.txt/all.m3u 为空")

    print(f"  合并输出：{out_txt}")
    print(f"  合并输出：{out_m3u}（标准格式）")


# ==================== 主流程 ====================

def main():
    start = time.time()
    os.makedirs(INVALID_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logo_map = load_logo_map()

    raw_lines, groups = read_test_ip(INPUT_FILE)
    print(f"\n读取完成，共需扫描 {len(groups)} 组")
    if not groups:
        print("无有效配置，跳过")
        return

    # province_results[province] = {
    #     "valid": [(ip, speed), ...],   # 本组通过测速的 IP（速度降序）
    #     "invalid_fully": [],    # 完全穷尽扫描仍无效 → 可能删除
    #     "invalid_partial": [],  # 因提前停止/测速未过 → 保留
    #     "kept_raw": []
    # }
    province_results = {}

    for idx, (a, b, c_str, d_str, port, has_range, province) in enumerate(groups, 1):
        if province not in province_results:
            province_results[province] = {
                "valid": [], "invalid_fully": [], "invalid_partial": [], "kept_raw": []
            }
        res = province_results[province]

        original_raw = f"{a}.{b}.{c_str}.{d_str}:{port}${province}"
        original_addr = f"{a}.{b}.{c_str}.{d_str}:{port}"

        print(f"\n--- 第 {idx}/{len(groups)} 组 ({province}) ---")

        # ---- 扫描（返回是否完全穷尽） ----
        valid_ips, fully_exhausted = asyncio.run(
            scan_group(a, b, c_str, d_str, port, has_range)
        )

        # ---- 测速筛选 ----
        stream_paths = CITY_STREAMS.get(province, [])
        if valid_ips:
            print(f"  检测到 {len(valid_ips)} 个有效 IP，开始测速...")
            passed = asyncio.run(filter_by_speed(valid_ips, stream_paths))
        else:
            passed = []

        if passed:
            # ===== 有效且通过测速 → 保留在 test_ip.txt + 保存到省份 config =====
            # 累积本省份所有通过测速的 IP（带速度，供多链接/排序使用）
            res["valid"].extend(passed)
            # 全部通过 IP 都记入省份 config（去重）
            all_passed_ips = [ip for ip, _ in passed]
            append_to_config(province, all_passed_ips)
            # 保留在 test_ip.txt
            res["kept_raw"].append(original_raw)
            best_ip, best_speed = passed[0]
            print(f"  本组最佳 IP: http://{best_ip}  ({best_speed:.1f} KB/s)")
            print(f"  有效配置，保留在 {os.path.basename(INPUT_FILE)}：{original_addr}")

        else:
            # ===== 无效（无有效IP 或 测速未过） =====
            if fully_exhausted:
                if has_range:
                    res["invalid_fully"].append(original_addr)
                    res["kept_raw"].append(original_raw)
                    print(f"  有区间 + 完全无效，保留在 {os.path.basename(INPUT_FILE)}：{original_addr}")
                else:
                    res["invalid_fully"].append(original_addr)
                    print(f"  无区间 + 完全无效，从 {os.path.basename(INPUT_FILE)} 删除：{original_addr}")
            else:
                res["invalid_partial"].append(original_addr)
                res["kept_raw"].append(original_raw)
                print(f"  扫描未完全（提前停止/测速未过），保留在 {os.path.basename(INPUT_FILE)}：{original_addr}")

    # ========== 汇总：写省份 config / 无效记录 / 生成频道链接 ==========
    print(f"\n{'='*30}\n  汇总保存\n{'='*30}")

    # all_channels: province -> [(name, [(url, speed), ...]), ...]
    all_channels = {}

    for province in sorted(province_results.keys()):
        res = province_results[province]

        if res["valid"]:
            # 本省份所有通过测速 IP，按速度降序、去重
            by_speed = sorted(set(res["valid"]), key=lambda x: x[1], reverse=True)
            ip_ports = [ip for ip, _ in by_speed]
            # key 用 hostname（不含端口），与 urlparse(u).hostname 一致
            ip_speed_map = {urlparse(f"http://{ip}").hostname or ip: spd for ip, spd in by_speed}

            # 生成频道链接文件（每个频道 = 多 IP 链接，按速度降序，最多 MAX）
            print(f"\n[{province}] 生成频道链接（{len(ip_ports)} 个有效 IP，按速度降序）")
            channel_links = generate_province_files(province, ip_ports)

            # 为合并构建带速度的结构：province -> [(name, [(url, speed), ...])]
            if channel_links:
                named = []
                for name, urls in channel_links:
                    url_speed = []
                    for u in urls:
                        host = urlparse(u).hostname or ""
                        url_speed.append((u, ip_speed_map.get(host, 0.0)))
                    named.append((name, url_speed))
                all_channels[province] = named

        # 无效记录（完全无效 + 部分无效）
        all_invalid = sorted(set(res["invalid_fully"] + res["invalid_partial"]))
        if all_invalid:
            write_invalid_records(province, all_invalid)

    # ========== 合并输出 all.txt / all.m3u ==========
    if os.path.exists(DEMO_FILE) and all_channels:
        print(f"\n{'='*30}\n  合并输出（按 demo.txt 排序/分类）\n{'='*30}")
        merge_and_output(all_channels, DEMO_FILE, logo_map, OUTPUT_DIR)
    else:
        if not os.path.exists(DEMO_FILE):
            print(f"\n未找到 demo.txt：{DEMO_FILE}，跳过合并")
        if not all_channels:
            print("无可用频道，跳过合并")

    # ========== 回写 test_ip.txt ==========
    kept_all = []
    for province in sorted(province_results.keys()):
        kept_all.extend(province_results[province]["kept_raw"])
    rewrite_test_ip(kept_all)

    print(f"\n全部扫描完成，耗时 {time.time() - start:.1f} 秒")


if __name__ == "__main__":
    main()
