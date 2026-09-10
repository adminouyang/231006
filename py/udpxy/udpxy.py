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
  场景                       test_ip.txt 处理
  无区间 + 有效(通过测速)     保留（同时保存到省份 config）
  有区间 + 有效(通过测速)     保留（同时保存到省份 config）
  无区间 + 无效               删除（记录到 Invalid_ip_file/）
  有区间 + 无效               保留（记录到 Invalid_ip_file/，下次继续扫描）
  即：仅「无区间 + 无效」才从 test_ip.txt 删除。
"""

import asyncio
import os
import re
import time

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
# =================================================


# ---------------- 测速配置（按省份） ----------------
# 用户维护：每个省份对应若干 rtp/udp 流地址，用于测速
CITY_STREAMS = {
    "安徽电信": ["udp/238.1.78.150:7072"],
    "四川电信": ["udp/239.94.0.59:5140"],
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
    sem = asyncio.Semaphore(HTTP_CONCURRENCY)
    connector = TCPConnector(limit=0, limit_per_host=30, ttl_dns_cache=300)
    timeout = ClientTimeout(total=HTTP_TIMEOUT, connect=HTTP_CONNECT_TIMEOUT)
    all_valid = []

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        if not has_range:
            ip_ports = generate_d_only(a, b, c_str, d_str, port)
            print(f"开始扫描：{a}.{b}.{c_str}.{d_str}:{port}  (D段 共 {len(ip_ports)} 个)")
            valid = await scan_until(session, sem, ip_ports, D_STOP_COUNT, "D段")
            all_valid.extend(valid)
            if all_valid:
                return sorted(set(all_valid))
            print(f"D段有效 0 个，扩展扫描 C(1-255)+D(1-255)")
            ip_ports_cd = generate_cd_full(a, b, c_str, d_str, port)
            print(f"开始扫描：{a}.{b}.*.{d_str}:{port}  (C+D 共 {len(ip_ports_cd)} 个)")
            valid_cd = await scan_until(session, sem, ip_ports_cd, CD_STOP_COUNT, "C+D段")
            all_valid.extend(valid_cd)
        else:
            ip_ports = generate_c_range(a, b, c_str, d_str, port)
            print(f"开始扫描：{a}.{b}.{c_str}.{d_str}:{port}  (C区间 共 {len(ip_ports)} 个)")
            valid = await scan_until(session, sem, ip_ports, CD_STOP_COUNT, "C区间")
            all_valid.extend(valid)
    return sorted(set(all_valid))


# ==================== 测速 ====================

async def speed_test_one(session, sem, ip_port, stream_path):
    """
    对 http://ip_port/stream_path 拉流 SPEED_TEST_DURATION 秒，
    返回速率(KB/s)；失败返回 0.0
    """
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
    """对一个 IP 用若干流地址测速，返回该 IP 的最大速率(KB/s)（任一达标即可）"""
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
        # 无测速配置：全部保留（不测速直接通过）
        print("  无 CITY_STREAMS 测速配置，跳过测速，全部保留")
        return [(ip, 0.0) for ip in valid_ips]

    print(f"  测速中（阈值 {SPEED_THRESHOLD_KB} KB/s）...")
    sem = asyncio.Semaphore(HTTP_CONCURRENCY)

    async def _do(ip):
        # 复用单个 session 较复杂，这里对每个 IP 独立测速（结果已聚合到 speed_test_ip）
        return ip, await speed_test_ip(ip, stream_paths)

    # 串行控制并发：用信号量包装
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
        for line in kept_raw_lines:
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
            # 格式：CCTV1, https://...
            if ',' in line:
                name, url = line.split(',', 1)
                logo[name.strip()] = url.strip()
    return logo


def generate_province_files(province, ip_port):
    """
    用 ip_port 替换模板 py/udpxy/template/<省份>.txt 中的 ipipip，
    输出 py/udpxy/output/<省份>.txt 与 .m3u
    返回该省份的频道列表 [(name, url), ...]，供合并使用
    """
    template_path = os.path.join(TEMPLATE_DIR, f"{province}.txt")
    if not os.path.exists(template_path):
        print(f"  模板不存在，跳过：{template_path}")
        return []

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_txt = os.path.join(OUTPUT_DIR, f"{province}.txt")
    out_m3u = os.path.join(OUTPUT_DIR, f"{province}.m3u")

    channels = []  # (name, url)
    lines_out = []
    with open(template_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.rstrip("\n")
            if not stripped.strip() or stripped.strip().endswith(",#genre#"):
                # 分类标题行原样保留
                lines_out.append(stripped)
                continue
            if "," in stripped:
                name, url = stripped.split(",", 1)
                name = name.strip()
                url = url.strip().replace("ipipip", f"{ip_port}")
                channels.append((name, url))
                lines_out.append(f"{name},{url}")

    # 写 .txt
    with open(out_txt, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines_out) + "\n")

    # 写 .m3u
    logo_map = load_logo_map()
    with open(out_m3u, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for name, url in channels:
            logo = logo_map.get(name, "")
            if logo:
                f.write(f'#EXTINF:-1 tvg-logo="{logo}",{name}\n')
            else:
                f.write(f"#EXTINF:-1,{name}\n")
            f.write(url + "\n")

    print(f"  生成频道链接：{out_txt} ({len(channels)} 个频道)")
    print(f"  生成播放列表：{out_m3u}")
    return channels


# ==================== 合并（按 demo.txt 排序/分类，别名匹配） ====================

def parse_demo(demo_path):
    """
    解析 demo.txt，返回：
      groups: [(分类名, [主频道名, [别名...]]), ...]
      顺序严格按 demo.txt
    """
    groups = []  # (genre, [(primary, [aliases]), ...])
    current_genre = ""
    current_list = []
    with open(demo_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip("\n").strip()
            if not line:
                continue
            if line.endswith(",#genre#"):
                # 保存上一个分类
                if current_genre and current_list:
                    groups.append((current_genre, current_list))
                current_genre = line
                current_list = []
            else:
                # 主频道名|别名1|别名2
                parts = [p.strip() for p in line.split("|")]
                primary = parts[0]
                aliases = [p for p in parts[1:] if p]
                current_list.append((primary, aliases))
        if current_genre and current_list:
            groups.append((current_genre, current_list))
    return groups


def build_alias_index(all_channels):
    """
    all_channels: {province: [(name, url), ...]}
    构建 name_lower -> url 索引；同名校重（后者覆盖），后续按优先级处理
    """
    index = {}
    for prov, ch_list in all_channels.items():
        for name, url in ch_list:
            key = name.strip().lower()
            index[key] = url
    return index


def match_channel(primary, aliases, alias_index):
    """
    按主频道名 + 别名依次匹配 alias_index，返回首个命中的 url 或 None
    """
    candidates = [primary] + aliases
    for c in candidates:
        if not c:
            continue
        key = c.strip().lower()
        if key in alias_index:
            return alias_index[key]
    return None


def merge_and_output(all_channels, demo_path, logo_map, output_dir):
    """
    all_channels: {province: [(name, url), ...]}
    按 demo.txt 的分类与顺序，用别名匹配，输出 all.txt / all.m3u
    """
    os.makedirs(output_dir, exist_ok=True)
    groups = parse_demo(demo_path)
    alias_index = build_alias_index(all_channels)

    out_txt = os.path.join(output_dir, "all.txt")
    out_m3u = os.path.join(output_dir, "all.m3u")

    txt_lines = []
    m3u_lines = ["#EXTM3U"]

    matched_any = False
    for genre, ch_list in groups:
        group_items = []  # (name, url)
        for primary, aliases in ch_list:
            url = match_channel(primary, aliases, alias_index)
            if url:
                group_items.append((primary, url))

        if not group_items:
            continue

        matched_any = True
        # txt 分类标题
        txt_lines.append(f"{genre}")
        for name, url in group_items:
            txt_lines.append(f"{name},{url}")
            logo = logo_map.get(name, "")
            if logo:
                m3u_lines.append(f'#EXTINF:-1 tvg-logo="{logo}",{name}')
            else:
                m3u_lines.append(f"#EXTINF:-1,{name}")
            m3u_lines.append(url)

    if not matched_any:
        print("  合并：demo.txt 中未匹配到任何频道，all.txt/all.m3u 为空")
    else:
        total = 0
        for _, ch_list in groups:
            for primary, aliases in ch_list:
                if match_channel(primary, aliases, alias_index):
                    total += 1
        print(f"  合并：匹配 {total} 个频道")

    with open(out_txt, 'w', encoding='utf-8') as f:
        f.write("\n".join(txt_lines) + "\n")
    with open(out_m3u, 'w', encoding='utf-8') as f:
        f.write("\n".join(m3u_lines) + "\n")

    print(f"  合并输出：{out_txt}")
    print(f"  合并输出：{out_m3u}")


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
    #     "valid": [(ip, speed), ...], "invalid": [], "kept_raw": []
    # }
    province_results = {}

    for idx, (a, b, c_str, d_str, port, has_range, province) in enumerate(groups, 1):
        if province not in province_results:
            province_results[province] = {"valid": [], "invalid": [], "kept_raw": []}
        res = province_results[province]

        original_raw = f"{a}.{b}.{c_str}.{d_str}:{port}${province}"
        original_addr = f"{a}.{b}.{c_str}.{d_str}:{port}"

        print(f"\n--- 第 {idx}/{len(groups)} 组 ({province}) ---")
        valid_ips = asyncio.run(scan_group(a, b, c_str, d_str, port, has_range))

        # ---- 测速筛选 ----
        stream_paths = CITY_STREAMS.get(province, [])
        if valid_ips:
            print(f"  检测到 {len(valid_ips)} 个有效 IP，开始测速...")
            passed = asyncio.run(filter_by_speed(valid_ips, stream_paths))
        else:
            passed = []

        if passed:
            # 取最快的一个作为该省份代表 IP（其余保留到 config）
            best_ip, best_speed = passed[0]
            res["valid"].append((best_ip, best_speed))
            # 其余有效 IP 也记入 config（去重追加）
            extra_ips = [ip for ip, _ in passed[1:]]
            if extra_ips:
                append_to_config(province, extra_ips)
            # ===== 保留策略（新规则）：有效无论有无区间，均保留在 test_ip.txt =====
            res["kept_raw"].append(original_raw)
            print(f"  本组最佳 IP: http://{best_ip}  ({best_speed:.1f} KB/s)")
            print(f"  有效配置，保留在 {os.path.basename(INPUT_FILE)}：{original_addr}")
        else:
            # 未通过测速（或无可测 IP）→ 视为无效
            res["invalid"].append(original_addr)
            if has_range:
                # 有区间：保留在 test_ip.txt，下次继续扫描
                res["kept_raw"].append(original_raw)
                print(f"  有区间配置，保留在 {os.path.basename(INPUT_FILE)}：{original_addr}")
            else:
                # 无区间 + 无效：从 test_ip.txt 删除（不加入 kept_raw）
                print(f"  无区间配置，从 {os.path.basename(INPUT_FILE)} 删除：{original_addr}")

    # ========== 汇总：写省份 config / 无效记录 / 生成频道链接 ==========
    print(f"\n{'='*30}\n  汇总保存\n{'='*30}")

    all_channels = {}  # province -> [(name, url), ...]

    for province in sorted(province_results.keys()):
        res = province_results[province]

        if res["valid"]:
            # 记录速率到 config（可选：追加 speed 信息）
            passed_ips = [ip for ip, _ in res["valid"]]
            best_ip = passed_ips[0]
            # 速率信息追加到 config（追加 # 注释行记录速率）
            config_path = os.path.join(BASE_DIR, f"{province}_config.txt")
            existing = set()
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        existing.add(line.strip().split(',')[0].strip())
            new_ips = [ip for ip in passed_ips if ip not in existing]
            if new_ips:
                with open(config_path, 'a', encoding='utf-8') as f:
                    for ip in new_ips:
                        f.write(ip + "\n")

            # ---- 生成频道链接文件（用最佳 IP）----
            print(f"\n[{province}] 生成频道链接（代表 IP: {best_ip}）")
            channels = generate_province_files(province, best_ip)
            if channels:
                all_channels[province] = channels

        if res["invalid"]:
            write_invalid_records(province, sorted(set(res["invalid"])))

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
