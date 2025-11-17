import os
import re
import requests
import subprocess
from urllib.parse import urlparse
from ipaddress import ip_address, IPv4Address, IPv6Address
import concurrent.futures
import time
import threading
from collections import OrderedDict
import json

# 配置参数
CONFIG_DIR = 'config'
SUBSCRIBE_FILE = os.path.join(CONFIG_DIR, 'subscribe.txt')
DEMO_FILE = os.path.join(CONFIG_DIR, 'demo.txt')
LOCAL_FILE = os.path.join(CONFIG_DIR, 'local.txt')
BLACKLIST_FILE = os.path.join(CONFIG_DIR, 'blacklist.txt')
RUN_COUNTER_FILE = os.path.join(CONFIG_DIR, 'run_counter.txt')

OUTPUT_DIR = 'output'
IPV4_DIR = os.path.join(OUTPUT_DIR, 'ipv4')
IPV6_DIR = os.path.join(OUTPUT_DIR, 'ipv6')
SPEED_LOG = os.path.join(OUTPUT_DIR, 'sort.log')

SPEED_TEST_DURATION = 5
MAX_WORKERS = 10
SPEED_THRESHOLD = 50  # 速度阈值，单位KB/s

# GitHub代理列表
GITHUB_PROXIES = [


    'https://ghproxy.cc/',

    'https://gh.ddlc.top/',

    'https://gh-proxy.com/'
]

# 全局变量
failed_domains = set()
log_lock = threading.Lock()
domain_lock = threading.Lock()
counter_lock = threading.Lock()
domain_cache = {}  # 域名检测缓存
available_proxy = None  # 可用的GitHub代理

os.makedirs(IPV4_DIR, exist_ok=True)
os.makedirs(IPV6_DIR, exist_ok=True)


# --------------------------
# 工具函数
# --------------------------
def write_log(message):
    """线程安全的日志写入"""
    with log_lock:
        with open(SPEED_LOG, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")


def get_domain(url):
    """提取域名和端口作为唯一标识"""
    try:
        parsed = urlparse(url)
        domain = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        return f"{domain}:{port}"
    except:
        return None


def update_blacklist(domain):
    """更新黑名单"""
    if domain:
        with domain_lock:
            failed_domains.add(domain)


def get_ip_type(url):
    """安全获取IP类型"""
    try:
        host = urlparse(url).hostname
        if not host:
            return 'ipv4'

        # 尝试解析IP地址类型
        ip = ip_address(host)
        return 'ipv6' if isinstance(ip, IPv6Address) else 'ipv4'
    except ValueError:
        return 'ipv4'
    except Exception as e:
        print(f"⚠️ IP类型检测异常: {str(e)} ← {url}")
        return 'ipv4'


def load_run_counter():
    """加载运行计数器"""
    try:
        with open(RUN_COUNTER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"run_count": 0, "last_run": None}


def save_run_counter(counter):
    """保存运行计数器"""
    with open(RUN_COUNTER_FILE, 'w', encoding='utf-8') as f:
        json.dump(counter, f, ensure_ascii=False, indent=2)


def clear_blacklist_if_needed():
    """运行10次后清空黑名单"""
    counter = load_run_counter()
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')

    # 如果是同一天的不同运行，不增加计数
    last_run_date = counter.get('last_run', '').split(' ')[0] if counter.get('last_run') else ''
    current_date = current_time.split(' ')[0]

    if last_run_date != current_date:
        counter['run_count'] = 0

    counter['run_count'] += 1
    counter['last_run'] = current_time

    if counter['run_count'] >= 10:
        print("🔄 达到10次运行，清空黑名单...")
        if os.path.exists(BLACKLIST_FILE):
            os.remove(BLACKLIST_FILE)
        counter['run_count'] = 0

    save_run_counter(counter)
    return counter['run_count']


def test_proxy(proxy_url):
    """测试GitHub代理是否可用"""
    # 使用一个简单的GitHub文件进行测试
    test_url = "https://raw.githubusercontent.com/octocat/Hello-World/master/README"
    try:
        full_url = proxy_url + test_url
        response = requests.get(full_url, timeout=10, verify=False)
        if response.status_code == 200 and "Hello World" in response.text:
            print(f"✅ 代理可用: {proxy_url}")
            return True
    except Exception as e:
        print(f"❌ 代理不可用: {proxy_url} - {str(e)}")
    return False


def get_github_proxy():
    """获取可用的GitHub代理"""
    global available_proxy

    if available_proxy:
        # 测试当前代理是否仍然可用
        if test_proxy(available_proxy):
            return available_proxy

    print("🔍 检测GitHub代理...")
    for proxy in GITHUB_PROXIES:
        if test_proxy(proxy):
            available_proxy = proxy
            return proxy

    print("⚠️ 未找到可用代理，直接访问GitHub")
    return None


def add_proxy_to_github_url(url):
    """为GitHub链接添加代理"""
    if 'raw.githubusercontent.com' in url and not url.startswith(tuple(GITHUB_PROXIES)):
        proxy = get_github_proxy()
        if proxy:
            # 直接拼接代理和原始URL
            return proxy + url
    return url


# --------------------------
# 核心逻辑
# --------------------------
def parse_demo_file():
    """解析频道模板文件"""
    print("\n🔍 解析频道模板文件...")
    alias_map = {}
    group_map = {}
    group_order = []
    channel_order = OrderedDict()
    current_group = None

    try:
        with open(DEMO_FILE, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                if line.endswith(',#genre#'):
                    current_group = line.split(',', 1)[0]
                    group_order.append(current_group)
                    channel_order[current_group] = []
                    print(f"  发现分组 [{current_group}]")
                elif current_group and line:
                    parts = [p.strip() for p in line.split('|')]
                    standard_name = parts[0]
                    channel_order[current_group].append(standard_name)

                    for alias in parts:
                        alias_map[alias] = standard_name
                    group_map[standard_name] = current_group

        print(f"✅ 发现 {len(group_order)} 个分组，{len(alias_map)} 个别名")
        return alias_map, group_map, group_order, channel_order

    except Exception as e:
        print(f"❌ 模板解析失败: {str(e)}")
        return {}, {}, [], OrderedDict()


def fetch_sources():
    """获取订阅源数据（支持GitHub代理）"""
    print("\n🔍 获取订阅源...")
    sources = []

    try:
        # 修复编码问题：尝试多种编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        urls = []

        for encoding in encodings:
            try:
                with open(SUBSCRIBE_FILE, 'r', encoding=encoding) as f:
                    urls = [line.strip() for line in f if line.strip()]
                print(f"✅ 使用 {encoding} 编码成功读取订阅文件")
                break
            except UnicodeDecodeError:
                print(f"⚠️ {encoding} 编码读取失败，尝试下一种编码")
                continue
        else:
            # 所有编码都失败，使用错误忽略模式
            with open(SUBSCRIBE_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                urls = [line.strip() for line in f if line.strip()]
            print("⚠️ 使用错误忽略模式读取订阅文件")

        print(f"  发现 {len(urls)} 个订阅地址")
        for idx, url in enumerate(urls, 1):
            try:
                # 处理GitHub链接代理
                final_url = add_proxy_to_github_url(url)
                print(f"\n🌐 正在获取源 ({idx}/{len(urls)})：{final_url}")

                response = requests.get(final_url, timeout=15)
                content = response.text

                if '#EXTM3U' in content or url.endswith('.m3u'):
                    parsed = parse_m3u(content)
                    print(f"  解析到 {len(parsed)} 个M3U源")
                    sources.extend(parsed)
                else:
                    parsed = parse_txt(content)
                    print(f"  解析到 {len(parsed)} 个TXT源")
                    sources.extend(parsed)

            except Exception as e:
                print(f"❌ 下载失败: {str(e)}")

    except FileNotFoundError:
        print("⚠️ 订阅文件不存在")

    return sources


def parse_m3u(content):
    """解析M3U格式内容"""
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
    """解析TXT格式内容"""
    channels = []
    for line in content.split('\n'):
        line = line.strip()
        if ',' in line:
            try:
                name, urls = line.split(',', 1)
                for url in urls.split('#'):
                    clean_url = url.split('$')[0].strip()
                    if clean_url:
                        channels.append({'name': name.strip(), 'url': clean_url})
            except Exception as e:
                print(f"❌ 解析失败: {str(e)} ← {line}")
    return channels


def parse_local():
    """解析本地源文件"""
    print("\n🔍 解析本地源...")
    sources = []
    try:
        # 修复编码问题
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']

        for encoding in encodings:
            try:
                with open(LOCAL_FILE, 'r', encoding=encoding) as f:
                    for line in f:
                        line = line.strip()
                        if ',' in line:
                            try:
                                name, urls = line.split(',', 1)
                                for url in urls.split('#'):
                                    parts = url.split('$', 1)
                                    source = {
                                        'name': name.strip(),
                                        'url': parts[0].strip(),
                                        'whitelist': len(parts) > 1
                                    }
                                    sources.append(source)
                            except Exception as e:
                                print(f"❌ 解析失败: {str(e)} ← {line}")
                print(f"✅ 使用 {encoding} 编码成功读取本地源")
                break
            except UnicodeDecodeError:
                continue
        else:
            # 所有编码都失败，使用错误忽略模式
            with open(LOCAL_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if ',' in line:
                        try:
                            name, urls = line.split(',', 1)
                            for url in urls.split('#'):
                                parts = url.split('$', 1)
                                source = {
                                    'name': name.strip(),
                                    'url': parts[0].strip(),
                                    'whitelist': len(parts) > 1
                                }
                                sources.append(source)
                        except Exception as e:
                            print(f"❌ 解析失败: {str(e)} ← {line}")
            print("⚠️ 使用错误忽略模式读取本地源")

        print(f"✅ 找到 {len(sources)} 个本地源")
    except FileNotFoundError:
        print("⚠️ 本地源文件不存在")
    return sources


def read_blacklist():
    """读取黑名单列表"""
    try:
        # 修复编码问题
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']

        for encoding in encodings:
            try:
                with open(BLACKLIST_FILE, 'r', encoding=encoding) as f:
                    return [line.strip() for line in f if line.strip()]
            except UnicodeDecodeError:
                continue
        # 所有编码都失败，返回空列表
        return []
    except FileNotFoundError:
        return []


def filter_sources(sources, blacklist):
    """过滤黑名单源"""
    print("\n🔍 过滤黑名单...")
    filtered = []
    blacklist_lower = [kw.lower() for kw in blacklist]

    for s in sources:
        # URL格式校验
        if not urlparse(s['url']).scheme:
            print(f"🚫 无效URL格式: {s['url']}")
            continue

        if s.get('whitelist', False):
            filtered.append(s)
            continue

        if any(kw in s['url'].lower() for kw in blacklist_lower):
            print(f"🚫 拦截黑名单: {s['url']}")
            continue

        filtered.append(s)

    print(f"✅ 保留 {len(filtered)}/{len(sources)} 个源")
    return filtered


def group_sources_by_domain(sources):
    """按域名和端口分组源"""
    domain_groups = {}
    for source in sources:
        domain = get_domain(source['url'])
        if not domain:
            continue
        if domain not in domain_groups:
            domain_groups[domain] = []
        domain_groups[domain].append(source)
    return domain_groups


def select_test_channel(sources):
    """选择测试频道（优先选择包含CCTV或卫视的频道）"""
    # 第一优先级：CCTV频道
    for source in sources:
        if 'CCTV' in source['name']:
            return source

    # 第二优先级：卫视频道
    for source in sources:
        if '卫视' in source['name']:
            return source

    # 第三优先级：其他频道
    return sources[0] if sources else None


def test_rtmp(url):
    """RTMP推流检测"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-i', url, '-t', '1', '-v', 'error', '-f', 'null', '-'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        if result.returncode == 0:
            write_log(f"RTMP检测成功: {url}")
            return 100  # RTMP成功返回100，大于阈值
        write_log(f"RTMP检测失败: {url} | {result.stderr.decode()[:100]}")
        return 0
    except Exception as e:
        write_log(f"RTMP检测异常: {url} | {str(e)}")
        return 0


def test_speed(url):
    """增强版测速函数 - 基于100KB数据测试"""
    try:
        start_time = time.time()

        # RTMP协议处理
        if url.startswith(('rtmp://', 'rtmps://')):
            return test_rtmp(url)

        # HTTP协议处理
        if not url.startswith(('http://', 'https://')):
            write_log(f"⚠️ 跳过非常规协议: {url}")
            return 0

        with requests.Session() as session:
            response = session.get(url,
                                   stream=True,
                                   timeout=(3.05, 5),
                                   allow_redirects=True,
                                   verify=False,
                                   headers={'User-Agent': 'Mozilla/5.0'})

            total_bytes = 0
            target_bytes = 100 * 1024  # 100KB
            data_start = time.time()

            for chunk in response.iter_content(chunk_size=8192):  # 使用8KB块大小
                if chunk:
                    total_bytes += len(chunk)
                    # 达到100KB立即停止
                    if total_bytes >= target_bytes:
                        break

                # 添加超时保护，避免网络问题导致长时间阻塞
                if (time.time() - data_start) > 10:  # 10秒超时
                    write_log(f"⏰ 测速超时: {url}")
                    break

            duration = max(time.time() - data_start, 0.001)

            # 如果实际读取不足100KB，按比例计算速度
            if total_bytes < target_bytes:
                write_log(f"⚠️ 仅读取 {total_bytes / 1024:.1f}KB 数据: {url}")
                # 可以返回0或按实际读取量计算
                # return 0

            speed = (total_bytes / 1024) / duration  # KB/s

            # 检查速度是否大于阈值
            if speed > SPEED_THRESHOLD:
                log_msg = (f"✅ 测速成功: {url}\n"
                           f"   速度: {speed:.2f}KB/s > {SPEED_THRESHOLD}KB/s | 数据量: {total_bytes / 1024:.1f}KB | "
                           f"总耗时: {time.time() - start_time:.2f}s")
                write_log(log_msg)
                return speed
            else:
                log_msg = (f"⚠️ 速度不足: {url}\n"
                           f"   速度: {speed:.2f}KB/s <= {SPEED_THRESHOLD}KB/s | 数据量: {total_bytes / 1024:.1f}KB | "
                           f"总耗时: {time.time() - start_time:.2f}s")
                write_log(log_msg)
                return 0  # 速度不足，返回0

    except Exception as e:
        domain = get_domain(url)
        update_blacklist(domain)
        log_msg = (f"❌ 测速失败: {url}\n"
                   f"   错误: {str(e)} | 域名: {domain}")
        write_log(log_msg)
        return 0


def process_sources_optimized(sources):
    """优化版源处理：按域名分组检测"""
    print("\n🔍 开始优化检测流程...")
    print(f"📊 速度阈值: {SPEED_THRESHOLD}KB/s")

    # 按域名分组
    domain_groups = group_sources_by_domain(sources)
    print(f"📊 将 {len(sources)} 个源按域名分组为 {len(domain_groups)} 个组")

    processed = []
    test_results = {}  # 域名检测结果缓存

    for domain_idx, (domain, group_sources) in enumerate(domain_groups.items(), 1):
        print(f"\n🔍 处理域名组 ({domain_idx}/{len(domain_groups)}): {domain}")
        print(f"   组内包含 {len(group_sources)} 个频道")

        # 如果该域名已经在缓存中且有结果，直接使用缓存结果
        if domain in domain_cache:
            speed_result = domain_cache[domain]  # 修改变量名，避免与函数名冲突
            print(f"   ✅ 使用缓存结果: 速度 {speed_result:.2f}KB/s")
        else:
            # 选择测试频道
            test_channel = select_test_channel(group_sources)
            if not test_channel:
                print(f"   ⚠️ 该组无有效测试频道，跳过")
                continue

            print(f"   🎯 选择测试频道: {test_channel['name']},{test_channel['url']}")

            # 测试该频道 - 修改变量名，避免与函数名冲突
            speed_result = test_speed(test_channel['url'])
            domain_cache[domain] = speed_result
            test_results[domain] = speed_result

            if speed_result > SPEED_THRESHOLD:
                print(f"   ✅ 域名检测通过: 速度 {speed_result:.2f}KB/s > {SPEED_THRESHOLD}KB/s")
            else:
                print(f"   ❌ 域名检测失败: 速度 {speed_result:.2f}KB/s <= {SPEED_THRESHOLD}KB/s")

        # 如果检测通过，添加该域名下所有频道
        if speed_result > SPEED_THRESHOLD:  # 使用速度阈值判断
            for source in group_sources:
                ip_type = get_ip_type(source['url'])
                processed.append((source['name'], source['url'], speed_result, ip_type))  # 使用修改变量名
            print(f"   📥 添加 {len(group_sources)} 个频道")
        else:
            print(f"   🚫 跳过 {len(group_sources)} 个频道 (速度不足)")

    # 保存黑名单更新
    if failed_domains:
        existing = set()
        if os.path.exists(BLACKLIST_FILE):
            # 修复编码问题
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            for encoding in encodings:
                try:
                    with open(BLACKLIST_FILE, 'r', encoding=encoding) as f:
                        existing = set(line.strip() for line in f)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                with open(BLACKLIST_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                    existing = set(line.strip() for line in f)

        new_domains = failed_domains - existing
        if new_domains:
            with open(BLACKLIST_FILE, 'a', encoding='utf-8') as f:
                for domain in new_domains:
                    f.write(f"{domain}\n")
            print(f"🆕 新增 {len(new_domains)} 个域名到黑名单")

    print(f"\n✅ 优化检测完成，共处理 {len(processed)} 个频道")
    return processed


def organize_channels(processed, alias_map, group_map):
    """整理频道数据"""
    print("\n📚 整理频道数据...")
    organized = {'ipv4': OrderedDict(), 'ipv6': OrderedDict()}

    for name, url, speed, ip_type in processed:
        if ip_type not in ('ipv4', 'ipv6'):
            print(f"⚠️ 异常IP类型: {ip_type}，使用ipv4代替 ← {url}")
            ip_type = 'ipv4'

        std_name = alias_map.get(name, name)
        group = group_map.get(std_name, '其他')

        if group not in organized[ip_type]:
            organized[ip_type][group] = OrderedDict()
        if std_name not in organized[ip_type][group]:
            organized[ip_type][group][std_name] = []

        organized[ip_type][group][std_name].append((url, speed))

    return organized


def finalize_output(organized, group_order, channel_order):
    """生成输出文件"""
    print("\n📂 生成结果文件...")
    for ip_type in ['ipv4', 'ipv6']:
        txt_lines = []
        m3u_lines = [
            '#EXTM3U x-tvg-url="https://gh.catmak.name/https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"',
        ]

        # 统计通过的频道数量
        total_channels = 0

        # 按模板顺序处理分组
        for group in group_order:
            if group not in organized[ip_type]:
                continue

            txt_lines.append(f"{group},#genre#")

            # 处理模板频道
            for channel in channel_order[group]:
                if channel not in organized[ip_type][group]:
                    continue

                # 按速度排序，最多取10个
                urls = sorted(organized[ip_type][group][channel], key=lambda x: x[1], reverse=True)
                selected = [u[0] for u in urls[:10]]

                if selected:
                    # TXT格式：每个链接单独一行
                    for url in selected:
                        txt_lines.append(f"{channel},{url}")

                    # M3U格式
                    for url in selected:
                        m3u_lines.append(
                            f'#EXTINF:-1 tvg-name="{channel}" tvg-logo="https://gh.catmak.name/https://raw.githubusercontent.com/fanmingming/live/main/tv/{channel}.png" group-title="{group}",{channel}')
                        m3u_lines.append(url)

                    total_channels += 1

            # 处理额外频道
            extra = sorted(
                [c for c in organized[ip_type][group] if c not in channel_order[group]],
                key=lambda x: x.lower()
            )
            for channel in extra:
                urls = sorted(organized[ip_type][group][channel], key=lambda x: x[1], reverse=True)
                selected = [u[0] for u in urls[:10]]
                if selected:
                    for url in selected:
                        txt_lines.append(f"{channel},{url}")
                    for url in selected:
                        m3u_lines.append(f'#EXTINF:-1 tvg-name="{channel}" group-title="{group}",{channel}')
                        m3u_lines.append(url)

                    total_channels += 1

        # 处理其他分组
        if '其他' in organized[ip_type]:
            txt_lines.append("其他,#genre#")
            for channel in sorted(organized[ip_type]['其他'].keys(), key=lambda x: x.lower()):
                urls = sorted(organized[ip_type]['其他'][channel], key=lambda x: x[1], reverse=True)
                selected = [u[0] for u in urls[:10]]
                if selected:
                    for url in selected:
                        txt_lines.append(f"{channel},{url}")
                    for url in selected:
                        m3u_lines.append(f'#EXTINF:-1 tvg-name="{channel}" group-title="其他",{channel}')
                        m3u_lines.append(url)

                    total_channels += 1

        # 写入文件
        dir_path = IPV4_DIR if ip_type == 'ipv4' else IPV6_DIR
        with open(os.path.join(dir_path, 'result.txt'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(txt_lines))
        with open(os.path.join(dir_path, 'result.m3u'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(m3u_lines))

        print(f"  已生成 {ip_type.upper()} 文件 → {dir_path}")
        print(f"  通过速度阈值的频道数量: {total_channels}")


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("🎬 IPTV直播源处理脚本（优化版）")
    print("=" * 50)
    print(f"⚡ 速度阈值: {SPEED_THRESHOLD}KB/s")

    # 初始化运行计数器和黑名单
    run_count = clear_blacklist_if_needed()
    print(f"📊 当前运行次数: {run_count}")

    # 初始化日志文件
    with open(SPEED_LOG, 'w', encoding='utf-8') as f:
        f.write(f"测速日志 {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"速度阈值: {SPEED_THRESHOLD}KB/s\n")

    # 初始化数据
    alias_map, group_map, group_order, channel_order = parse_demo_file()
    sources = fetch_sources() + parse_local()
    blacklist = read_blacklist()

    # 处理流程
    filtered = filter_sources(sources, blacklist)
    processed = process_sources_optimized(filtered)
    organized = organize_channels(processed, alias_map, group_map)
    finalize_output(organized, group_order, channel_order)

    print("\n" + "=" * 50)
    print("🎉 处理完成！结果文件已保存至 output 目录")
    print("=" * 50)
