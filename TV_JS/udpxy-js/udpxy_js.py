#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP 扫描检测脚本（完善版 · 按省份分流 + 测速 + 生成 JS 频道文件）

输入：TV_JS/udpxy-js/ip.txt
    格式：ip:port$省份    例：58.37.152.210:4022$上海电信

流程：
  1) 扫描检测有效 IP（/status -> /stat）
  2) 对有效 IP 用 CITY_STREAMS 测速，> SPEED_THRESHOLD_KB 才保留
  3) 用省份模板生成 <key>.js（替换 ipipip，同频道多链接按速度降序，最多 N 个）
     生成文件格式为 TVRemote.define({...})
  4) 不再生成 .txt / .m3u / all.js

ip.txt 维护规则（核心）：
  场景                                  ip.txt   Invalid_ip_file/
  ------------------------------------------------------------------------
  无区间 + 扫描完全穷尽(C+D全扫)仍0有效   删除           存档 ✓
  有区间 + 区间全扫完仍0有效              保留           存档 ✓
  因"凑满即停"提前停止(未扫完)           保留           不存档
  有效但测速未通过(未扫完)               保留           不存档
  有效且测速通过                         保留           不存档

<省份>.txt（IP白名单）规则：
  - 只保存「测速通过」的 IP
  - 每次运行前，先对本文件已有 IP 做"在线复检"（/status -> /stat），
    失效(离线/非 udpxy) 的 IP 自动删除，只保留当前仍然有效的 IP
  - 再把本轮新测速通过的 IP 追加进去（去重）
"""

import asyncio
import os
import time

import aiohttp
from aiohttp import ClientTimeout, TCPConnector

# ==================== 可调参数 ====================
BASE_DIR = "TV_JS/udpxy-js"
INPUT_FILE = os.path.join(BASE_DIR, "ip.txt")
INVALID_DIR = os.path.join(BASE_DIR, "Invalid_ip_file")
TEMPLATE_DIR = os.path.join(BASE_DIR, "template")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

HTTP_CONCURRENCY = 300        # 并发数
HTTP_TIMEOUT = 4.0            # 总超时(秒)
HTTP_CONNECT_TIMEOUT = 1.0    # 连接超时(秒)
D_STOP_COUNT = 2              # D 段扫描停止阈值（凑满即停）
CD_STOP_COUNT = 1             # C+D / C区间 扫描停止阈值

SPEED_DURATION = 3.0     # 测速采样时长(秒)
SPEED_THRESHOLD_KB = 300.0    # 最低速率阈值(KB/s)，低于此值丢弃
MAX_LINKS_PER_CHANNEL = 5     # 同一频道最多保留的链接数（按速度降序取前 N）

CONFIG_HEALTH_CHECK = True    # True: 每次运行清理失效 IP；False: 只追加不清理
# =================================================

# ---------------- 省份 key/group 映射 ----------------
OPERATOR_SUFFIXES = ["电信", "联通", "移动", "广电", "铁通"]

PROVINCE_META = {
    "安徽电信":   {"key": "anhui",      "group": "安徽"},
    "北京电信":   {"key": "beijing",    "group": "北京"},
    "北京联通":   {"key": "beijing",    "group": "北京"},
    "江苏电信":   {"key": "jiangsu",    "group": "江苏"},
    "四川电信":   {"key": "sichuan",    "group": "四川"},
    "四川移动":   {"key": "sichuan",    "group": "四川"},
    "四川联通":   {"key": "sichuan",    "group": "四川"},
    "上海电信":   {"key": "shanghai",   "group": "上海"},
    "云南电信":   {"key": "yunnan",     "group": "云南"},
    "海南电信":   {"key": "hainan",     "group": "海南"},
    "湖北电信":   {"key": "hubei",      "group": "湖北"},
    "湖北联通":   {"key": "hubei",      "group": "湖北"},
    "湖南电信":   {"key": "hunan",      "group": "湖南"},
    "甘肃电信":   {"key": "gansu",      "group": "甘肃"},
    "福建电信":   {"key": "fujian",     "group": "福建"},
    "贵州电信":   {"key": "guizhou",    "group": "贵州"},
    "辽宁联通":   {"key": "liaoning",   "group": "辽宁"},
    "重庆电信":   {"key": "chongqing",  "group": "重庆"},
    "重庆联通":   {"key": "chongqing",  "group": "重庆"},
    "陕西电信":   {"key": "shaanxi",    "group": "陕西"},
    "青海电信":   {"key": "qinghai",    "group": "青海"},
    "黑龙江联通": {"key": "heilongjiang","group": "黑龙江"},
}

def get_province_meta(province):
    """返回 (key, group)，优先从 PROVINCE_META 查；否则去掉运营商后缀再尝试。"""
    if province in PROVINCE_META:
        meta = PROVINCE_META[province]
        return meta["key"], meta["group"]

    main_name = province
    for suffix in OPERATOR_SUFFIXES:
        if province.endswith(suffix):
            main_name = province[:-len(suffix)]
            break

    pinyin_map = {
        "安徽": "anhui", "北京": "beijing", "重庆": "chongqing", "福建": "fujian",
        "甘肃": "gansu", "广东": "guangdong", "广西": "guangxi", "贵州": "guizhou",
        "海南": "hainan", "河北": "hebei", "黑龙江": "heilongjiang", "河南": "henan",
        "湖北": "hubei", "湖南": "hunan", "江苏": "jiangsu", "江西": "jiangxi",
        "吉林": "jilin", "辽宁": "liaoning", "内蒙古": "neimenggu", "宁夏": "ningxia",
        "青海": "qinghai", "山东": "shandong", "上海": "shanghai", "山西": "shanxi",
        "陕西": "shaanxi", "四川": "sichuan", "天津": "tianjin", "西藏": "xizang",
        "新疆": "xinjiang", "云南": "yunnan", "浙江": "zhejiang",
    }
    if main_name in pinyin_map:
        return pinyin_map[main_name], main_name

    print(f"警告：未找到省份 {province} 的 key 映射，使用原字符串作为 key")
    return province, province


# ---------------- 测速配置（按省份） ----------------
CITY_STREAMS = {
    "安徽电信": ["udp/238.1.78.150:7072"],
    "北京电信": ["rtp/225.1.8.21:8002"],
    "北京联通": ["rtp/239.3.1.241:8000"],
    "江苏电信": ["udp/239.49.8.19:9614"],
    "四川电信": ["udp/239.94.0.59:5140"],
    "四川移动": ["rtp/239.11.0.77:5140"],
    "四川联通": ["rtp/239.0.0.1:5140"],
    "上海电信": ["rtp/233.18.204.51:5140"],
    "云南电信": ["rtp/239.200.200.145:8840"],
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

def parse_ip_line(line):
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


def read_ip(input_file):
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
                a, b, c_str, d_str, port, has_range, province = parse_ip_line(stripped)
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
    """仅 D 段变化（1-255），C 固定。"""
    c = int(c_str)
    start_d = int(d_str)
    d_order = list(range(start_d + 1, 256)) + list(range(1, start_d + 1))
    return [f"{a}.{b}.{c}.{y}:{port}" for y in d_order]


def generate_cd_full(a, b, c_str, d_str, port):
    """C(1-255) + D(1-255) 全扫，C 从当前值+1 开始绕圈。"""
    start_c = int(c_str)
    c_order = list(range(start_c + 1, 256)) + list(range(1, start_c + 1))
    start_d = int(d_str)
    d_order = list(range(start_d + 1, 256)) + list(range(1, start_d + 1))
    return [f"{a}.{b}.{x}.{y}:{port}" for x in c_order for y in d_order]


def generate_c_range(a, b, c_str, d_str, port):
    c_first, c_last = c_str.split('-')
    c_first, c_last = int(c_first), int(c_last)
    return [f"{a}.{b}.{x}.{y}:{port}" for x in range(c_first, c_last + 1) for y in range(1, 256)]


# ==================== 单 IP 检测 ====================

async def check_one(session, sem, ip_port):
    """检测单个 ip:port 是否为可用 udpxy（先 /status，失败再 /stat）"""
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
      - True:  扫描已完全穷尽（D段全部扫完仍0有效 → 转 C+D 全扫；C+D 也全扫完仍0有效）
      - False: 因"凑满即停"提前停止，未扫完
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
                # D段找到有效IP，但因 stop_count 提前停止 → 未完全穷尽
                return sorted(set(all_valid)), False

            # --- D 段 0 个有效，才转扫 C+D（此时才算"扫了C段和D段"）---
            print(f"D段有效 0 个，扩展扫描 C(1-255)+D(1-255)")
            ip_ports_cd = generate_cd_full(a, b, c_str, d_str, port)
            print(f"开始扫描：{a}.{b}.*.{d_str}:{port}  (C+D 共 {len(ip_ports_cd)} 个)")
            valid_cd = await scan_until(session, sem, ip_ports_cd, CD_STOP_COUNT, "C+D段")
            all_valid.extend(valid_cd)

            if valid_cd:
                # C+D段找到有效IP，但因 stop_count=1 提前停止 → 未完全穷尽
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
                # 找到有效IP，但因 stop_count 提前停止 → 未完全穷尽
                return sorted(set(all_valid)), False
            else:
                # 有区间全部扫完，0 个有效 → 完全穷尽
                fully_exhausted = True

    return sorted(set(all_valid)), fully_exhausted


# ==================== 测速 ====================

async def speed_one(session, sem, ip_port, stream_path):
    url = f"http://{ip_port}/{stream_path}"
    try:
        async with sem:
            async with session.get(url, timeout=ClientTimeout(total=SPEED_DURATION + 5)) as resp:
                if resp.status != 200:
                    return 0.0
                start = time.time()
                total = 0
                while time.time() - start < SPEED_DURATION:
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


async def speed_ip(ip_port, stream_paths):
    sem = asyncio.Semaphore(HTTP_CONCURRENCY)
    connector = TCPConnector(limit=0, limit_per_host=30, ttl_dns_cache=300)
    timeout = ClientTimeout(total=SPEED_DURATION + 5)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [speed_one(session, sem, ip_port, sp) for sp in stream_paths]
        results = await asyncio.gather(*tasks, return_exceptions=False)

    max_speed = max(results) if results else 0.0
    return max_speed


async def filter_by_speed(valid_ips, stream_paths):
    """对有效 IP 列表并发测速，仅保留速率 > SPEED_THRESHOLD_KB 的 IP"""
    if not valid_ips:
        return []
    if not stream_paths:
        print("  无 CITY_STREAMS 测速配置，跳过测速，全部保留")
        return [(ip, 0.0) for ip in valid_ips]

    print(f"  测速中（阈值 {SPEED_THRESHOLD_KB} KB/s）...")
    sem = asyncio.Semaphore(HTTP_CONCURRENCY)

    async def _sem_do(ip):
        async with sem:
            return ip, await speed_ip(ip, stream_paths)

    results = await asyncio.gather(*[_sem_do(ip) for ip in valid_ips])

    passed = []
    for ip, spd in results:
        flag = "✓" if spd >= SPEED_THRESHOLD_KB else "✗"
        print(f"    {flag} http://{ip}  {spd:.1f} KB/s")
        if spd >= SPEED_THRESHOLD_KB:
            passed.append((ip, spd))

    passed.sort(key=lambda x: x[1], reverse=True)
    return passed


# ==================== 结果回写（省份 IP 白名单） ====================

def read_ips(province):
    """读取 <省份>.txt 中已有的 IP（每行一个 ip:port）"""
    config_path = os.path.join(BASE_DIR, f"{province}.txt")
    ips = []
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    ips.append(line.split(',')[0].strip())
    return ips


async def health_check(province):
    """对本省份 .txt 中已有的 IP 做在线复检，失效的删除。"""
    existing = read_ips(province)
    if not existing:
        return []

    sem = asyncio.Semaphore(HTTP_CONCURRENCY)
    connector = TCPConnector(limit=0, limit_per_host=30, ttl_dns_cache=300)
    timeout = ClientTimeout(total=HTTP_TIMEOUT, connect=HTTP_CONNECT_TIMEOUT)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [asyncio.create_task(check_one(session, sem, ip)) for ip in existing]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    alive = []
    dead = []
    for ip, r in zip(existing, results):
        if r is not None and not isinstance(r, Exception):
            alive.append(ip)
        else:
            dead.append(ip)

    if dead:
        config_path = os.path.join(BASE_DIR, f"{province}.txt")
        with open(config_path, 'w', encoding='utf-8') as f:
            for ip in alive:
                f.write(ip + "\n")
        print(f"   复检：{len(dead)} 个失效 IP 已清理（{province}），保留 {len(alive)} 个")
    else:
        if alive:
            print(f"   复检：{province} 全部 {len(alive)} 个 IP 仍有效")

    return alive


async def sync(province, new_passed_ips):
    """
    同步 <省份>.txt（IP白名单）：
      1) 先对已有 IP 做在线复检，删除失效 IP
      2) 再把本轮新测速通过的 IP 追加进去（去重）
    """
    if CONFIG_HEALTH_CHECK:
        alive = await health_check(province)
    else:
        alive = read_ips(province)

    alive_set = set(alive)
    added = []
    for ip in new_passed_ips:
        if ip not in alive_set:
            alive_set.add(ip)
            added.append(ip)

    config_path = os.path.join(BASE_DIR, f"{province}.txt")
    with open(config_path, 'w', encoding='utf-8') as f:
        for ip in sorted(alive_set):
            f.write(ip + "\n")

    if added:
        print(f"   更新：新增 {len(added)} 个测速通过 IP → {config_path}")
    print(f"   当前共 {len(alive_set)} 个有效 IP（{province}）")
    return added, len(alive_set)


def write_invalid_records(province, invalid_ips):
    """将"完全穷尽扫描仍无效"的 IP 记录到 Invalid_ip_file/"""
    if not invalid_ips:
        return
    os.makedirs(INVALID_DIR, exist_ok=True)
    invalid_path = os.path.join(INVALID_DIR, f"{province}_invalid.txt")
    with open(invalid_path, 'a', encoding='utf-8') as f:
        for ip in invalid_ips:
            f.write(ip + "\n")
    print(f"  存档至 {invalid_path}（完全穷尽仍无效，共 {len(invalid_ips)} 条）")


def rewrite_ip(kept_raw_lines):
    """回写 ip.txt（仅保留应保留的行）"""
    with open(INPUT_FILE, 'w', encoding='utf-8') as f:
        for line in sorted(set(kept_raw_lines)):
            f.write(line + "\n")


# ==================== 生成 JS 频道文件 ====================

def parse_template_channels(template_path):
    """
    解析省份模板文件，返回：
      channels: [(name, url), ...]   （url 中 ipipip 未替换）
      genres:   [(genre_line, [(name, url), ...]), ...]  保持分类顺序
    """
    channels = []
    genres = []
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


def generate_province_js(province, ip_ports):
    """
    用 ip_ports（该省份测速通过的 IP 列表，按速度降序）替换模板中的 ipipip，
    为每个频道生成多个链接（按 IP 顺序，去重，最多 MAX_LINKS_PER_CHANNEL 个）。
    输出 OUTPUT_DIR/<key>.js，格式为 TVRemote.define({...})

    返回该省份的频道列表：[(name, [(url, speed), ...]), ...]（供后续使用）
    """
    template_path = os.path.join(TEMPLATE_DIR, f"{province}.txt")
    if not os.path.exists(template_path):
        print(f"  模板不存在，跳过：{template_path}")
        return []

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # key 和 group
    key, group = get_province_meta(province)
    out_js = os.path.join(OUTPUT_DIR, f"{key}.js")

    _, genres = parse_template_channels(template_path)

    # ip_speed 映射：key=ip:port, value=speed
    ip_speed_list = [(ip, spd) for ip, spd in ip_ports]

    def build_urls_with_speed(tpl_url):
        """返回 [(url, speed), ...]"""
        urls = []
        seen = set()
        for ip_port, speed in ip_speed_list:
            real_url = tpl_url.replace("ipipip", ip_port)
            if real_url not in seen:
                seen.add(real_url)
                urls.append((real_url, speed))
            if len(urls) >= MAX_LINKS_PER_CHANNEL:
                break
        return urls

    # 构建频道列表（保持模板分类/顺序）
    channel_links = []  # [(name, [(url, speed), ...]), ...]
    for genre_line, ch_list in genres:
        for name, tpl_url in ch_list:
            channel_links.append((name, build_urls_with_speed(tpl_url)))

    # 构建 JS 内容
    js_lines = []
    js_lines.append("TVRemote.define({")
    js_lines.append(f'  key: "{key}",')
    js_lines.append(f'  group: "{group}",')
    js_lines.append("  list: [")

    for idx, (name, url_speed_list) in enumerate(channel_links):
        safe_name = name.replace('"', '\\"')
        js_lines.append("    { name: \"" + safe_name + "\",")
        js_lines.append("  urls: [")
        for j, (url, speed) in enumerate(url_speed_list, 1):
            comma = "," if j < len(url_speed_list) else ""
            js_lines.append(f"    \"{url}\"{comma}   // 线路{j}")
        js_lines.append("  ] }," if idx < len(channel_links) - 1 else "  ] }")

    js_lines.append("  ]")
    js_lines.append("});")

    with open(out_js, 'w', encoding='utf-8') as f:
        f.write("\n".join(js_lines) + "\n")

    total_links = sum(len(urls) for _, urls in channel_links)
    print(f"  生成频道文件：{out_js} ({len(channel_links)} 个频道, {total_links} 条链接)")
    return channel_links


# ==================== 主流程 ====================

async def _main_async():
    start = time.time()
    os.makedirs(INVALID_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    raw_lines, groups = read_ip(INPUT_FILE)
    print(f"\n读取完成，共需扫描 {len(groups)} 组")
    if not groups:
        print("无有效配置，跳过")
        return

    # province_results[province] = {
    #     "valid":   [(ip, speed), ...],  # 本轮测速通过的 IP（速度降序）
    #     "invalid_fully":   [],          # 完全穷尽扫描仍无效 → 删 ip + 存档 Invalid
    #     "invalid_partial": [],          # 未扫完(提前停止/测速未过) → 保留 ip，不存档
    #     "kept_raw": []                  # 需保留在 ip.txt 的原始行
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
        valid_ips, fully_exhausted = await scan_group(a, b, c_str, d_str, port, has_range)

        # ---- 测速筛选 ----
        stream_paths = CITY_STREAMS.get(province, [])
        if valid_ips:
            print(f"  检测到 {len(valid_ips)} 个有效 IP，开始测速...")
            passed = await filter_by_speed(valid_ips, stream_paths)
        else:
            passed = []

        if passed:
            # ===== 有效且通过测速 → 保留在 ip.txt + 同步到省份  =====
            res["valid"].extend(passed)
            # 保留在 ip.txt（有效即保留，无论有无区间）
            res["kept_raw"].append(original_raw)
            best_ip, best_speed = passed[0]
            print(f"  本组最佳 IP: http://{best_ip}  ({best_speed:.1f} KB/s)")
            print(f"  测速通过，保留在 {os.path.basename(INPUT_FILE)}：{original_addr}")

        else:
            # ===== 无效（无有效IP 或 测速未过） =====
            if fully_exhausted:
                # C段和D段都扫了，仍未扫出有效IP
                res["invalid_fully"].append(original_addr)
                if has_range:
                    # 有区间：保留在 ip.txt（下次继续扫），但仍存档到 Invalid
                    res["kept_raw"].append(original_raw)
                    print(f"  有区间 + 完全穷尽仍无效，保留在 {os.path.basename(INPUT_FILE)}（存档）：{original_addr}")
                else:
                    # 无区间：从 ip.txt 删除，并存档到 Invalid_ip_file
                    print(f"  无区间 + C/D段全扫仍无效，从 {os.path.basename(INPUT_FILE)} 删除并存档：{original_addr}")
            else:
                # 因"凑满即停"提前停止 或 测速未过 → 未扫完，不删除、不存档
                res["invalid_partial"].append(original_addr)
                res["kept_raw"].append(original_raw)
                print(f"  扫描未完全（提前停止/测速未过），保留在 {os.path.basename(INPUT_FILE)}：{original_addr}")

    # ========== 汇总：同步省份  / 存档无效 / 生成 JS ==========
    print(f"\n{'='*30}\n  汇总保存\n{'='*30}")

    for province in sorted(province_results.keys()):
        res = province_results[province]

        if res["valid"]:
            # 本省份本轮测速通过的 IP，按速度降序、去重
            by_speed = sorted(set(res["valid"]), key=lambda x: x[1], reverse=True)
            new_passed_ips = [ip for ip, _ in by_speed]

            # ---- 同步 .txt：先清理失效 IP，再追加本轮新通过 IP ----
            print(f"\n[{province}] 同步 .txt（只保留测速通过且当前在线的 IP）")
            await sync(province, new_passed_ips)

            # 用于生成 JS 的 IP 顺序 = 本轮通过的 IP（速度降序）
            ip_ports = new_passed_ips

            # 生成 JS 频道文件
            print(f"[{province}] 生成 JS 频道文件（{len(ip_ports)} 个测速通过 IP，按速度降序）")
            generate_province_js(province, by_speed)

        # 无效记录（仅"完全穷尽仍无效"才存档到 Invalid_ip_file）
        if res["invalid_fully"]:
            write_invalid_records(province, sorted(set(res["invalid_fully"])))

    # ========== 回写 ip.txt ==========
    kept_all = []
    for province in sorted(province_results.keys()):
        kept_all.extend(province_results[province]["kept_raw"])
    rewrite_ip(kept_all)

    print(f"\n全部扫描完成，耗时 {time.time() - start:.1f} 秒")


def main():
    asyncio.run(_main_async())


if __name__ == "__main__":
    main()
