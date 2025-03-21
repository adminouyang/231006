import requests
import pandas as pd
import re
import os

urls = [
    #"https://ghproxy.cc/https://raw.githubusercontent.com/junge3333/yrys2026/refs/heads/main/2026yrys.txt",
    #"https://ghproxy.cc/https://raw.githubusercontent.com/HD1116/iptv-m3u8/refs/heads/master/tv/iptv4.txt",
   #      "https://gh-proxy.com/https://raw.githubusercontent.com/250992941/iptv/refs/heads/main/st1.txt",
   #  "https://gh-proxy.com/https://raw.githubusercontent.com/frxz751113/IPTVzb1/refs/heads/main/综合源.txt",
   #  "https://gh-proxy.com/https://raw.githubusercontent.com/frxz751113/IPTVzb1/refs/heads/main/网络收集.txt",
   #  "https://gh-proxy.com/https://raw.githubusercontent.com/dengmeiqing/IPTV1/refs/heads/main/live.txt",
   "https://gh-proxy.com/https://raw.githubusercontent.com/fudong305/iptv/refs/heads/main/gl.m3u",
   # "https://gh-proxy.com/https://raw.githubusercontent.com/adminouyang/231006/refs/heads/main/tvbox/直播源/手动收集.txt",
   #  "https://live.zhoujie218.top/tv/iptv4.txt",
   # "https://tv.youdu.fan:666/live/",
   # "http://ww.weidonglong.com/dsj.txt",
   #  "http://xhztv.top/zbc.txt",
   #  "https://gh-proxy.com/https://raw.githubusercontent.com/zht298/IPTVlist/refs/heads/main/bh.txt",
   #  "https://gh-proxy.com/https://raw.githubusercontent.com/isw866/iptv/refs/heads/main/iptv4.m3u",
   #  "http://home.jundie.top:81/Cat/tv/live.txt",
   # "https://gh-proxy.com/https://raw.githubusercontent.com/jiangyong9977/iptv/refs/heads/main/mytv.txt",
   #  "https://gh-proxy.com/https://raw.githubusercontent.com/kimwang1978/collect-tv-txt/main/merged_output.txt",
   #  "https://gh-proxy.com/https://raw.githubusercontent.com/djhui/IPTV/refs/heads/main/IPTV.m3u",
   #  "https://gh-proxy.com/https://raw.githubusercontent.com/vbskycn/iptv/refs/heads/master/tv/iptv4.txt",
   #  "http://www.clmy.cc:35455/tv.m3u",#肥羊IPTV聚合
   #  "http://wab201.win:35455/tv.m3u",#肥羊IPTV聚合
   #  "http://146.235.213.45:35455/tv.m3u",#肥羊IPTV聚合
   #  "",#yy轮播
   #  "http://wab201.win:35455/yylunbo.m3u",#yy轮播
   #  "http://www.clmy.cc:35455/yylunbo.m3u",#yy轮播

    #"https://ghproxy.cc/https://raw.githubusercontent.com/maitel2020/iptv-self-use/refs/heads/main/iptv.m3u",
    #"https://live.zbds.top/tv/iptv4.txt",
    #"https://ghproxy.cc/https://raw.githubusercontent.com/isw866/iptv/refs/heads/main/ipv4.m3u"
]

ipv4_pattern = re.compile(r'^http://(\d{1,3}\.){3}\d{1,3}')
ipv6_pattern = re.compile(r'^http://\[([a-fA-F0-9:]+)\]')

def fetch_streams_from_url(url):
    print(f"正在爬取网站源: {url}")
    try:
        response = requests.get(url, timeout=6)  # 增加超时处理
        response.encoding = 'utf-8'  # 确保使用utf-8编码
        if response.status_code == 200:
            content = response.text
            print(f"成功获取源自: {url}")
            return content
        else:
            print(f"从 {url} 获取数据失败，状态码: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"请求 {url} 时发生错误: {e}")
        return None

def fetch_all_streams():
    all_streams = []
    for url in urls:
        content = fetch_streams_from_url(url)
        if content:
            all_streams.append(content)
        else:
            print(f"跳过来源: {url}")
    return "\n".join(all_streams)

def parse_m3u(content):
    lines = content.splitlines()
    streams = []
    current_program = None

    for line in lines:
        if line.startswith("#EXTINF"):
            program_match = re.search(r'tvg-name="([^"]+)"', line)
            if program_match:
                current_program = program_match.group(1).strip()
        elif line.startswith("http"):
            stream_url = line.strip()
            if current_program:
                streams.append({"program_name": current_program, "stream_url": stream_url})

    return streams

def parse_txt(content):
    lines = content.splitlines()
    streams = []

    for line in lines:
        match = re.match(r"(.+?),\s*(http.+)", line)
        if match:
            program_name = match.group(1).strip()
            stream_url = match.group(2).strip()
            streams.append({"program_name": program_name, "stream_url": stream_url})

    return streams

def organize_streams(content):
    if content.startswith("#EXTM3U"):
        streams = parse_m3u(content)
    else:
        streams = parse_txt(content)

    df = pd.DataFrame(streams)
    df = df.drop_duplicates(subset=['program_name', 'stream_url'])
    grouped = df.groupby('program_name')['stream_url'].apply(list).reset_index()

    return grouped

def save_to_txt(grouped_streams, filename="py/TvSources/iptv.txt"):
    filepath = os.path.join(os.getcwd(), filename)
    print(f"保存文件的路径是: {filepath}")
    ipv4_lines = []
    ipv6_lines = []

    for _, row in grouped_streams.iterrows():
        program_name = row['program_name']
        stream_urls = row['stream_url']

        for url in stream_urls:
            if ipv4_pattern.match(url):
                ipv4_lines.append(f"{program_name},{url}")
            elif ipv6_pattern.match(url):
                ipv6_lines.append(f"{program_name},{url}")

    with open(filepath, 'w', encoding='utf-8') as output_file:
        output_file.write("# IPv4 Streams\n")
        output_file.write("\n".join(ipv4_lines))
        output_file.write("\n\n# IPv6 Streams\n")
        output_file.write("\n".join(ipv6_lines))

    print(f"所有源已保存到 {filepath}")

if __name__ == "__main__":
    print("开始抓取所有源...")
    all_content = fetch_all_streams()
    if all_content:
        print("开始整理源...")
        organized_streams = organize_streams(all_content)
        save_to_txt(organized_streams)
    else:
        print("未能抓取到任何源。")
