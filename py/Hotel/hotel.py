import asyncio
import aiohttp
import re
import datetime
import requests
import os
import socket
import struct
from urllib.parse import urljoin
import json
from collections import defaultdict
import time

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
    "其它频道": [],
}

CHANNEL_MAPPING = {
    "高清": [""],
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

# 卫视节目到省份的映射
PROVINCE_CHANNELS = {
    "北京": ["北京卫视"],
    "上海": ["东方卫视"],
    "天津": ["天津卫视"],
    "重庆": ["重庆卫视"],
    "河北": ["河北卫视"],
    "山西": ["山西卫视"],
    "内蒙古": ["内蒙古卫视"],
    "辽宁": ["辽宁卫视"],
    "吉林": ["吉林卫视"],
    "黑龙江": ["黑龙江卫视"],
    "江苏": ["江苏卫视"],
    "浙江": ["浙江卫视"],
    "安徽": ["安徽卫视"],
    "福建": ["东南卫视"],
    "江西": ["江西卫视"],
    "山东": ["山东卫视"],
    "河南": ["河南卫视"],
    "湖北": ["湖北卫视"],
    "湖南": ["湖南卫视"],
    "广东": ["广东卫视", "深圳卫视"],
    "广西": ["广西卫视"],
    "海南": ["海南卫视"],
    "四川": ["四川卫视"],
    "贵州": ["贵州卫视"],
    "云南": ["云南卫视"],
    "西藏": ["西藏卫视"],
    "陕西": ["陕西卫视"],
    "甘肃": ["甘肃卫视"],
    "青海": ["青海卫视"],
    "宁夏": ["宁夏卫视"],
    "新疆": ["新疆卫视"],
    "三沙": ["三沙卫视"],
    "兵团": ["兵团卫视"],
    "延边": ["延边卫视"],
    "安多": ["安多卫视"],
    "康巴": ["康巴卫视"],
    "农林": ["农林卫视"],
    "山东教育": ["山东教育卫视"],
    "中国教育1台": ["中国教育1台"],
    "中国教育2台": ["中国教育2台"],
    "中国教育3台": ["中国教育3台"],
    "中国教育4台": ["中国教育4台"],
    "早期教育": ["早期教育"],
}

RESULTS_PER_CHANNEL = 20

# IP地址到省份的映射
IP_PREFIX_TO_PROVINCE = {
    "1.0.0.0": "北京",
    "14.0.0.0": "广东",
    "27.0.0.0": "北京",
    "36.0.0.0": "福建",
    "39.0.0.0": "北京",
    "42.0.0.0": "辽宁",
    "49.0.0.0": "江苏",
    "58.0.0.0": "北京",
    "59.0.0.0": "广东",
    "60.0.0.0": "北京",
    "61.0.0.0": "广东",
    "101.0.0.0": "北京",
    "103.0.0.0": "北京",
    "106.0.0.0": "北京",
    "110.0.0.0": "北京",
    "111.0.0.0": "北京",
    "112.0.0.0": "北京",
    "113.0.0.0": "广东",
    "114.0.0.0": "北京",
    "115.0.0.0": "北京",
    "116.0.0.0": "北京",
    "117.0.0.0": "北京",
    "118.0.0.0": "北京",
    "119.0.0.0": "四川",
    "120.0.0.0": "北京",
    "121.0.0.0": "上海",
    "122.0.0.0": "江苏",
    "123.0.0.0": "辽宁",
    "124.0.0.0": "黑龙江",
    "125.0.0.0": "吉林",
    "139.0.0.0": "四川",
    "140.0.0.0": "台湾",
    "150.0.0.0": "台湾",
    "163.0.0.0": "上海",
    "175.0.0.0": "台湾",
    "180.0.0.0": "北京",
    "182.0.0.0": "北京",
    "183.0.0.0": "广东",
    "192.0.0.0": "美国",
    "202.0.0.0": "北京",
    "203.0.0.0": "香港",
    "210.0.0.0": "台湾",
    "211.0.0.0": "北京",
    "218.0.0.0": "北京",
    "219.0.0.0": "辽宁",
    "220.0.0.0": "北京",
    "221.0.0.0": "山东",
    "222.0.0.0": "北京",
    "223.0.0.0": "北京",
}

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
    """生成要扫描的URL列表"""
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
    """获取JSON数据并解析频道"""
    async with semaphore:
        try:
            async with session.get(url, timeout=3) as resp:
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

                    # 提取IP地址
                    ip = extract_ip_from_url(urlx)
                    results.append((name, urlx, ip, url))
                return results
        except Exception as e:
            return []

def extract_ip_from_url(url):
    """从URL中提取IP地址"""
    match = re.search(r'http://(\d+\.\d+\.\d+\.\d+)', url)
    if match:
        return match.group(1)
    return None

def get_province_by_ip(ip):
    """根据IP地址获取省份"""
    if not ip:
        return None
    
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return None
        
        # 将IP转换为整数以便比较
        ip_int = struct.unpack("!I", socket.inet_aton(ip))[0]
        
        # 简化版：使用IP前缀判断
        ip_prefix = '.'.join(parts[:2]) + ".0.0"
        if ip_prefix in IP_PREFIX_TO_PROVINCE:
            return IP_PREFIX_TO_PROVINCE[ip_prefix]
        
        # 更精确的匹配：使用IP范围
        for prefix, province in IP_PREFIX_TO_PROVINCE.items():
            prefix_parts = prefix.split('.')
            if len(prefix_parts) == 4:
                prefix_int = struct.unpack("!I", socket.inet_aton(prefix))[0]
                # 检查是否在同一/8网络
                if (ip_int >> 24) == (prefix_int >> 24):
                    return province
        
        return None
    except:
        return None

async def test_channel_speed(session, name, url, timeout=3, retry_count=2):
    """改进的测速函数，使用多种方法尝试，增加重试机制"""
    data_sizes = [10240, 20480, 51200]  # 尝试不同的数据大小：10KB, 20KB, 50KB
    
    for attempt in range(retry_count):
        for data_size in data_sizes:
            # 方法1: 使用Range请求
            try:
                headers = {'Range': f'bytes=0-{data_size-1}', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                start_time = asyncio.get_event_loop().time()
                
                async with session.get(url, headers=headers, timeout=timeout) as response:
                    if response.status in [200, 206]:
                        # 读取数据
                        content = await response.read()
                        end_time = asyncio.get_event_loop().time()
                        
                        if content and end_time > start_time:
                            duration = end_time - start_time
                            if duration > 0:
                                speed = len(content) / 1024 / duration  # KB/s
                                if speed > 0:
                                    return speed
            except asyncio.TimeoutError:
                continue
            except Exception:
                continue
            
            # 方法2: 不使用Range，尝试读取部分数据
            try:
                start_time = asyncio.get_event_loop().time()
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        # 尝试读取部分数据
                        content = b''
                        remaining = data_size
                        
                        async for chunk in response.content.iter_chunked(8192):
                            content += chunk
                            remaining -= len(chunk)
                            if remaining <= 0:
                                break
                        
                        end_time = asyncio.get_event_loop().time()
                        
                        if content and end_time > start_time:
                            duration = end_time - start_time
                            if duration > 0:
                                speed = len(content) / 1024 / duration
                                if speed > 0:
                                    return speed
            except asyncio.TimeoutError:
                continue
            except Exception:
                continue
    
    return 0  # 所有尝试都失败

async def check_url_availability(session, url, semaphore, timeout=2):
    """检查URL是否可用，返回响应时间"""
    async with semaphore:
        try:
            start_time = asyncio.get_event_loop().time()
            async with session.head(url, timeout=timeout) as resp:
                if resp.status in [200, 206, 302, 301]:
                    end_time = asyncio.get_event_loop().time()
                    response_time = (end_time - start_time) * 1000  # 转换为毫秒
                    return response_time
        except:
            pass
        return None

async def check_json_url(session, url, semaphore):
    """检查JSON API是否可用"""
    async with semaphore:
        try:
            async with session.get(url, timeout=2) as resp:
                if resp.status == 200:
                    return url
        except:
            return None

async def process_channel(session, name, url, ip, source_url, semaphore, 
                         test_speed=True, min_speed=100, 
                         max_channels_per_province=5):
    """处理单个频道：检查、测速、过滤"""
    
    # 检查URL格式是否有效
    if not is_valid_stream(url):
        return None
    
    # 获取IP对应的省份
    province = get_province_by_ip(ip) if ip else None
    
    # 默认速度
    speed = 0
    need_speed_test = False
    skip_channel = False
    
    # 判断是否需要测速
    if test_speed and province and province in PROVINCE_CHANNELS:
        province_channels = PROVINCE_CHANNELS[province]
        if name in province_channels:
            need_speed_test = True
    
    # 如果需要测速，进行测速
    if need_speed_test:
        # 先检查URL基本可用性
        response_time = await check_url_availability(session, url, semaphore)
        if response_time is None:
            print(f"  ❌ {name} ({province}) - 无法访问")
            return None
        
        # 进行测速
        speed = await test_channel_speed(session, name, url)
        
        if speed > 0:
            print(f"  📡 {name} ({province}) - 速度: {speed:.2f} KB/s, 响应: {response_time:.0f}ms")
            
            # 如果速度小于最小要求，不保存
            if speed < min_speed:
                print(f"    ❌ 速度不足 {min_speed} KB/s，跳过")
                return None
        else:
            print(f"  ⚠️  {name} ({province}) - 测速失败，响应: {response_time:.0f}ms")
            # 测速失败但URL可访问，可以保存，但标记速度未知
            speed = -1
    else:
        # 不需要测速的频道，只检查可用性
        response_time = await check_url_availability(session, url, semaphore)
        if response_time is None:
            return None
        
        if province:
            print(f"  ✓ {name} ({province}) - 非卫视频道，不测速，响应: {response_time:.0f}ms")
        else:
            print(f"  ✓ {name} - 省份未知，不测速，响应: {response_time:.0f}ms")
    
    return (name, url, speed, province)

def is_valid_stream(url):
    """检查是否为有效的流媒体URL"""
    if url.startswith("rtp://") or url.startswith("udp://") or url.startswith("rtsp://"):
        return False
    if "239." in url:
        return False
    if url.startswith("http://16.") or url.startswith("http://10.") or url.startswith("http://192.168."):
        return False
    
    valid_ext = (".m3u8", ".ts", ".flv", ".mp4", ".mkv")
    return url.startswith("http") and any(ext in url for ext in valid_ext)

async def main():
    print("🚀 开始运行 hotel 脚本")
    
    # 设置并发数
    semaphore = asyncio.Semaphore(80)  # 稍微降低并发数以提高稳定性
    
    # 加载基础URL
    urls = load_urls()
    
    async with aiohttp.ClientSession() as session:
        # 生成所有要扫描的URL
        all_urls = []
        for url in urls:
            modified_urls = await generate_urls(url)
            all_urls.extend(modified_urls)
        
        print(f"🔍 生成待扫描 URL 共: {len(all_urls)} 个")
        
        # 检测可用的JSON API
        print("⏳ 开始检测可用 JSON API...")
        tasks = [check_json_url(session, u, semaphore) for u in all_urls]
        valid_urls = [r for r in await asyncio.gather(*tasks) if r]
        
        print(f"✅ 可用 JSON 地址: {len(valid_urls)} 个")
        for u in valid_urls[:5]:  # 只显示前5个
            print(f"  - {u}")
        if len(valid_urls) > 5:
            print(f"  ... 和 {len(valid_urls) - 5} 个更多")
        
        # 抓取节目单JSON
        print("📥 开始抓取节目单 JSON...")
        tasks = [fetch_json(session, u, semaphore) for u in valid_urls]
        fetched = await asyncio.gather(*tasks)
        
        # 合并结果
        all_channels = []
        for sublist in fetched:
            all_channels.extend(sublist)
        
        print(f"📺 抓到原始频道总数: {len(all_channels)} 条")
        
        # 去重：基于频道名称和URL
        unique_channels = {}
        for name, url, ip, source_url in all_channels:
            key = (name, url)
            if key not in unique_channels:
                unique_channels[key] = (name, url, ip, source_url)
        
        print(f"🔍 去重后频道总数: {len(unique_channels)} 条")
        
        # 处理每个频道：检查、测速、过滤
        print("⏳ 开始处理频道（检查、测速、过滤）...")
        tasks = []
        for name, url, ip, source_url in unique_channels.values():
            task = process_channel(session, name, url, ip, source_url, semaphore, 
                                 test_speed=True, min_speed=100)
            tasks.append(task)
        
        processed_results = await asyncio.gather(*tasks)
        
        # 过滤掉None结果
        final_results = [r for r in processed_results if r is not None]
        
        print(f"✅ 最终有效频道: {len(final_results)} 条")
        
        # 按频道名称分组，统计速度
        channel_stats = defaultdict(list)
        for name, url, speed, province in final_results:
            channel_stats[name].append((url, speed, province))
        
        # 分类频道
        categorized_channels = {cat: [] for cat in CHANNEL_CATEGORIES}
        
        for name in channel_stats:
            # 获取该频道的所有URL，按速度排序
            urls_for_channel = channel_stats[name]
            # 按速度降序排序（速度-1表示测速失败但可访问）
            urls_for_channel.sort(key=lambda x: x[1] if x[1] != -1 else 0, reverse=True)
            
            # 每个频道最多保存RESULTS_PER_CHANNEL个最快的URL
            for url, speed, province in urls_for_channel[:RESULTS_PER_CHANNEL]:
                # 分类
                categorized = False
                for cat, channels in CHANNEL_CATEGORIES.items():
                    if cat != "其它频道" and name in channels:
                        categorized_channels[cat].append((name, url, speed, province))
                        categorized = True
                        break
                
                # 如果未分类，放入"其它频道"
                if not categorized:
                    categorized_channels["其它频道"].append((name, url, speed, province))
        
        # 统计信息
        for cat in CHANNEL_CATEGORIES:
            count = len(categorized_channels[cat])
            print(f"📦 分类《{cat}》找到 {count} 条频道")
        
        # 生成输出文件
        beijing_now = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=8))
        ).strftime("%Y-%m-%d %H:%M:%S")
        
        # 确保输出目录存在
        os.makedirs("py/Hotel", exist_ok=True)
        
        with open("py/Hotel/hotel.txt", 'w', encoding='utf-8') as f:
            f.write("更新时间,#genre#\n")
            f.write(f"{beijing_now},\n\n")
            
            for cat in CHANNEL_CATEGORIES:
                channels_in_cat = categorized_channels[cat]
                if channels_in_cat:
                    f.write(f"{cat},#genre#\n")
                    
                    # 对频道按名称排序
                    channels_by_name = defaultdict(list)
                    for name, url, speed, province in channels_in_cat:
                        channels_by_name[name].append((url, speed, province))
                    
                    # 对频道名称排序
                    sorted_names = sorted(channels_by_name.keys())
                    
                    for name in sorted_names:
                        urls_for_channel = channels_by_name[name]
                        # 每个频道最多输出RESULTS_PER_CHANNEL个URL
                        for url, speed, province in urls_for_channel[:RESULTS_PER_CHANNEL]:
                            f.write(f"{name},{url}\n")
                    f.write("\n")
        
        print("🎉 hotel.txt 已生成完成！")
        
        # 生成详细的统计信息
        with open("py/Hotel/hotel_stats.txt", 'w', encoding='utf-8') as f:
            f.write(f"Hotel IPTV 扫描统计\n")
            f.write(f"更新时间: {beijing_now}\n")
            f.write(f"="*50 + "\n\n")
            
            f.write(f"📊 总体统计:\n")
            f.write(f"  - 原始频道数: {len(all_channels)}\n")
            f.write(f"  - 去重后频道数: {len(unique_channels)}\n")
            f.write(f"  - 最终有效频道数: {len(final_results)}\n")
            f.write(f"  - 可用JSON源: {len(valid_urls)}\n\n")
            
            f.write(f"📈 分类统计:\n")
            for cat in CHANNEL_CATEGORIES:
                count = len(categorized_channels[cat])
                f.write(f"  - {cat}: {count} 个频道\n")
            
            f.write(f"\n📡 各省份卫视测速统计:\n")
            province_stats = defaultdict(list)
            for name, url, speed, province in final_results:
                if province and province in PROVINCE_CHANNELS and name in PROVINCE_CHANNELS[province]:
                    province_stats[province].append(speed)
            
            for province, speeds in sorted(province_stats.items()):
                avg_speed = sum(speeds) / len(speeds) if speeds else 0
                f.write(f"  - {province}: {len(speeds)} 个卫视频道，平均速度: {avg_speed:.2f} KB/s\n")
            
            f.write(f"\n⚡ 测速结果统计:\n")
            speed_stats = {
                "大于1000 KB/s": 0,
                "500-1000 KB/s": 0,
                "100-500 KB/s": 0,
                "小于100 KB/s": 0,
                "测速失败但可访问": 0
            }
            
            for name, url, speed, province in final_results:
                if speed == -1:
                    speed_stats["测速失败但可访问"] += 1
                elif speed > 1000:
                    speed_stats["大于1000 KB/s"] += 1
                elif speed > 500:
                    speed_stats["500-1000 KB/s"] += 1
                elif speed > 100:
                    speed_stats["100-500 KB/s"] += 1
                else:
                    speed_stats["小于100 KB/s"] += 1
            
            for category, count in speed_stats.items():
                f.write(f"  - {category}: {count} 个频道\n")
        
        print("📊 详细统计已保存到 hotel_stats.txt")

if __name__ == "__main__":
    asyncio.run(main())
