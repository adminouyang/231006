import asyncio
import aiohttp
import datetime
import requests
import json
import re
from urllib.parse import urljoin, urlparse
import time
import os
import random
from typing import List, Tuple, Dict, Set
import socket
import statistics

URL_FILE = "https://raw.githubusercontent.com/adminouyang/231006/refs/heads/main/py/Hotel/hotel_ip.txt"

CHANNEL_CATEGORIES = {
    "央视频道": [
        "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV4欧洲", "CCTV4美洲", "CCTV5", "CCTV5+", "CCTV6", "CCTV7",
        "CCTV8", "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15", "CCTV16", "CCTV17",
        "兵器科技", "风云音乐", "风云足球", "风云剧场", "怀旧剧场", "第一剧场", "女性时尚", "世界地理", "央视台球", "高尔夫网球",
        "央视文化精品", "卫生健康", "电视指南", "老故事", "中学生", "发现之旅", "书法频道", "国学频道", "环球奇观"
    ],
    "卫视频道": [
        "湖南卫视", "浙江卫视", "江苏卫视", "东方卫视", "深圳卫视", "北京卫视", "广东卫视", "广西卫视", "东南卫视", "海南卫视",
        "河北卫视", "河南卫视", "湖北卫视", "江西卫视", "四川卫视", "重庆卫视", "贵州卫视", "云南卫视", "天津卫视", "安徽卫视",
        "山东卫视", "辽宁卫视", "黑龙江卫视", "吉林卫视", "内蒙古卫视", "宁夏卫视", "山西卫视", "陕西卫视", "甘肃卫视", "青海卫视",
        "新疆卫视", "西藏卫视", "三沙卫视", "兵团卫视", "延边卫视", "安多卫视", "康巴卫视", "农林卫视", "山东教育卫视",
        "中国教育1台", "中国教育2台", "中国教育3台", "中国教育4台", "早期教育"
    ],
    "数字频道": [
        "CHC动作电影", "CHC家庭影院", "CHC影迷电影", "淘电影", "淘精彩", "淘剧场", "淘4K", "淘娱乐", "淘BABY", "淘萌宠", "重温经典",
        "星空卫视", "CHANNEL[V]", "凤凰卫视中文台", "凤凰卫视资讯台", "凤凰卫视香港台", "凤凰卫视电影台", "求索纪录", "求索科学",
        "求索生活", "求索动物", "纪实人文", "金鹰纪实", "纪实科教", "睛彩青少", "睛彩竞技", "睛彩篮球", "睛彩广场舞", "魅力足球", "五星体育",
        "劲爆体育", "快乐垂钓", "茶频道", "先锋乒羽", "天元围棋", "汽摩", "梨园频道", "文物宝库", "武术世界",
        "乐游", "生活时尚", "都市剧场", "欢笑剧场", "游戏风云", "金色学堂", "动漫秀场", "新动漫", "卡酷少儿", "金鹰卡通", "优漫卡通", "哈哈炫动", "嘉佳卡通", 
        "中国交通", "中国天气", "海看大片", "经典电影", "精彩影视", "喜剧影院", "动作影院", "都市剧场", "精品剧场"
    ],
    "广东频道": [
        "广东影视","广东珠江", "广东体育", "广东新闻", "广东公共", "梅州-1", "梅州-2", "惠州公共", "经济科教", "广东少儿", "岭南戏曲"
    ],
    "吉林频道": [
        "吉林生活","长影频道", "吉林都市", "吉林乡村", "吉林市公共", "吉林影视", "吉林新闻", "吉林舒兰综合频道"
    ],
    "山东频道": [
        "山东齐鲁", "山东影视", "山东公共", "山东体育", "山东综艺", "山东少儿", "济宁综合", "济宁公共", "梁山综合", "梁山影视"
    ],
    "新疆频道": [
        "新疆卫视-3","新疆卫视-5"
    ],
    "其它频道": [
    ],
}

CHANNEL_MAPPING = {
    "CCTV1": ["CCTV-1", "CCTV1-综合", "CCTV-1 综合", "CCTV-1综合", "CCTV1HD", "CCTV-1高清", "CCTV-1HD", "cctv-1HD", "CCTV1综合高清", "cctv1"],
    "CCTV2": ["CCTV-2", "CCTV2-财经", "CCTV-2 财经", "CCTV-2财经", "CCTV2HD", "CCTV-2高清", "CCTV-2HD", "cctv-2HD", "CCTV2财经高清", "cctv2"],
    "CCTV3": ["CCTV-3", "CCTV3-综艺", "CCTV-3 综艺", "CCTV-3综艺", "CCTV3HD", "CCTV-3高清", "CCTV-3HD", "cctv-3HD", "CCTV3综艺高清", "cctv3"],
    "CCTV4": ["CCTV-4", "CCTV4-国际", "CCTV-4 中文国际", "CCTV-4中文国际", "CCTV4HD", "cctv4HD", "CCTV-4HD", "CCTV4-中文国际", "CCTV4国际高清", "cctv4"],
    "CCTV4欧洲": ["CCTV-4欧洲", "CCTV-4欧洲", "CCTV4欧洲 HD", "CCTV-4 欧洲", "CCTV-4中文国际欧洲", "CCTV4中文欧洲", "CCTV4欧洲HD", "cctv4欧洲HD", "CCTV-4欧洲HD", "cctv-4欧洲HD"],
    "CCTV4美洲": ["CCTV-4美洲", "CCTV-4北美", "CCTV4美洲 HD", "CCTV-4 美洲", "CCTV-4中文国际美洲", "CCTV4中文美洲", "CCTV4美洲HD", "cctv4美洲HD", "CCTV-4美洲HD", "cctv-4美洲HD"],
    "CCTV5": ["CCTV-5", "CCTV5-体育", "CCTV-5 体育", "CCTV-5体育", "CCTV5HD", "CCTV-5高清", "CCTV-5HD", "CCTV5体育", "CCTV5体育高清", "cctv5"],
    "CCTV5+": ["CCTV-5+", "CCTV5+体育赛事", "CCTV-5+ 体育赛事", "CCTV5+体育赛事", "CCTV5+HD", "CCTV-5+高清", "CCTV-5+HD", "cctv-5+HD", "CCTV5plas", "CCTV5+体育赛视高清", "cctv5+"],
    "CCTV6": ["CCTV-6", "CCTV6-电影", "CCTV-6 电影", "CCTV-6电影", "CCTV6HD", "CCTV-6高清", "CCTV-6HD", "cctv-6HD", "CCTV6电影高清", "cctv6"],
    "CCTV7": ["CCTV-7", "CCTV7-军农", "CCTV-7 国防军事", "CCTV-7国防军事", "CCTV7HD", "CCTV-7高清", "CCTV-7HD", "CCTV7-国防军事", "CCTV7军事高清", "cctv7"],
    "CCTV8": ["CCTV-8", "CCTV8-电视剧", "CCTV-8 电视剧", "CCTV-8电视剧", "CCTV8HD", "CCTV-8高清", "CCTV-8HD", "cctv-8HD", "CCTV8电视剧高清", "cctv8"],
    "CCTV9": ["CCTV-9", "CCTV9-纪录", "CCTV-9 纪录", "CCTV-9纪录", "CCTV9HD", "cctv9HD", "CCTV-9高清", "cctv-9HD", "CCTV9记录高清", "cctv9"],
    "CCTV10": ["CCTV-10", "CCTV10-科教", "CCTV-10 科教", "CCTV-10科教", "CCTV10HD", "CCTV-10高清", "CCTV-10HD", "CCTV-10高清", "CCTV10科教高清", "cctv10"],
    "CCTV11": ["CCTV-11", "CCTV11-戏曲", "CCTV-11 戏曲", "CCTV-11戏曲", "CCTV11HD", "cctv11HD", "CCTV-11HD", "cctv-11HD", "CCTV11戏曲高清", "cctv11"],
    "CCTV12": ["CCTV-12", "CCTV12-社会与法", "CCTV-12 社会与法", "CCTV-12社会与法", "CCTV12HD", "CCTV-12高清", "CCTV-12HD", "cctv-12HD", "CCTV12社会与法高清", "cctv12"],
    "CCTV13": ["CCTV-13", "CCTV13-新闻", "CCTV-13 新闻", "CCTV-13新闻", "CCTV13HD", "cctv13HD", "CCTV-13HD", "cctv-13HD", "CCTV13新闻高清", "cctv13"],
    "CCTV14": ["CCTV-14", "CCTV14-少儿", "CCTV-14 少儿", "CCTV-14少儿", "CCTV14HD", "CCTV-14高清", "CCTV-14HD", "CCTV少儿", "CCTV14少儿高清", "cctv14"],
    "CCTV15": ["CCTV-15", "CCTV15-音乐", "CCTV-15 音乐", "CCTV-15音乐", "CCTV15HD", "cctv15HD", "CCTV-15HD", "cctv-15HD", "CCTV15音乐高清", "cctv15"],
    "CCTV16": ["CCTV-16", "CCTV-16 HD", "CCTV-16 4K", "CCTV-16奥林匹克", "CCTV16HD", "cctv16HD", "CCTV-16HD", "cctv-16HD", "CCTV16奥林匹克高清", "cctv16"],
    "CCTV17": ["CCTV-17", "CCTV17高清", "CCTV17 HD", "CCTV-17农业农村", "CCTV17HD", "cctv17HD", "CCTV-17HD", "cctv-17HD", "CCTV17农业农村高清", "cctv17"],
    "兵器科技": ["CCTV-兵器科技", "CCTV兵器科技", "CCTV兵器高清"],
    "风云音乐": ["CCTV-风云音乐", "CCTV风云音乐"],
    "第一剧场": ["CCTV-第一剧场", "CCTV第一剧场"],
    "风云足球": ["CCTV-风云足球", "CCTV风云足球"],
    "风云剧场": ["CCTV-风云剧场", "CCTV风云剧场"],
    "怀旧剧场": ["CCTV-怀旧剧场", "CCTV怀旧剧场"],
    "女性时尚": ["CCTV-女性时尚", "CCTV女性时尚"],
    "世界地理": ["CCTV-世界地理", "CCTV世界地理"],
    "央视台球": ["CCTV-央视台球", "CCTV央视台球"],
    "高尔夫网球": ["CCTV-高尔夫网球", "CCTV高尔夫网球", "CCTV央视高网", "CCTV-高尔夫·网球", "央视高网"],
    "央视文化精品": ["CCTV-央视文化精品", "CCTV央视文化精品", "CCTV文化精品", "CCTV-文化精品", "文化精品", "央视文化"],
    "卫生健康": ["CCTV-卫生健康", "CCTV卫生健康"],
    "电视指南": ["CCTV-电视指南", "CCTV电视指南"],
    "东南卫视": ["福建东南"],
    "东方卫视": ["上海卫视"],
    "农林卫视": ["陕西农林卫视"],
    "内蒙古卫视": ["内蒙古", "内蒙卫视"],
    "康巴卫视": ["四川康巴卫视"],
    "山东教育卫视": ["山东教育"],
    "CETV1": ["中国教育1台", "中国教育一台", "中国教育1", "CETV", "CETV-1", "中国教育", "中国教育高清"],
    "CETV2": ["中国教育2台", "中国教育二台", "中国教育2", "CETV-2 空中课堂", "CETV-2"],
    "CETV3": ["中国教育3台", "中国教育三台", "中国教育3", "CETV-3 教育服务", "CETV-3", "早期教育"],
    "CETV4": ["中国教育4台", "中国教育四台", "中国教育4", "中国教育电视台第四频道", "CETV-4"],
    "CHC动作电影": ["CHC动作电影高清", "动作电影"],
    "CHC家庭影院": ["CHC家庭电影高清", "家庭影院"],
    "CHC影迷电影": ["CHC高清电影", "高清电影", "影迷电影", "chc高清电影"],
    "淘电影": ["IPTV淘电影", "北京IPTV淘电影", "北京淘电影"],
    "淘精彩": ["IPTV淘精彩", "北京IPTV淘精彩", "北京淘精彩"],
    "淘剧场": ["IPTV淘剧场", "北京IPTV淘剧场", "北京淘剧场"],
    "淘4K": ["IPTV淘4K", "北京IPTV4K超清", "北京淘4K", "淘4K", "淘 4K"],
    "淘娱乐": ["IPTV淘娱乐", "北京IPTV淘娱乐", "北京淘娱乐"],
    "淘BABY": ["IPTV淘BABY", "北京IPTV淘BABY", "北京淘BABY", "IPTV淘baby", "北京IPTV淘baby", "北京淘baby"],
    "淘萌宠": ["IPTV淘萌宠", "北京IPTV萌宠TV", "北京淘萌宠"],
    "吉林都市": ["吉视都市"],
    "吉林乡村": ["吉视乡村"],
    "吉林公共": ["吉林市公共"],
    "吉林影视": ["吉视影视"],
    "吉林生活": ["吉视生活"],
    "吉林舒兰综合频道": ["舒兰"],
    "魅力足球": ["上海魅力足球"],
    "睛彩青少": ["睛彩羽毛球"],
    "求索纪录": ["求索记录", "求索纪录4K", "求索记录4K", "求索纪录 4K", "求索记录 4K"],
    "金鹰纪实": ["湖南金鹰纪实", "金鹰记实"],
    "纪实科教": ["北京纪实科教", "BRTV纪实科教", "北京纪实卫视高清"],
    "星空卫视": ["星空衛視", "星空卫視"],
    "CHANNEL[V]": ["Channel [V]", "Channel[V]"],
    "凤凰卫视中文台": ["凤凰中文", "凤凰中文台", "凤凰卫视中文", "凤凰卫视"],
    "凤凰卫视香港台": ["凤凰香港台", "凤凰卫视香港", "凤凰香港"],
    "凤凰卫视资讯台": ["凤凰资讯", "凤凰资讯台", "凤凰咨询", "凤凰咨询台", "凤凰卫视咨询台", "凤凰卫视资讯", "凤凰卫视咨询"],
    "凤凰卫视电影台": ["凤凰电影", "凤凰电影台", "凤凰卫视电影", "鳳凰衛視電影台", " 凤凰电影"],
    "茶频道": ["湖南茶频道"],
    "快乐垂钓": ["湖南快乐垂钓"],
    "先锋乒羽": ["湖南先锋乒羽"],
    "天元围棋": ["天元围棋频道"],
    "汽摩": ["重庆汽摩", "汽摩频道", "重庆汽摩频道"],
    "梨园频道": ["河南梨园频道", "梨园", "河南梨园"],
    "文物宝库": ["河南文物宝库"],
    "武术世界": ["河南武术世界"],
    "乐游": ["乐游频道", "上海乐游频道", "乐游纪实", "SiTV乐游频道", "SiTV 乐游频道"],
    "欢笑剧场": ["上海欢笑剧场4K", "欢笑剧场 4K", "欢笑剧场4K", "上海欢笑剧场"],
    "生活时尚": ["生活时尚4K", "SiTV生活时尚", "上海生活时尚"],
    "都市剧场": ["都市剧场4K", "SiTV都市剧场", "上海都市剧场"],
    "游戏风云": ["游戏风云4K", "SiTV游戏风云", "上海游戏风云"],
    "金色学堂": ["金色学堂4K", "SiTV金色学堂", "上海金色学堂"],
    "动漫秀场": ["动漫秀场4K", "SiTV动漫秀场", "上海动漫秀场"],
    "卡酷少儿": ["北京KAKU少儿", "BRTV卡酷少儿", "北京卡酷少儿", "卡酷动画", "北京卡通", "北京少儿"],
    "哈哈炫动": ["炫动卡通", "上海哈哈炫动"],
    "优漫卡通": ["江苏优漫卡通", "优漫漫画"],
    "金鹰卡通": ["湖南金鹰卡通"],
    "嘉佳卡通": ["佳佳卡通"],
    "中国交通": ["中国交通频道"],
    "中国天气": ["中国天气频道"],
    "经典电影": ["IPTV经典电影"],
}

RESULTS_PER_CHANNEL = 20
SPEED_THRESHOLD = 200  # KB/s
TEST_DOWNLOAD_SIZE = 51200  # 50KB for speed test
TEST_TIMEOUT = 8  # 单个测速任务超时时间
SPEED_TEST_CONCURRENCY = 30  # 测速并发数

def load_urls():
    """从 GitHub 下载 IPTV IP 段列表"""
    try:
        resp = requests.get(URL_FILE, timeout=5)
        resp.raise_for_status()
        urls = [line.strip() for line in resp.text.splitlines() if line.strip()]
        print(f"📡 已加载 {len(urls)} 个基础 URL")
        return urls
    except Exception as e:
        print(f"❌ 下载 {URL_FILE} 失败: {e}")
        exit()

async def generate_urls(url):
    """生成待扫描的URL列表"""
    modified_urls = []

    ip_start = url.find("//") + 2
    ip_end = url.find(":", ip_start)

    base = url[:ip_start]
    ip_prefix = url[ip_start:ip_end].rsplit('.', 1)[0]
    port = url[ip_end:]

    json_paths = [
        "/iptv/live/1000.json?key=txiptv",
        "/iptv/live/1001.json?key=txiptv",
        "/iptv/live/2000.json?key=txiptv",
        "/iptv/live/2001.json?key=txiptv"
    ]

    for i in range(1, 256):
        ip = f"{base}{ip_prefix}.{i}{port}"
        for path in json_paths:
            modified_urls.append(f"{ip}{path}")

    return modified_urls

async def fetch_json(session, url, semaphore):
    """获取JSON数据并解析频道信息"""
    async with semaphore:
        try:
            async with session.get(url, timeout=3) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                results = []
                for item in data.get('data', []):
                    name = item.get('name')
                    urlx = item.get('url')
                    if not name or not urlx or ',' in urlx:
                        continue

                    if not urlx.startswith("http"):
                        urlx = urljoin(url, urlx)

                    for std_name, aliases in CHANNEL_MAPPING.items():
                        if name in aliases:
                            name = std_name
                            break

                    results.append((name, urlx))
                return results
        except Exception as e:
            return []

async def check_url(session, url, semaphore):
    """检查URL是否可用"""
    async with semaphore:
        try:
            async with session.get(url, timeout=3) as resp:
                if resp.status == 200:
                    return url
        except:
            return None

async def test_stream_speed_accurate(session, url, semaphore, test_id=0):
    """准确的速度测试函数，使用分段下载计算平均速度"""
    async with semaphore:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Range': f'bytes=0-{TEST_DOWNLOAD_SIZE-1}'
            }
            
            start_time = time.time()
            total_downloaded = 0
            
            try:
                async with session.get(url, headers=headers, timeout=TEST_TIMEOUT) as resp:
                    if resp.status not in (200, 206):
                        print(f"  ❌ 测速{test_id}: 状态码 {resp.status}")
                        return 0
                    
                    # 分段下载，每段记录时间
                    chunk_size = 8192
                    download_times = []
                    chunk_start = time.time()
                    
                    while total_downloaded < TEST_DOWNLOAD_SIZE:
                        try:
                            # 设置读取超时
                            chunk = await asyncio.wait_for(
                                resp.content.read(chunk_size),
                                timeout=2.0
                            )
                            if not chunk:
                                break
                            
                            chunk_size_actual = len(chunk)
                            total_downloaded += chunk_size_actual
                            
                            chunk_end = time.time()
                            chunk_time = chunk_end - chunk_start
                            download_times.append((chunk_size_actual, chunk_time))
                            chunk_start = chunk_end
                            
                        except asyncio.TimeoutError:
                            break
                        except Exception as e:
                            break
                    
                    end_time = time.time()
                    total_time = end_time - start_time
                    
                    if total_time <= 0 or total_downloaded == 0:
                        print(f"  ⚠️ 测速{test_id}: 下载失败或时间为0")
                        return 0
                    
                    # 计算平均速度 (KB/s)
                    speed_kbs = (total_downloaded / 1024) / total_time
                    
                    # 计算最后一段的速度（更准确）
                    if len(download_times) >= 2:
                        # 取最后3个块的平均速度
                        last_chunks = download_times[-3:] if len(download_times) >= 3 else download_times
                        last_speeds = []
                        for size, t in last_chunks:
                            if t > 0:
                                last_speeds.append((size / 1024) / t)
                        if last_speeds:
                            # 使用最后几段的平均速度，更稳定
                            speed_kbs = sum(last_speeds) / len(last_speeds)
                    
                    # 打印详细的测速结果
                    speed_status = "✅" if speed_kbs >= SPEED_THRESHOLD else "❌"
                    ip_port = extract_ip_port(url) or "Unknown"
                    print(f"  {speed_status} 测速{test_id}: {speed_kbs:7.2f} KB/s | 大小: {total_downloaded/1024:.1f}KB | 时间: {total_time:.2f}s | {ip_port}")
                    
                    return speed_kbs
                    
            except asyncio.TimeoutError:
                print(f"  ⏱️ 测速{test_id}: 超时")
                return 0
            except Exception as e:
                print(f"  ❌ 测速{test_id}: 错误 {str(e)[:30]}")
                return 0
                
        except Exception as e:
            print(f"  ❌ 测速{test_id}: 异常 {str(e)[:30]}")
            return 0

def extract_ip_port(url):
    """从URL中提取IP和端口"""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        
        if not hostname:
            return None
            
        # 解析端口
        if parsed.port:
            port = parsed.port
        elif parsed.scheme == 'https':
            port = 443
        else:
            port = 80
            
        return f"{hostname}:{port}"
    except:
        return None

def is_valid_stream(url):
    """检查是否为有效流"""
    if url.startswith("rtp://") or url.startswith("udp://") or url.startswith("rtsp://"):
        return False
    if "239." in url:
        return False
    if url.startswith("http://16.") or url.startswith("http://10.") or url.startswith("http://192.168."):
        return False
    
    # 检查是否包含流媒体扩展名
    valid_ext = (".m3u8", ".ts", ".flv", ".mp4", ".mkv")
    if any(ext in url.lower() for ext in valid_ext):
        return True
        
    # 或者检查是否包含流媒体路径关键字
    stream_keywords = ("/live/", "/stream/", "/hls/", "/live-stream/", "m3u8", "ts")
    if any(keyword in url.lower() for keyword in stream_keywords):
        return True
        
    return False

async def main():
    print("🚀 开始运行 hotel 脚本 - 优化测速版")
    
    # 加载基础URL
    urls = load_urls()
    
    # 创建会话
    async with aiohttp.ClientSession() as session:
        # 设置信号量控制并发
        scan_semaphore = asyncio.Semaphore(150)
        speed_semaphore = asyncio.Semaphore(SPEED_TEST_CONCURRENCY)
        
        # 生成所有待扫描URL
        all_urls = []
        for url in urls:
            modified_urls = await generate_urls(url)
            all_urls.extend(modified_urls)
        
        print(f"🔍 生成待扫描 URL 共: {len(all_urls)} 个")
        
        # 检测可用JSON API
        print("⏳ 开始检测可用 JSON API...")
        tasks = [check_url(session, u, scan_semaphore) for u in all_urls]
        valid_urls = [r for r in await asyncio.gather(*tasks) if r]
        
        print(f"✅ 可用 JSON 地址: {len(valid_urls)} 个")
        
        # 抓取节目单JSON
        print("📥 开始抓取节目单 JSON...")
        tasks = [fetch_json(session, u, scan_semaphore) for u in valid_urls]
        fetched = await asyncio.gather(*tasks)
        
        # 合并结果
        all_results = []
        for sublist in fetched:
            all_results.extend(sublist)
        
        print(f"📺 抓到原始频道总数: {len(all_results)} 条")
        
        # 去重
        unique_results = []
        seen_channels_urls = set()
        for name, url in all_results:
            key = f"{name}::{url}"
            if key not in seen_channels_urls:
                seen_channels_urls.add(key)
                unique_results.append((name, url))
        
        print(f"🔍 去重后频道总数: {len(unique_results)} 条")
        
        # 过滤无效流
        valid_results = []
        for name, url in unique_results:
            if is_valid_stream(url):
                valid_results.append((name, url))
        
        print(f"✅ 有效流总数: {len(valid_results)} 条")
        
        # 按频道分组
        channel_groups = {}
        for name, url in valid_results:
            if name not in channel_groups:
                channel_groups[name] = []
            channel_groups[name].append(url)
        
        print(f"📊 频道分组数: {len(channel_groups)} 个")
        
        # 特别处理CCTV1 - 测速
        cctv1_urls = channel_groups.get("CCTV1", [])
        cctv1_with_speed = []
        qualified_ips = set()
        
        if cctv1_urls:
            print(f"\n🚀 开始对 CCTV1 进行测速，共 {len(cctv1_urls)} 个源")
            print("=" * 80)
            print("测速结果 (≥200KB/s为合格):")
            print("-" * 80)
            
            # 对CCTV1的所有源进行测速
            speed_tasks = []
            for i, url in enumerate(cctv1_urls[:100]):  # 限制最多测速100个，避免太多
                task = test_stream_speed_accurate(session, url, speed_semaphore, i+1)
                speed_tasks.append(task)
            
            speeds = await asyncio.gather(*speed_tasks)
            
            # 组合URL和速度
            for i, (url, speed) in enumerate(zip(cctv1_urls[:100], speeds)):
                if speed > 0:  # 只保留测速成功的
                    cctv1_with_speed.append((url, speed))
                    
                    # 检查是否合格
                    if speed >= SPEED_THRESHOLD:
                        ip_port = extract_ip_port(url)
                        if ip_port:
                            qualified_ips.add(ip_port)
            
            # 按速度降序排序
            cctv1_with_speed.sort(key=lambda x: x[1], reverse=True)
            
            print("-" * 80)
            print(f"📈 CCTV1 测速完成统计:")
            print(f"   总测试数: {len(cctv1_urls[:100])}")
            print(f"   有效源数: {len(cctv1_with_speed)}")
            print(f"   合格源数(≥{SPEED_THRESHOLD}KB/s): {len(qualified_ips)}")
            
            if cctv1_with_speed:
                print(f"\n🏆 速度排名前10:")
                for i, (url, speed) in enumerate(cctv1_with_speed[:10], 1):
                    ip_port = extract_ip_port(url) or "N/A"
                    print(f"  {i:2}. {speed:7.2f} KB/s - {ip_port}")
        
        # 将合格的IP保存到文件
        if qualified_ips:
            with open("py/Hotel/已检测ip.txt", 'w', encoding='utf-8') as f:
                f.write(f"# CCTV1 测速合格IP列表 (≥{SPEED_THRESHOLD}KB/s)\n")
                f.write(f"# 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 合格IP数量: {len(qualified_ips)}\n")
                f.write("#" * 50 + "\n")
                for ip_port in sorted(qualified_ips):
                    f.write(f"{ip_port}\n")
            print(f"\n💾 已保存 {len(qualified_ips)} 个测速合格的IP到 py/Hotel/已检测ip.txt")
        else:
            print(f"\n⚠️ 没有找到速度大于{SPEED_THRESHOLD}KB/s的CCTV1源")
            # 创建空文件
            with open("py/Hotel/已检测ip.txt", 'w', encoding='utf-8') as f:
                f.write(f"# 没有找到速度大于{SPEED_THRESHOLD}KB/s的CCTV1源\n")
                f.write(f"# 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 构建最终结果
        final_results = []
        
        # 添加CCTV1（使用测速结果，最多取RESULTS_PER_CHANNEL个）
        for url, speed in cctv1_with_speed[:RESULTS_PER_CHANNEL]:
            final_results.append(("CCTV1", url, speed))
        
        # 添加其他频道（每个频道取前3个URL，速度标记为0）
        for name, urls in channel_groups.items():
            if name == "CCTV1":
                continue  # CCTV1已处理
            
            # 每个非CCTV1频道最多取3个URL
            for url in urls[:3]:
                final_results.append((name, url, 0))
        
        print(f"\n🎯 最终频道列表: {len(final_results)} 条")
        
        # 分类整理
        itv_dict = {cat: [] for cat in CHANNEL_CATEGORIES}
        categorized_channels = set()
        
        # 首先处理已定义的频道
        for name, url, speed in final_results:
            categorized = False
            for cat, channels in CHANNEL_CATEGORIES.items():
                if name in channels:
                    itv_dict[cat].append((name, url, speed))
                    categorized_channels.add(name)
                    categorized = True
                    break
        
        # 然后将未分类的频道放入"其它频道"
        for name, url, speed in final_results:
            if name not in categorized_channels:
                itv_dict["其它频道"].append((name, url, speed))
        
        # 打印分类统计
        print("\n📦 分类统计:")
        for cat in CHANNEL_CATEGORIES:
            print(f"  {cat}: {len(itv_dict[cat])} 条")
        
        # 生成最终文件
        beijing_now = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=8))
        ).strftime("%Y-%m-%d %H:%M:%S")
        
        with open("py/Hotel/hotel.txt", 'w', encoding='utf-8') as f:
            f.write("更新时间,#genre#\n")
            f.write(f"{beijing_now},#\n\n")
            
            for cat in CHANNEL_CATEGORIES:
                f.write(f"{cat},#genre#\n")
                
                if cat == "其它频道":
                    # 对"其它频道"按照频道名称排序
                    channels_in_category = {}
                    for name, url, speed in itv_dict[cat]:
                        if name not in channels_in_category:
                            channels_in_category[name] = []
                        channels_in_category[name].append((name, url, speed))
                    
                    # 对频道名称排序
                    sorted_channel_names = sorted(channels_in_category.keys())
                    
                    for channel_name in sorted_channel_names:
                        ch_items = channels_in_category[channel_name]
                        ch_items = ch_items[:RESULTS_PER_CHANNEL]
                        
                        for item in ch_items:
                            f.write(f"{item[0]},{item[1]}\n")
                else:
                    # 原逻辑：只写入在CHANNEL_CATEGORIES[cat]中定义的频道
                    for ch in CHANNEL_CATEGORIES[cat]:
                        ch_items = [x for x in itv_dict[cat] if x[0] == ch]
                        ch_items = ch_items[:RESULTS_PER_CHANNEL]
                        
                        for item in ch_items:
                            f.write(f"{item[0]},{item[1]}\n")
        
        print("\n🎉 hotel.txt 已生成完成！")
        
        # 打印未分类的频道信息
        other_channels = sorted(set([name for name, _, _ in itv_dict["其它频道"]]))
        if other_channels:
            print(f"\n📊 未分类频道 ({len(other_channels)} 个):")
            for i, channel in enumerate(other_channels[:20], 1):
                print(f"  {i:3}. {channel}")
            if len(other_channels) > 20:
                print(f"  ... 还有 {len(other_channels) - 20} 个未显示")

if __name__ == "__main__":
    asyncio.run(main())
