import os
import requests
import re
import base64
import cv2
import datetime
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse


# 获取rtp目录下的文件名
files = os.listdir('rtp')

files_name = []

# 去除后缀名并保存至provinces_isps
for file in files:
    name, extension = os.path.splitext(file)
    files_name.append(name)

#忽略不符合要求的文件名
provinces_isps = [name for name in files_name if name.count('_') == 1]

# 打印结果
print(f"本次查询：{provinces_isps}的组播节目") 

for province_isp in provinces_isps:
    province, isp = province_isp.split("_")
    # 根据不同的 isp 设置不同的 org 值
    org = "Chinanet"

    if isp == "电信":
        org = "Chinanet"
    elif isp == "联通":
        org = "CHINA UNICOM China169 Backbone"
    else:
        org = ""

    current_time = datetime.now()
    timeout_cnt = 0
    result_urls = set() 
    str_channels = ''
    while len(result_urls) == 0 and timeout_cnt <= 5:
        try:
            search_url = 'https://fofa.info/result?qbase64='
            search_txt = f'\"udpxy\" && country=\"CN\" && region=\"{province}\" && org=\"{org}\"'
                # 将字符串编码为字节流
            bytes_string = search_txt.encode('utf-8')
                # 使用 base64 进行编码
            search_txt = base64.b64encode(bytes_string).decode('utf-8')
            search_url += search_txt
            print(f"{current_time} 查询运营商 : {province}{isp} ，查询网址 : {search_url}")
            response = requests.get(search_url, timeout=30)
            # 处理响应
            response.raise_for_status()
            # 检查请求是否成功
            html_content = response.text
            # 使用BeautifulSoup解析网页内容
            html_soup = BeautifulSoup(html_content, "html.parser")
            # print(f"{current_time} html_content:{html_content}")
            # 查找所有符合指定格式的网址
            # 设置匹配的格式，如http://8.8.8.8:8888
            pattern = r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+"
            urls_all = re.findall(pattern, html_content)
                # 去重得到唯一的URL列表
            result_urls = set(urls_all)
            print(f"{current_time} result_urls:{result_urls}")
            #对应省份的组播地址:重庆联通cctv1：225.0.4.74:7980，重庆电信cctv1:235.254.199.51:7980，广东电信广东卫视239.77.1.19:5146
            pro_isp = province + isp
            urls_udp = "/udp/239.77.1.19:5146"
            if pro_isp == "广东电信":
                urls_udp = "/udp/239.77.1.19:5146"
            elif pro_isp == "湖南电信":
                urls_udp = "/udp/239.76.253.101:9000"
            elif pro_isp == "重庆联通":
                urls_udp = "/udp/225.0.4.74:7980"
            elif pro_isp == "四川电信":
                urls_udp = "/udp/239.93.0.58:5140"
            else:
                org = ""

            valid_ips = []

            # 遍历所有视频链接
            for url in result_urls:
                ip_port = url.replace("http://", "")
                video_url = url + urls_udp

                # 用OpenCV读取视频
                cap = cv2.VideoCapture(video_url)

                # 检查视频是否成功打开
                if not cap.isOpened():
                    print(f"{current_time} {video_url} 无效")
                else:
                    # 读取视频的宽度和高度
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    print(f"{current_time} {video_url} 的分辨率为 {width}x{height}")
                    # 检查分辨率是否大于0
                    if width > 0 and height > 0:
                        valid_ips.append(ip_port)
                    # 关闭视频流
                    cap.release()
                    
            if valid_ips:
                #生成节目列表
                rtp_filename = f'rtp/{province}_{isp}.txt'
                with open(rtp_filename, 'r', encoding='utf-8') as file:
                    data = file.read()
                txt_filename = f'iptv_{province}{isp}.txt'
                with open(txt_filename, 'w') as new_file:
                    for ip in valid_ips:
                        new_data = data.replace("rtp://", f"http://{ip}/udp/")
                        new_file.write(new_data)

                print(f'已生成播放列表，保存至{txt_filename}')
                group_title = ""
                group_cctv = ["CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5", "CCTV5+", "CCTV6", "CCTV7", "CCTV8", "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15", "CCTV16", "CCTV17", "CCTV4K", "CCTV8K", "CGTN英语", "CGTN记录", "CGTN俄语", "CGTN法语", "CGTN西语", "CGTN阿语"]
                group_shuzi = ["CHC动作电影", "CHC家庭影院", "CHC高清电影", "重温经典", "第一剧场", "风云剧场", "怀旧剧场", "世界地理", "发现之旅", "求索纪录", "兵器科技", "风云音乐", "文化精品", "央视台球", "高尔夫网球", "风云足球", "女性时尚", "电视指南", "中视购物", "中学生", "卫生健康", "央广购物", "家有购物", "老故事", "书画", "中国天气", "收藏天下", "国学频道", "快乐垂钓", "先锋乒羽", "风尚购物", "财富天下", "天元围棋", "摄影频道", "新动漫", "证券服务", "梨园", "置业", "家庭理财", "茶友"]
                group_jiaoyu = ["CETV1", "CETV2", "CETV3", "CETV4", "山东教育", "早期教育"]
                group_weishi = ["北京卫视", "湖南卫视", "东方卫视", "四川卫视", "天津卫视", "安徽卫视", "山东卫视", "广东卫视", "广西卫视", "江苏卫视", "江西卫视", "河北卫视", "河南卫视", "浙江卫视", "海南卫视", "深圳卫视", "湖北卫视", "山西卫视", "东南卫视", "贵州卫视", "辽宁卫视", "重庆卫视", "黑龙江卫视", "内蒙古卫视", "宁夏卫视", "陕西卫视", "甘肃卫视", "吉林卫视", "云南卫视", "三沙卫视", "青海卫视", "新疆卫视", "西藏卫视", "兵团卫视", "延边卫视", "大湾区卫视", "安多卫视", "厦门卫视", "农林卫视", "康巴卫视", "优漫卡通", "哈哈炫动", "嘉佳卡通"]

                #生成m3u
                with open(txt_filename, 'r') as input_file:
                    lines = input_file.readlines()
                #删除空白行
                    lines = [line for line in lines if line.count(',') == 1]
                #lines = [line.strip() for line in lines if line.strip()]

            # 转换格式并写入到 iptv.m3u
                m3u_filename = f'iptv_{province}{isp}.m3u'
                with open(m3u_filename, 'w', encoding='utf-8') as output_file:
                    output_file.write('#EXTM3U  x-tvg-url="https://live.fanmingming.com/e.xml\n')  # 添加 #EXTM3U
                    for line in lines:
                        parts = line.strip().split(',')
                        name1 = parts[0]
                        uppercase_name1 = name1.upper()
                        name1 = uppercase_name1
                        name1 = name1.replace("中央", "CCTV")
                        name1 = name1.replace("高清", "")
                        name1 = name1.replace("HD", "")
                        name1 = name1.replace("标清", "")
                        name1 = name1.replace("频道", "")
                        name1 = name1.replace("-", "")
                        name1 = name1.replace("_", "")
                        name1 = name1.replace(" ", "")
                        name1 = name1.replace("PLUS", "+")
                        name1 = name1.replace("＋", "+")
                        name1 = name1.replace("(", "")
                        name1 = name1.replace(")", "")
                        name1 = name1.replace("CCTV1综合", "CCTV1")
                        name1 = name1.replace("CCTV2财经", "CCTV2")
                        name1 = name1.replace("CCTV3综艺", "CCTV3")
                        name1 = name1.replace("CCTV4国际", "CCTV4")
                        name1 = name1.replace("CCTV4中文国际", "CCTV4")
                        name1 = name1.replace("CCTV5体育", "CCTV5")
                        name1 = name1.replace("CCTV6电影", "CCTV6")
                        name1 = name1.replace("CCTV7军事", "CCTV7")
                        name1 = name1.replace("CCTV7军农", "CCTV7")
                        name1 = name1.replace("CCTV7国防军事", "CCTV7")
                        name1 = name1.replace("CCTV8电视剧", "CCTV8")
                        name1 = name1.replace("CCTV9记录", "CCTV9")
                        name1 = name1.replace("CCTV9纪录", "CCTV9")
                        name1 = name1.replace("CCTV10科教", "CCTV10")
                        name1 = name1.replace("CCTV11戏曲", "CCTV11")
                        name1 = name1.replace("CCTV12社会与法", "CCTV12")
                        name1 = name1.replace("CCTV13新闻", "CCTV13")
                        name1 = name1.replace("CCTV新闻", "CCTV13")
                        name1 = name1.replace("CCTV14少儿", "CCTV14")
                        name1 = name1.replace("CCTV15音乐", "CCTV15")
                        name1 = name1.replace("CCTV16奥林匹克", "CCTV16")
                        name1 = name1.replace("CCTV17农业农村", "CCTV17")
                        name1 = name1.replace("CCTV5+体育赛视", "CCTV5+")
                        name1 = name1.replace("CCTV5+体育赛事", "CCTV5+")
                        name1 = name1.replace("综合教育", "")
                        name1 = name1.replace("空中课堂", "")
                        name1 = name1.replace("教育服务", "")
                        name1 = name1.replace("职业教育", "")
                        name1 = name1.replace("Documentary", "记录")
                        name1 = name1.replace("Français", "法语")
                        name1 = name1.replace("Русский", "俄语")
                        name1 = name1.replace("Español", "西语")
                        name1 = name1.replace("العربية", "阿语")
                        name1 = name1.replace("NewTv", "")
                        name1 = name1.replace("CCTV兵器科技", "兵器科技")
                        name1 = name1.replace("CCTV怀旧剧场", "怀旧剧场")
                        name1 = name1.replace("CCTV世界地理", "世界地理")
                        name1 = name1.replace("CCTV文化精品", "文化精品")
                        name1 = name1.replace("CCTV央视台球", "央视台球")
                        name1 = name1.replace("CCTV央视高网", "央视高网")
                        name1 = name1.replace("CCTV风云剧场", "风云剧场")
                        name1 = name1.replace("CCTV第一剧场", "第一剧场")
                        name1 = name1.replace("CCTV风云足球", "风云足球")
                        name1 = name1.replace("CCTV电视指南", "电视指南")
                        name1 = name1.replace("CCTV风云音乐", "风云音乐")
                        name1 = name1.replace("CCTV女性时尚", "女性时尚")
                        name1 = name1.replace("CHC电影", "CHC高清电影")
                        name2 = parts[0]
                        url = parts[1]
                        if name1 in group_cctv:
                            group_title = "央视频道"
                        elif name1 in group_shuzi:
                            group_title = "数字频道"
                        elif name1 in group_jiaoyu:
                            group_title = "教育频道"
                        elif name1 in group_weishi:
                            group_title = "卫视频道"
                        else:
                            group_title = "其他频道"

                        output_file.write(f'#EXTINF:-1 tvg-id="{name1}" tvg-name="{name1}" tvg-logo="https://live.fanmingming.com/tv/{name1}.png" group-title="{group_title}",{name2}\n{url}\n')
        
                print(f'已保存至{m3u_filename}')

            else:
                print("未找到合适的 IP 地址。")

        except (requests.Timeout, requests.RequestException) as e:
            timeout_cnt += 1
            print(f"{current_time} [{province}]搜索请求发生超时，异常次数：{timeout_cnt}")
            if timeout_cnt <= 5:
                    # 继续下一次循环迭代
                continue
            else:
                print(f"{current_time} 搜索IPTV频道源[]，超时次数过多：{timeout_cnt} 次，停止处理")
            