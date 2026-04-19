import os
import re
import requests
import subprocess
from urllib.parse import urlparse, urlunparse
from ipaddress import ip_address, IPv4Address, IPv6Address
import concurrent.futures
import time
import threading
from collections import OrderedDict
import ssl
import socket
import hashlib

# 配置参数
CONFIG_DIR = 'py/优质源/config'
SUBSCRIBE_FILE = os.path.join(CONFIG_DIR, 'subscribe.txt')
DEMO_FILE = os.path.join(CONFIG_DIR, 'demo.txt')
LOCAL_FILE = os.path.join(CONFIG_DIR, 'local.txt')
BLACKLIST_FILE = os.path.join(CONFIG_DIR, 'blacklist.txt')
RUN_COUNT_FILE = os.path.join(CONFIG_DIR, 'run_count.txt')  # 新增运行次数记录文件

OUTPUT_DIR = 'py/优质源/output'
IPV4_DIR = os.path.join(OUTPUT_DIR, 'ipv4')
IPV6_DIR = os.path.join(OUTPUT_DIR, 'ipv6')
SPEED_LOG = os.path.join(OUTPUT_DIR, 'sort.log')

SPEED_TEST_DURATION = 5
MAX_WORKERS = 10
HTTPS_VERIFY = False
SPEED_THRESHOLD = 150  # 新增速度阈值120KB/s[6](@ref)
RESET_COUNT = 12       # 新增运行12次后重置黑名单[7](@ref)

# 全局变量
failed_domains = set()
log_lock = threading.Lock()
domain_lock = threading.Lock()
counter_lock = threading.Lock()
url_cache_lock = threading.Lock()
url_cache = set()  # 全局URL缓存用于去重

os.makedirs(IPV4_DIR, exist_ok=True)
os.makedirs(IPV6_DIR, exist_ok=True)


# --------------------------
# 新增运行次数管理函数
# --------------------------
def manage_run_count():
    """管理运行次数并在第12次时清空黑名单[7](@ref)"""
    try:
        # 读取当前运行次数
        if os.path.exists(RUN_COUNT_FILE):
            with open(RUN_COUNT_FILE, 'r') as f:
                current_count = int(f.read().strip())
        else:
            current_count = 0
        
        # 增加运行次数
        current_count += 1
        print(f"🔢 当前是第 {current_count} 次运行")
        
        # 检查是否需要清空黑名单[8](@ref)
        if current_count >= RESET_COUNT:
            print("🔄 达到12次运行，清空黑名单文件")
            if os.path.exists(BLACKLIST_FILE):
                with open(BLACKLIST_FILE, 'w') as f:
                    f.write('')  # 清空文件内容
                print("✅ 黑名单文件已清空")
            current_count = 0  # 重置计数器
        
        # 保存更新后的运行次数
        with open(RUN_COUNT_FILE, 'w') as f:
            f.write(str(current_count))
        
        return current_count
        
    except Exception as e:
        print(f"❌ 运行次数管理错误: {str(e)}")
        return 1


# --------------------------
# 工具函数
# --------------------------
def write_log(message):
    """线程安全的日志写入"""
    with log_lock:
        with open(SPEED_LOG, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")


def get_domain(url):
    """提取域名"""
    try:
        netloc = urlparse(url).netloc
        return netloc.split(':')[0] if ':' in netloc else netloc
    except:
        return None


def normalize_url(url):
    """标准化URL，去除多余参数，用于去重比较"""
    try:
        parsed = urlparse(url)
        # 保留基本部分：协议、域名、端口、路径
        # 去掉查询参数和片段
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip('/') if parsed.path else '/',
            '',  # params
            '',  # query
            ''   # fragment
        ))
        return normalized
    except:
        return url


def get_url_hash(url):
    """获取URL的哈希值，用于快速比较"""
    normalized = normalize_url(url)
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()


def is_duplicate_url(url):
    """检查URL是否重复"""
    url_hash = get_url_hash(url)
    with url_cache_lock:
        if url_hash in url_cache:
            return True
        url_cache.add(url_hash)
        return False


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


def get_protocol(url):
    """获取URL的协议类型"""
    try:
        return urlparse(url).scheme.lower()
    except:
        return 'unknown'


def test_https_certificate(domain, port=443):
    """测试HTTPS证书有效性"""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                # 检查证书有效期
                not_after = cert.get('notAfter', '')
                if not_after:
                    # 简单验证证书是否在有效期内
                    return True, "证书有效"
                return True, "证书信息获取成功"
    except ssl.SSLError as e:
        return False, f"SSL错误: {str(e)}"
    except Exception as e:
        return False, f"证书检查失败: {str(e)}"
    return False, "未知错误"


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
    """获取订阅源数据"""
    print("\n🔍 获取订阅源...")
    sources = []

    try:
        with open(SUBSCRIBE_FILE, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"  发现 {len(urls)} 个订阅地址")
        for idx, url in enumerate(urls, 1):
            try:
                print(f"\n🌐 正在获取源 ({idx}/{len(urls)})：{url}")
                response = requests.get(url, timeout=15, verify=HTTPS_VERIFY)
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
    current = None
    
    for line in content.splitlines():
        line = line.strip()
        
        if not line:  # 跳过空行
            continue
            
        if line.startswith('#EXTINF:'):
            # 解析EXTINF行
            name_match = re.search(r'tvg-name="([^"]*)"', line)
            name = name_match.group(1) if name_match else '未知频道'
            
            # 可以提取更多属性
            logo_match = re.search(r'tvg-logo="([^"]*)"', line)
            group_match = re.search(r'group-title="([^"]*)"', line)
            
            # 从逗号后提取显示名称（如果有）
            display_name = line.split(',')[-1] if ',' in line else name
            
            current = {
                'name': name,
                'display_name': display_name,
                'logo': logo_match.group(1) if logo_match else '',
                'group': group_match.group(1) if group_match else '',
                'urls': []
            }
            
        elif line and not line.startswith('#'):
            # URL行
            if current is not None:
                current['urls'].append(line)
                # 如果有多个URL，不立即添加，等下一个EXTINF行或文件结束
            else:
                # 没有EXTINF信息的URL，跳过或处理为匿名频道
                pass
                
        elif line.startswith('#EXTM3U'):
            # 文件头，可以处理版本信息等
            continue
            
        elif line.startswith('#EXTGRP:'):
            # 处理分组信息
            if current is not None:
                current['group'] = line.split(':', 1)[1]
                
    # 处理最后一个频道
    if current is not None and current['urls']:
        channels.append(current)
        
    # 展开多个URL
    result = []
    for channel in channels:
        for url in channel['urls']:
            result.append({
                'name': channel['name'],
                'display_name': channel.get('display_name', channel['name']),
                'logo': channel.get('logo', ''),
                'group': channel.get('group', ''),
                'url': url
            })
    
    return result


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
        with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
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
        print(f"✅ 找到 {len(sources)} 个本地源")
    except FileNotFoundError:
        print("⚠️ 本地源文件不存在")
    return sources


def read_blacklist():
    """读取黑名单列表"""
    try:
        with open(BLACKLIST_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip()]
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
            return 100
        write_log(f"RTMP检测失败: {url} | {result.stderr.decode()[:100]}")
        return 0
    except Exception as e:
        write_log(f"RTMP检测异常: {url} | {str(e)}")
        return 0


def test_https_specific(url, domain):
    """HTTPS协议特殊检测"""
    try:
        # 测试证书有效性
        cert_valid, cert_msg = test_https_certificate(domain)
        
        # 进行常规速度测试
        start_time = time.time()
        with requests.Session() as session:
            response = session.get(url,
                                   stream=True,
                                   timeout=(3.05, 5),
                                   allow_redirects=True,
                                   verify=HTTPS_VERIFY,
                                   headers={'User-Agent': 'Mozilla/5.0'})

            total_bytes = 0
            data_start = time.time()
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    total_bytes += len(chunk)
                if (time.time() - data_start) >= SPEED_TEST_DURATION:
                    break

            duration = max(time.time() - data_start, 0.001)
            speed = (total_bytes / 1024) / duration
            
            # 记录HTTPS特定信息
            https_info = f" | 证书: {'有效' if cert_valid else '无效'}"
            log_msg = (f"✅ HTTPS测速成功: {url}\n"
                       f"   速度: {speed:.2f}KB/s | 数据量: {total_bytes / 1024:.1f}KB | "
                       f"总耗时: {time.time() - start_time:.2f}s{https_info}")
            write_log(log_msg)
            return speed
            
    except requests.exceptions.SSLError as e:
        log_msg = f"❌ HTTPS SSL错误: {url} | 错误: {str(e)}"
        write_log(log_msg)
        return 0
    except Exception as e:
        domain = get_domain(url)
        update_blacklist(domain)
        log_msg = f"❌ HTTPS测速失败: {url} | 错误: {str(e)}"
        write_log(log_msg)
        return 0


def test_speed(url):
    """增强版测速函数，支持HTTPS检测"""
    try:
        protocol = get_protocol(url)
        
        # RTMP协议处理
        if protocol in ['rtmp', 'rtmps']:
            return test_rtmp(url)

        # HTTPS协议特殊处理
        if protocol == 'https':
            domain = get_domain(url)
            if domain:
                return test_https_specific(url, domain)
            else:
                write_log(f"⚠️ 无法提取HTTPS域名: {url}")
                return 0

        # HTTP协议处理
        if protocol not in ['http', 'https']:
            write_log(f"⚠️ 跳过非常规协议: {url}")
            return 0

        # 普通HTTP请求
        start_time = time.time()
        with requests.Session() as session:
            response = session.get(url,
                                   stream=True,
                                   timeout=(3.05, 5),
                                   allow_redirects=True,
                                   verify=False,
                                   headers={'User-Agent': 'Mozilla/5.0'})

            total_bytes = 0
            data_start = time.time()
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    total_bytes += len(chunk)
                if (time.time() - data_start) >= SPEED_TEST_DURATION:
                    break

            duration = max(time.time() - data_start, 0.001)
            speed = (total_bytes / 1024) / duration
            
            # 新增速度阈值检查[6](@ref)
            if speed > SPEED_THRESHOLD:
                status = "✅ 通过阈值"
            else:
                status = "🚫 未达阈值"
                
            log_msg = (f"{status} {protocol.upper()}测速: {url}\n"
                       f"   速度: {speed:.2f}KB/s | 数据量: {total_bytes / 1024:.1f}KB | "
                       f"总耗时: {time.time() - start_time:.2f}s | 阈值: {SPEED_THRESHOLD}KB/s")
            write_log(log_msg)
            return speed

    except Exception as e:
        domain = get_domain(url)
        update_blacklist(domain)
        protocol = get_protocol(url)
        log_msg = (f"❌ {protocol.upper()}测速失败: {url}\n"
                   f"   错误: {str(e)} | 域名: {domain}")
        write_log(log_msg)
        return 0


def process_sources(sources):
    """处理所有源并进行测速，应用速度阈值过滤[6](@ref)"""
    total = len(sources)
    print(f"\n🔍 开始检测 {total} 个源")
    print(f"📊 速度阈值: {SPEED_THRESHOLD}KB/s")
    
    processed = []
    processed_count = 0
    passed_count = 0  # 通过阈值计数
    duplicate_count = 0  # 重复URL计数

    # 统计协议类型
    protocol_stats = {}
    seen_urls = set()  # 用于去重的URL集合

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for s in sources:
            # 在提交任务前检查URL是否重复
            url_hash = get_url_hash(s['url'])
            if url_hash in seen_urls:
                duplicate_count += 1
                print(f"⏭️  跳过重复URL: {s['name']} | {s['url'][:50]}...")
                continue
            seen_urls.add(url_hash)
            
            future = executor.submit(
                lambda s: (s['name'], s['url'], test_speed(s['url']), 
                          get_ip_type(s['url']), get_protocol(s['url'])), s)
            futures[future] = s

        for future in concurrent.futures.as_completed(futures):
            try:
                name, url, speed, ip_type, protocol = future.result()
                with counter_lock:
                    processed_count += 1
                    progress = f"[{processed_count}/{total}]"

                    # 更新协议统计
                    if protocol not in protocol_stats:
                        protocol_stats[protocol] = {'total': 0, 'passed': 0}
                    protocol_stats[protocol]['total'] += 1

                speed_str = f"{speed:>7.2f}KB/s".rjust(12)
                protocol_icon = "🔒" if protocol == "https" else "🌐"
                if protocol in ['rtmp', 'rtmps']:
                    protocol_icon = "📹"
                
                # 应用速度阈值过滤[6](@ref)
                if speed > SPEED_THRESHOLD:
                    status = "✅"
                    passed_count += 1
                    protocol_stats[protocol]['passed'] += 1
                    
                    # 再次检查URL重复（多线程环境下）
                    if not is_duplicate_url(url):
                        processed.append((name, url, speed, ip_type, protocol))
                    else:
                        print(f"🔁 检测到重复URL（已跳过）: {name} | {url[:50]}...")
                        passed_count -= 1
                else:
                    status = "❌"
                
                print(f"{progress} {status} 频道: {name[:15]:<15} | 速度:{speed_str} | {protocol_icon}{protocol.upper()} | {url}")
                
            except Exception as e:
                print(f"⚠️ 处理异常: {str(e)}")

    # 打印统计信息
    print(f"\n📊 速度阈值过滤结果:")
    print(f"   📡 总检测数: {processed_count}")
    print(f"   🔁 跳过重复: {duplicate_count}")
    print(f"   ✅ 通过数: {passed_count} (速度 > {SPEED_THRESHOLD}KB/s)")
    print(f"   ❌ 淘汰数: {processed_count - passed_count} (速度 ≤ {SPEED_THRESHOLD}KB/s)")
    print(f"   📈 通过率: {passed_count/max(processed_count,1)*100:.1f}%")
    
    print(f"📊 协议分布:")
    for protocol, data in protocol_stats.items():
        icon = "🔒" if protocol == "https" else ("📹" if protocol in ['rtmp', 'rtmps'] else "🌐")
        passed = data['passed']
        total = data['total']
        pass_rate = passed/max(total,1)*100
        print(f"   {icon} {protocol.upper():<6}: {passed}/{total} 通过 ({pass_rate:.1f}%)")

    # 保存黑名单更新
    if failed_domains:
        existing = set()
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r') as f:
                existing = set(line.strip() for line in f)

        new_domains = failed_domains - existing
        if new_domains:
            with open(BLACKLIST_FILE, 'a') as f:
                for domain in new_domains:
                    f.write(f"{domain}\n")
            print(f"🆕 新增 {len(new_domains)} 个域名到黑名单")

    print(f"\n✅ 全部源检测完成，最终保留 {len(processed)} 个不重复的有效源")
    return processed


def organize_channels(processed, alias_map, group_map):
    """整理频道数据，并进行URL去重"""
    print("\n📚 整理频道数据...")
    organized = {'ipv4': OrderedDict(), 'ipv6': OrderedDict()}
    duplicate_stats = {'total': 0, 'channel': {}}

    for name, url, speed, ip_type, protocol in processed:
        if ip_type not in ('ipv4', 'ipv6'):
            print(f"⚠️ 异常IP类型: {ip_type}，使用ipv4代替 ← {url}")
            ip_type = 'ipv4'

        std_name = alias_map.get(name, name)
        group = group_map.get(std_name, '其他')

        if group not in organized[ip_type]:
            organized[ip_type][group] = OrderedDict()
        if std_name not in organized[ip_type][group]:
            organized[ip_type][group][std_name] = []

        # 检查同一频道下是否有重复URL
        existing_urls = {normalize_url(u[0]) for u in organized[ip_type][group][std_name]}
        normalized_url = normalize_url(url)
        
        if normalized_url in existing_urls:
            # 找到重复的源，保留速度更快的
            for i, (existing_url, existing_speed, existing_protocol) in enumerate(organized[ip_type][group][std_name]):
                if normalize_url(existing_url) == normalized_url:
                    if speed > existing_speed:
                        # 用更快的替换
                        organized[ip_type][group][std_name][i] = (url, speed, protocol)
                        duplicate_stats['total'] += 1
                        duplicate_stats['channel'][std_name] = duplicate_stats['channel'].get(std_name, 0) + 1
                        print(f"🔄 频道 '{std_name}' 替换重复URL: 新速度 {speed:.1f}KB/s > 旧速度 {existing_speed:.1f}KB/s")
                    break
        else:
            # 没有重复，添加新URL
            organized[ip_type][group][std_name].append((url, speed, protocol))

    # 打印去重统计
    if duplicate_stats['total'] > 0:
        print(f"🔁 频道内去重: 共清理 {duplicate_stats['total']} 个重复源")
        if len(duplicate_stats['channel']) <= 10:  # 只显示前10个频道
            for channel, count in duplicate_stats['channel'].items():
                print(f"   📺 {channel}: {count} 个重复源")
        else:
            print(f"   📺 涉及 {len(duplicate_stats['channel'])} 个频道")
    
    # 对每个频道的源按速度排序
    for ip_type in ['ipv4', 'ipv6']:
        for group in organized[ip_type]:
            for channel in organized[ip_type][group]:
                organized[ip_type][group][channel].sort(key=lambda x: x[1], reverse=True)
    
    return organized


def deduplicate_final_output(txt_lines, m3u_lines):
    """对最终输出进行去重"""
    print("\n🔁 对最终输出进行去重...")
    
    # 对TXT格式去重
    txt_dict = {}
    txt_duplicates = 0
    for line in txt_lines:
        if line.endswith(',#genre#'):
            txt_dict[line] = line
        elif ',' in line:
            channel, url = line.split(',', 1)
            key = f"{channel},{normalize_url(url)}"
            if key not in txt_dict:
                txt_dict[key] = line
            else:
                txt_duplicates += 1
    
    deduped_txt = list(txt_dict.values())
    
    # 对M3U格式去重
    m3u_dict = {}
    m3u_duplicates = 0
    i = 0
    while i < len(m3u_lines):
        if m3u_lines[i].startswith('#EXTINF:'):
            if i + 1 < len(m3u_lines) and not m3u_lines[i + 1].startswith('#'):
                extinf_line = m3u_lines[i]
                url_line = m3u_lines[i + 1]
                key = normalize_url(url_line)
                if key not in m3u_dict:
                    m3u_dict[key] = (extinf_line, url_line)
                else:
                    m3u_duplicates += 1
                i += 2
            else:
                i += 1
        else:
            i += 1
    
    # 重新构建M3U文件
    deduped_m3u = ['#EXTM3U x-tvg-url="https://gh.catmak.name/https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"']
    for extinf, url in m3u_dict.values():
        deduped_m3u.append(extinf)
        deduped_m3u.append(url)
    
    if txt_duplicates > 0 or m3u_duplicates > 0:
        print(f"✅ 去重完成: 移除 {txt_duplicates} 个重复TXT行，{m3u_duplicates} 个重复M3U源")
    
    return deduped_txt, deduped_m3u


def finalize_output(organized, group_order, channel_order):
    """生成输出文件 - 合并所有协议到单一文件，并进行去重"""
    print("\n📂 生成结果文件...")
    
    for ip_type in ['ipv4', 'ipv6']:
        txt_lines = []
        m3u_lines = [
            '#EXTM3U x-tvg-url="https://gh.catmak.name/https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"',
        ]

        # 统计信息
        total_sources = 0
        speed_stats = []
        seen_channels = set()

        # 按模板顺序处理分组
        for group in group_order:
            if group not in organized[ip_type]:
                continue

            txt_lines.append(f"{group},#genre#")

            # 处理模板频道
            for channel in channel_order[group]:
                if channel not in organized[ip_type][group]:
                    continue

                # 合并所有协议的源，按速度排序
                all_urls = organized[ip_type][group][channel]
                urls = sorted(all_urls, key=lambda x: x[1], reverse=True)
                
                # 对每个URL，只保留最佳（已排序，第一个最快）
                seen_in_channel = set()
                unique_urls = []
                for url, speed, protocol in urls:
                    normalized_url = normalize_url(url)
                    if normalized_url not in seen_in_channel:
                        seen_in_channel.add(normalized_url)
                        unique_urls.append((url, speed, protocol))
                
                # 生成TXT格式：每个URL单独一行
                for url, speed, protocol in unique_urls:
                    txt_lines.append(f"{channel},{url}")
                    total_sources += 1
                    speed_stats.append(speed)
                    
                    # 生成M3U格式
                    protocol_icon = "🔒" if protocol == "https" else "📹" if protocol in ['rtmp', 'rtmps'] else "🌐"
                    m3u_lines.append(f'#EXTINF:-1 tvg-name="{channel}" tvg-logo="https://gh.catmak.name/https://raw.githubusercontent.com/fanmingming/live/main/tv/{channel}.png" group-title="{group}",{protocol_icon} {channel} | {speed:.1f}KB/s')
                    m3u_lines.append(url)
                
                seen_channels.add(channel)

            # 处理额外频道
            extra = sorted(
                [c for c in organized[ip_type][group] if c not in channel_order[group]],
                key=lambda x: x.lower()
            )
            for channel in extra:
                all_urls = organized[ip_type][group][channel]
                urls = sorted(all_urls, key=lambda x: x[1], reverse=True)
                
                # 去重
                seen_in_channel = set()
                unique_urls = []
                for url, speed, protocol in urls:
                    normalized_url = normalize_url(url)
                    if normalized_url not in seen_in_channel:
                        seen_in_channel.add(normalized_url)
                        unique_urls.append((url, speed, protocol))
                
                if unique_urls:
                    for url, speed, protocol in unique_urls:
                        txt_lines.append(f"{channel},{url}")
                        total_sources += 1
                        speed_stats.append(speed)
                        
                        protocol_icon = "🔒" if protocol == "https" else "📹" if protocol in ['rtmp', 'rtmps'] else "🌐"
                        m3u_lines.append(f'#EXTINF:-1 tvg-name="{channel}" tvg-logo="https://gh.catmak.name/https://raw.githubusercontent.com/fanmingming/live/main/tv/{channel}.png" group-title="{group}",{protocol_icon} {channel} | {speed:.1f}KB/s')
                        m3u_lines.append(url)
                    
                    seen_channels.add(channel)

        # 处理其他分组
        if '其他' in organized[ip_type]:
            txt_lines.append("其他,#genre#")
            for channel in sorted(organized[ip_type]['其他'].keys(), key=lambda x: x.lower()):
                if channel in seen_channels:
                    continue
                    
                all_urls = organized[ip_type]['其他'][channel]
                urls = sorted(all_urls, key=lambda x: x[1], reverse=True)
                
                # 去重
                seen_in_channel = set()
                unique_urls = []
                for url, speed, protocol in urls:
                    normalized_url = normalize_url(url)
                    if normalized_url not in seen_in_channel:
                        seen_in_channel.add(normalized_url)
                        unique_urls.append((url, speed, protocol))
                
                if unique_urls:
                    for url, speed, protocol in unique_urls:
                        txt_lines.append(f"{channel},{url}")
                        total_sources += 1
                        speed_stats.append(speed)
                        
                        protocol_icon = "🔒" if protocol == "https" else "📹" if protocol in ['rtmp', 'rtmps'] else "🌐"
                        m3u_lines.append(f'#EXTINF:-1 tvg-name="{channel}" tvg-logo="https://gh.catmak.name/https://raw.githubusercontent.com/fanmingming/live/main/tv/{channel}.png" group-title="其他",{protocol_icon} {channel} | {speed:.1f}KB/s')
                        m3u_lines.append(url)
        
        # 最终去重
        txt_lines, m3u_lines = deduplicate_final_output(txt_lines, m3u_lines)
        
        # 写入文件
        dir_path = IPV4_DIR if ip_type == 'ipv4' else IPV6_DIR
        
        # 只生成两个文件：result.txt 和 result.m3u
        with open(os.path.join(dir_path, 'result.txt'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(txt_lines))
        with open(os.path.join(dir_path, 'result.m3u'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(m3u_lines))

        # 计算统计信息
        if speed_stats:
            avg_speed = sum(speed_stats) / len(speed_stats)
            max_speed = max(speed_stats)
            min_speed = min(speed_stats)
        else:
            avg_speed = max_speed = min_speed = 0

        print(f"✅ 已生成 {ip_type.upper()} 文件:")
        print(f"   📄 {os.path.join(dir_path, 'result.txt')} - {len(txt_lines)} 行")
        print(f"   📺 {os.path.join(dir_path, 'result.m3u')} - {len(m3u_lines)} 行")
        print(f"   📊 统计: {total_sources} 个源 | 平均速度: {avg_speed:.1f}KB/s")
        print(f"   📈 速度范围: {min_speed:.1f} - {max_speed:.1f}KB/s")
        
        # 统计协议信息
        protocol_count = {}
        for group in organized[ip_type]:
            for channel in organized[ip_type][group]:
                for url, speed, protocol in organized[ip_type][group][channel]:
                    if protocol not in protocol_count:
                        protocol_count[protocol] = 0
                    protocol_count[protocol] += 1
        
        if protocol_count:
            print(f"   🌐 协议分布: {', '.join([f'{p.upper()}:{c}' for p, c in protocol_count.items()])}")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🎬 IPTV直播源处理脚本（增强版）")
    print("=" * 60)
    
    # 新增运行次数管理[7](@ref)
    run_count = manage_run_count()
    
    print(f"🔧 配置参数:")
    print(f"   📊 速度阈值: {SPEED_THRESHOLD}KB/s")
    print(f"   🔢 运行次数: {run_count}/{RESET_COUNT}")
    print(f"   🔐 HTTPS证书验证: {'开启' if HTTPS_VERIFY else '关闭'}")
    print(f"   ⏱️ 测速时长: {SPEED_TEST_DURATION}秒")
    print(f"   👥 最大并发数: {MAX_WORKERS}")
    print(f"   📁 输出文件: result.txt, result.m3u")
    print(f"   🔁 去重功能: 已启用")

    # 初始化日志文件
    with open(SPEED_LOG, 'w', encoding='utf-8') as f:
        f.write(f"测速日志 {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"速度阈值: {SPEED_THRESHOLD}KB/s\n")
        f.write(f"运行次数: {run_count}\n")
        f.write(f"HTTPS验证: {HTTPS_VERIFY}\n\n")

    # 清除URL缓存
    url_cache.clear()

    # 初始化数据
    alias_map, group_map, group_order, channel_order = parse_demo_file()
    sources = fetch_sources() + parse_local()
    blacklist = read_blacklist()

    # 处理流程
    filtered = filter_sources(sources, blacklist)
    processed = process_sources(filtered)
    organized = organize_channels(processed, alias_map, group_map)
    finalize_output(organized, group_order, channel_order)

    print("\n" + "=" * 60)
    print("🎉 处理完成！")
    print(f"🔢 本次运行次数: {run_count}")
    if run_count >= RESET_COUNT - 1:
        print(f"⚠️ 下次运行将清空黑名单")
    print("📁 结果文件:")
    print(f"   IPv4: {IPV4_DIR}/result.txt, result.m3u")
    print(f"   IPv6: {IPV6_DIR}/result.txt, result.m3u")
    print("🔍 所有协议源已合并到同一文件中")
    print("✅ 去重功能已启用，已移除重复的URL")
    print("=" * 60)
