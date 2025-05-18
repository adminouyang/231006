# -*- coding: utf-8 -*-
import sys
import ctypes
import json
import requests
from urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urlparse, quote

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Windows系统设置控制台编码为UTF-8
if sys.platform == "win32":
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleOutputCP(65001)
    kernel32.SetConsoleCP(65001)

import os
import re
import subprocess
from ipaddress import ip_address, IPv4Address, IPv6Address
import concurrent.futures
import time
import threading
from collections import OrderedDict, defaultdict
from functools import lru_cache

# 配置参数
CONFIG_DIR = 'py/TV/config'
SUBSCRIBE_FILE = os.path.join(CONFIG_DIR, 'subscribe.txt')
DEMO_FILE = os.path.join(CONFIG_DIR, 'demo.txt')
LOCAL_FILE = os.path.join(CONFIG_DIR, 'local.txt')
BLACKLIST_FILE = os.path.join(CONFIG_DIR, 'blacklist.txt')
RESOLUTION_BLACKLIST = os.path.join(CONFIG_DIR, 'resolution_blacklist.txt')

PROXY_PREFIXES = {
    'https': 'https://ghproxy.cc/',
    'https': 'https://gh-proxy.com/'
}

OUTPUT_DIR = 'py/TV/output'
IPV4_DIR = os.path.join(OUTPUT_DIR, 'ipv4')
IPV6_DIR = os.path.join(OUTPUT_DIR, 'ipv6')
SPEED_LOG = os.path.join(OUTPUT_DIR, 'sort.log')
SD_SOURCES_FILE = "标清源.txt"

SPEED_TEST_DURATION = 5
MAX_WORKERS = 4
MIN_RESOLUTION = 720
SPEED_THRESHOLD_1080P = 400  # 1080p速度阈值
TEST_DURATION = 4.5       # 延长测试时长至4.5秒

os.makedirs(IPV4_DIR, exist_ok=True)
os.makedirs(IPV6_DIR, exist_ok=True)

# 全局变量
success_domains = set()
failed_domains = set()
subscribe_domains = set()
low_res_sources = defaultdict(lambda: defaultdict(list))
log_lock = threading.Lock()
domain_lock = threading.Lock()
counter_lock = threading.Lock()

print_lock = threading.Lock()

def write_log(message):
    # 保持原有日志记录逻辑不变
    with log_lock:
        with open(SPEED_LOG, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
def safe_url(url):
    parsed = urlparse(url)
    encoded_path = quote(parsed.path)
    return parsed._replace(path=encoded_path).geturl()

@lru_cache(maxsize=1000)
def get_domain(url):
    try:
        if not urlparse(url).scheme:
            url = 'http://' + url
        parsed = urlparse(url)
        netloc = parsed.netloc.split(':')[0]
        return netloc if '.' in netloc else None
    except:
        return None

def update_blacklist(domain, from_subscribe=False):
    if domain and not from_subscribe:
        with domain_lock:
            failed_domains.add(domain)
            write_log(f"记录失败域名: {domain}")

def update_resolution_blacklist(domain, from_subscribe=False):
    if domain and not from_subscribe:
        try:
            with open(RESOLUTION_BLACKLIST, 'a+', encoding='utf-8') as f:
                f.seek(0)
                existing = set(line.strip() for line in f)
                if domain not in existing:
                    f.write(f"{domain}\n")
                    write_log(f"新增分辨率黑名单: {domain}")
        except Exception as e:
            write_log(f"更新分辨率黑名单失败: {str(e)}")

def get_ip_type(url):
    try:
        host = urlparse(url).hostname
        ip = ip_address(host)
        return 'ipv6' if isinstance(ip, IPv6Address) else 'ipv4'
    except:
        return 'ipv4'

def parse_m3u(content):
    channels = []
    current = {}
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('#EXTINF'):
            match = re.search(r'tvg-name="([^"]*)"', line)
            current = {'name': match.group(1) if match else '未知频道', 'urls': []}
        elif line and not line.startswith('#'):
            if current:
                current['urls'].append(line)
                channels.append(current)
                current = {}
    return [{'name': c['name'], 'url': u} for c in channels for u in c['urls']]

def parse_txt(content):
    channels = []
    for line in content.split('\n'):
        line = line.strip()
        if ',' in line:
            try:
                name_part, url_part = line.split(',', 1)
                name = name_part.strip()
                for url in url_part.split('#'):
                    clean_url = url.split('$')[0].strip()
                    if clean_url:
                        channels.append({'name': name, 'url': clean_url})
            except Exception as e:
                write_log(f"TXT解析失败: {line} | {str(e)}")
    return channels

# 新增带锁的彩色打印函数
def safe_print(color, prefix, message):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'end': '\033[0m'
    }
    with print_lock:
        print(f"{colors[color]}[{prefix}]{colors['end']} {message}")

def get_resolution(url):
    safe_print('blue', '分辨率检测', f"开始检测: {url}")
    for attempt in range(2):
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=height',
                '-of', 'json',
                '-timeout', '10000000',
                '-user_agent', 'Mozilla/5.0',
                '-i', url
            ]

            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
                startupinfo=startupinfo
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get('streams'):
                    height = int(data['streams'][0].get('height', 0))
                    # 添加分辨率结果输出
                    safe_print('blue', '分辨率结果',
                               f"{url[:30]:<30} => {height}p (尝试次数: {attempt + 1})")
                    return height
            time.sleep(1)
        except Exception as e:
            write_log(f"分辨率检测异常: {url} | {str(e)}")
        # 添加检测失败提示
        safe_print('red', '分辨率失败', f"无法获取分辨率: {url}")
        return 0

def parse_demo_file():
    print("\n解析频道模板...")
    alias_map = {}
    group_map = {}
    group_order = []
    channel_order = OrderedDict()
    current_group = None

    try:
        with open(DEMO_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.endswith(',#genre#'):
                    current_group = line.split(',', 1)[0]
                    group_order.append(current_group)
                    channel_order[current_group] = []
                elif current_group and line:
                    parts = [p.strip() for p in line.split('|')]
                    standard_name = parts[0]
                    channel_order[current_group].append(standard_name)
                    for alias in parts:
                        alias_map[alias] = standard_name
                    group_map[standard_name] = current_group

        if '其他' not in group_order:
            group_order.append('其他')
            channel_order['其他'] = []

        print(f"加载 {len(group_order)} 个分组，{len(alias_map)} 个别名")
        return alias_map, group_map, group_order, channel_order

    except Exception as e:
        print(f"模板解析失败: {str(e)}")
        return {}, {}, [], OrderedDict()

def process_local_sources(local_sources, alias_map):
    print("\n处理本地源...")
    processed = []
    for source in local_sources:
        name = source['name']
        url = source['url']
        domain = get_domain(url)
        from_subscribe = domain in subscribe_domains
        height = get_resolution(url)

        if height >= MIN_RESOLUTION:
            ip_type = get_ip_type(url)
            processed.append((name, url, 9999.99, ip_type, True))
            print(f"[本地] 有效: {name[:15]:<15} | 分辨率: {height}p")
        else:
            ip_type = get_ip_type(url)
            std_name = alias_map.get(name, name)
            if height > 0:
                with domain_lock:
                    low_res_sources[ip_type][std_name].append((url, 9999.99))
            else:
                update_resolution_blacklist(domain, from_subscribe)
            print(f"[本地] 无效: {name[:15]:<15} | 分辨率: {height}p")
    return processed

def test_speed(url):
    try:
        safe_print('yellow', '测速开始', f"测试: {url}")
        
        # 精确计时工具
        start_timer = time.perf_counter()
        total_bytes = 0
        established_time = None
        chunk_size = 8192  # 增大数据块减少循环次数
        
        with requests.get(url, stream=True, 
                         timeout=(3.05, 6.05),  # 连接/读取超时分离
                         headers={'Connection': 'close'}) as response:
            response.raise_for_status()
            
            # 数据流分析策略
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not established_time:  # 首个数据包到达开始计时
                    established_time = time.perf_counter()
                    safe_print('blue', '连接建立', f"开始接收: {url}")
                
                total_bytes += len(chunk)
                
                # 动态结束检测：有效传输需满足最低时长
                elapsed = time.perf_counter() - established_time
                if elapsed >= max(TEST_DURATION, 2.5):  # 保证最低2.5秒有效数据
                    break

        # 有效性校验
        if not established_time:
            safe_print('red', '无数据', f"{url} 未接收到任何数据")
            return 0
            
        # 精确时间计算（毫秒级）
        duration = max(time.perf_counter() - established_time, 0.001)
        
        # 数据补偿机制（针对快速传输场景）
        if duration < 0.5 and total_bytes > 51200:  # 50KB内短时爆发
            duration = 0.5  # 最低按500ms计算
        
        # 带宽计算优化
        speed_kb = (total_bytes / duration) / 1024  # 精确浮点运算
        speed_mb = speed_kb / 1024
        
        # 智能单位切换
        if speed_mb >= 0.5:
            display_speed = f"{speed_mb:.2f}MB/s"
        else:
            display_speed = f"{speed_kb:.2f}KB/s"

        # 详细数据输出
        safe_print('green', '测速成功', 
                 f"{url} {display_speed.ljust(10)} "
                 f"[数据量: {total_bytes/1024:.1f}KB 时间: {duration:.2f}s]")
        
        return speed_kb  # 保持KB/s单位用于阈值判断

    except requests.Timeout:
        safe_print('red', '超时终止', f"{url} 超过6秒无响应")
        return 0
    except Exception as e:
        safe_print('red', '测速异常', f"{url} {str(e)[:50]}")
        write_log(f"测速异常: {url} | {type(e).__name__} - {str(e)}")
        return 0

def _speed_test(sources, alias_map):
    total = len(sources)
    print(f"\n开始测速 {total} 个源...")
    processed = []
    processed_count = 0  # 新增处理计数器

    def process_source(source):
        nonlocal processed_count
        name = source['name']
        url = source['url']
        domain = get_domain(url)
        from_subscribe = domain in subscribe_domains

        # 新增频道处理提示
        safe_print('blue', '处理频道',
                   f"{name[:15]:<15} ({url}) 开始检测...")

        speed = 0
        height = 0
        ip_type = 'ipv4'

        try:
            ip_type = get_ip_type(url)
            speed = test_speed(url)
            if speed > 0:
                height = get_resolution(url)
            else:
                update_blacklist(domain, from_subscribe)
                # 新增速度不合格提示
                safe_print('red', '速度淘汰',
                           f"{url}速度不合格: {speed:.2f}KB/s")
        except Exception as e:
            write_log(f"处理异常: {url} | {str(e)}")

        # 处理结果判断逻辑
        result_msg = ""
        if speed > 0 and height >= MIN_RESOLUTION:
            if height >= 1080 and speed < SPEED_THRESHOLD_1080P:
                result_msg = (f"1080p源速度不足: {speed:.2f}KB/s < {SPEED_THRESHOLD_1080P}KB/s")
                safe_print('yellow', '速度淘汰', f"{url} {result_msg}")
            else:
                if domain:
                    with domain_lock:
                        success_domains.add(domain)
                result_msg = (f"✓ 合格 | 速度: {speed:.2f}KB/s | 分辨率: {height}p")
                safe_print('green', '通过检测',
                           f"{name[:15]:<15} ({url}) {result_msg}")
                return (name, url, speed, ip_type, False)
        else:
            if speed > 0 and 0 < height < MIN_RESOLUTION:
                result_msg = (f"分辨率不足: {height}p < {MIN_RESOLUTION}p")
                safe_print('yellow', '分辨率淘汰',
                           f"{name[:15]:<15} ({url}) {result_msg}")
                std_name = alias_map.get(name, name)
                with domain_lock:
                    low_res_sources[ip_type][std_name].append((url, speed))
            else:
                result_msg = "基本检测失败"
                safe_print('red', '完全淘汰',
                           f"{name[:15]:<15} ({url}) {result_msg}")
            update_blacklist(domain, from_subscribe)
            if height <= 0:
                update_resolution_blacklist(domain, from_subscribe)

        # 更新进度计数器
        with counter_lock:
            processed_count += 1
            remaining = total - processed_count
            sys.stdout.write(f"\r已完成: {processed_count}/{total} 剩余: {remaining}")
            sys.stdout.flush()

        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_source, s) for s in sources}

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                processed.append(result)

    print("\n测速完成")
    return processed

def save_sd_sources(group_order, channel_order, alias_map):
    print("\n生成标清源文件...")
    for ip_type in ['ipv4', 'ipv6']:
        output_lines = []
        dir_path = IPV4_DIR if ip_type == 'ipv4' else IPV6_DIR
        output_file = os.path.join(dir_path, SD_SOURCES_FILE)

        categorized = defaultdict(list)
        uncategorized = []

        for group in group_order:
            for channel in channel_order[group]:
                std_name = alias_map.get(channel, channel)
                if std_name in low_res_sources[ip_type]:
                    urls = sorted(
                        low_res_sources[ip_type][std_name],
                        key=lambda x: x[1],
                        reverse=True
                    )[:10]
                    if urls:
                        categorized[group].append((channel, urls))

        all_channels = set(low_res_sources[ip_type].keys())
        categorized_channels = set()
        for group in group_order:
            for channel in channel_order[group]:
                categorized_channels.add(alias_map.get(channel, channel))
        uncategorized_channels = all_channels - categorized_channels

        for group in group_order:
            if group not in categorized:
                continue
            output_lines.append(f"{group},#genre#\n")
            for channel, urls in categorized[group]:
                for url, speed in urls:
                    output_lines.append(f"{channel},{url},{speed:.2f}KB/s")

        if uncategorized_channels:
            output_lines.append("\n# 未分类频道")
            for channel in sorted(uncategorized_channels, key=lambda x: x.lower()):
                urls = sorted(
                    low_res_sources[ip_type][channel],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
                for url, speed in urls:
                    output_lines.append(f"{channel},{url},{speed:.2f}KB/s")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(output_lines))
        print(f"保存 {len(output_lines)} 行到 {output_file}")

def finalize_output(organized, group_order, channel_order):
    print("\n生成输出文件...")
    for ip_type in ['ipv4', 'ipv6']:
        txt_lines = []
        m3u_lines = [
            '#EXTM3U x-tvg-url="https://gh.catmak.name/https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"', ]

        for group in group_order:
            if group not in organized[ip_type]:
                continue

            txt_lines.append(f"\n{group},#genre#")
            m3u_lines.append(f'\n#EXTINF:-1 group-title="{group}",{group}')

            for channel in channel_order[group]:
                if channel in organized[ip_type][group]:
                    sources = organized[ip_type][group][channel]
                    for url in [u[0] for u in sources['local'] + sources['remote']]:
                        txt_lines.append(f"{channel},{url}")
                        m3u_lines.append(f'#EXTINF:-1 tvg-name="{channel}",{channel}')
                        m3u_lines.append(url)

            extra = sorted(
                [c for c in organized[ip_type][group] if c not in channel_order[group]],
                key=lambda x: x.lower()
            )
            for channel in extra:
                sources = organized[ip_type][group][channel]
                for url in [u[0] for u in sources['local'] + sources['remote']]:
                    txt_lines.append(f"{channel},{url}")
                    m3u_lines.append(f'#EXTINF:-1 tvg-name="{channel}", tvg-logo="https://gh.catmak.name/https://raw.githubusercontent.com/fanmingming/live/main/tv/{channel}.png", {channel}')
                    m3u_lines.append(url)

        other_group = '其他'
        if other_group in organized[ip_type]:
            txt_lines.append(f"\n{other_group},#genre#")
            m3u_lines.append(f'\n#EXTINF:-1 group-title="{other_group}",{other_group}')
            for channel in organized[ip_type][other_group]:
                sources = organized[ip_type][other_group][channel]
                for url in [u[0] for u in sources['local'] + sources['remote']]:
                    txt_lines.append(f"{channel},{url}")
                    m3u_lines.append(f'#EXTINF:-1 tvg-name="{channel}",tvg-logo="https://gh.catmak.name/https://raw.githubusercontent.com/fanmingming/live/main/tv/{channel}.png", {channel}')
                    m3u_lines.append(url)

        dir_path = IPV4_DIR if ip_type == 'ipv4' else IPV6_DIR
        with open(os.path.join(dir_path, 'result.txt'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(txt_lines))
        with open(os.path.join(dir_path, 'result.m3u'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(m3u_lines))
        print(f"{ip_type.upper()} 输出文件已生成")

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print(" IPTV直播源处理脚本 v4.3 ")
    print("=" * 50)

    if os.path.exists(SUBSCRIBE_FILE):
        with open(SUBSCRIBE_FILE, 'r', encoding='utf-8') as f:
            subscribe_urls = [line.strip() for line in f if line.strip()]
            subscribe_domains = {get_domain(url) for url in subscribe_urls}
            subscribe_domains.discard(None)

    alias_map, group_map, group_order, channel_order = parse_demo_file()

    local_sources = []
    if os.path.exists(LOCAL_FILE):
        with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
            local_sources = [{
                'name': line.split(',')[0].strip(),
                'url': line.split(',')[1].split('$')[0].strip(),
                'is_local': True
            } for line in f if line.strip()]

    local_processed = process_local_sources(local_sources, alias_map)

    remote_sources = []
    if os.path.exists(SUBSCRIBE_FILE):
        with open(SUBSCRIBE_FILE, 'r', encoding='utf-8') as f:
            origin_urls = [line.strip() for line in f if line.strip()]

        for origin_url in origin_urls:
            success = False
            last_exception = None
            safe_origin_url = safe_url(origin_url)

            try:
                response = requests.get(safe_origin_url, timeout=15, verify=False)
                if response.status_code == 200:
                    content = response.text
                    if '#EXTM3U' in content:
                        remote_sources.extend(parse_m3u(content))
                    else:
                        remote_sources.extend(parse_txt(content))
                    print(f"直连成功: {origin_url}")
                    success = True
            except Exception as e:
                last_exception = e

            if not success:
                for proxy_prefix in PROXY_PREFIXES:
                    try:
                        proxied_url = safe_url(proxy_prefix + origin_url)
                        response = requests.get(proxied_url, timeout=15, verify=False)
                        if response.status_code == 200:
                            content = response.text
                            if '#EXTM3U' in content:
                                remote_sources.extend(parse_m3u(content))
                            else:
                                remote_sources.extend(parse_txt(content))
                            print(f"代理成功: {origin_url} 使用 {proxy_prefix}")
                            success = True
                            break
                    except Exception as e:
                        last_exception = e
                        continue

            if not success:
                print(f"获取失败: {origin_url}")
    # 添加初始化完成提示
    safe_print('green', '初始化完成',
             f"加载本地源: {len(local_sources)} 个 | 订阅源: {len(remote_sources)} 个")
    blacklist = []
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
            blacklist = [line.strip().lower() for line in f if line.strip()]

    filtered_remote = []
    for s in remote_sources:
        url_lower = s['url'].lower()
        if not any(kw in url_lower for kw in blacklist):
            filtered_remote.append(s)

    remote_processed = _speed_test(filtered_remote, alias_map)

    organized = {'ipv4': OrderedDict(), 'ipv6': OrderedDict()}
    all_processed = local_processed + remote_processed

    for item in all_processed:
        name, url, speed, ip_type, is_local = item
        std_name = alias_map.get(name, name)
        group = group_map.get(std_name, '其他')

        if group not in organized[ip_type]:
            organized[ip_type][group] = OrderedDict()
        if std_name not in organized[ip_type][group]:
            organized[ip_type][group][std_name] = {'local': [], 'remote': []}

        target = 'local' if is_local else 'remote'
        organized[ip_type][group][std_name][target].append((url, speed))

    finalize_output(organized, group_order, channel_order)
    save_sd_sources(group_order, channel_order, alias_map)

    final_failed = failed_domains - success_domains
    if final_failed:
        existing = set()
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
                existing = set(line.strip() for line in f if line.strip())
        new_domains = [d for d in final_failed if d not in existing and d not in subscribe_domains]
        if new_domains:
            with open(BLACKLIST_FILE, 'a', encoding='utf-8') as f:
                f.write("\n".join(new_domains) + "\n")
            print(f"\n新增 {len(new_domains)} 个域名到黑名单")

    print("\n" + "=" * 50)
    print(" 处理完成！结果文件已保存至 output 目录 ")
    print("=" * 50)
