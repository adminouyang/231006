import re
import requests
import os

targets = []
ipv4 = []
ipv6 = []


# m3u8 解析方法
def m3u8_decode(file_content):
    result_ipv6 = []
    result_ipv4 = []
    tv_name = ""
    for file_line in file_content.split("\n"):
        file_line = file_line.strip()
        if file_line.startswith("#EXTINF"):
            tv_name = file_line.split(",")[-1]
        elif file_line and not file_line.startswith("#"):
            if test_url(file_line):
                if not is_valid_ipv6(file_line):
                    result_ipv4.append({
                        "name": tv_name,
                        "url": file_line
                    })
                '''
                else:
                    result_ipv6.append({
                        "name": tv_name,
                        "url": file_line
                    })
                '''
            tv_name = ""
    return result_ipv4.copy(), result_ipv6.copy()


# 测试是否为ipv6地址
def is_valid_ipv6(url):
    pattern = (r'^(([0-9a-fA-F]{1,4}):){7}([0-9a-fA-F]{1,4})$|^(([0-9a-fA-F]{1,4}):){0,6}:([0-9a-fA-F]{1,4})$|^((['
               r'0-9a-fA-F]{1,4}):){0,5}:([0-9a-fA-F]{1,4}):$|^(([0-9a-fA-F]{1,4}):){0,4}:([0-9a-fA-F]{1,4}):{2}$|^(('
               r'[0-9a-fA-F]{1,4}):){0,3}:([0-9a-fA-F]{1,4}):{3}$|^(([0-9a-fA-F]{1,4}):){0,2}:([0-9a-fA-F]{1,'
               r'4}):{4}$|^([0-9a-fA-F]{1,4}):{5}:([0-9a-fA-F]{1,4})$|^:((:[0-9a-fA-F]{1,4}){1,7}|:)$')
    if re.match(pattern, url):
        return True
    else:
        return False


# 测试视频地址是否可用
def test_url(video_url):
    # print("正在测试视频地址：" + video_url)
    try:
        video_response = requests.head(video_url, allow_redirects=True, timeout=5)
        if video_response.status_code == 200:
            return True
        else:
            return False
    except requests.RequestException as e:
        return False


# txt 解析方法
def txt_decode(txt_content):
    result_ipv6 = []
    result_ipv4 = []
    for txt_line in txt_content.split("\n"):
        txt_line = txt_line.strip()
        if "更新" in txt_line:
            break
        elif "#genre#" in txt_line:
            continue
        elif "http" in txt_line and "," in txt_line:
            txt_line_data = txt_line.split(",")
            if test_url(txt_line_data[1]):
                if not is_valid_ipv6(txt_line_data[1]):                    
                    result_ipv4.append({
                        "name": txt_line_data[0],
                        "url": txt_line_data[1]
                    })
                '''                   
                else:
                    result_ipv4.append({
                        "name": txt_line_data[0],
                        "url": txt_line_data[1]
                    })
                '''
    return result_ipv4.copy(), result_ipv6.copy()


# 从urls.txt中读取所有直播源合集URL
with open("./py/TvSources/urls.txt", "r", encoding="utf-8") as file:
    lines = file.readlines()
    for line in lines:
        data = line.split(",")
        url = {
            "url": data[1].strip(),
            # 0代表采用m3u8解析  1代表采用txt解析
            "type": 0 if data[0].strip() == "m3u8" else 1
        }
        targets.append(url)

for target in targets:
    response = requests.get(target["url"])
    response.encoding = "utf-8"
    content = response.text
    # 采用m3u8解析
    if target["type"] == 0:
        ipv4_datas, ipv6_datas = m3u8_decode(content)
        ipv4.extend(ipv4_datas)
        # ipv6.extend(ipv6_datas)
    else:
        ipv4_datas, ipv6_datas = txt_decode(content)
        ipv4.extend(ipv4_datas)
        # ipv6.extend(ipv6_datas)

# 输出可用ipv4节目到文件
with open("./py/TvSources/ipv4.txt", "w", encoding="utf-8") as file:
    for data in ipv4:
        # data[0]是频道名称 data[1]是链接
        file.write(data["name"] + "," + data["url"] + "\n")

# 输出可用ipv6节目到文件
'''
with open("./py/TvSources/ipv6.txt", "w", encoding="utf-8") as file:
    for data in ipv6:
        # data[0]是频道名称 data[1]是链接
        file.write(data["name"] + "," + data["url"] + "\n")
'''

normal_ipv4 = []
normal_ipv6 = []
programs = []
# 输出可用央视频道+地方频道到文件
with open("./py/TvSources/program.txt", "r", encoding="utf-8") as file:
    for program in file.readlines():
        programs.append(program.strip())

for program in programs:
    # ipv4节目
    for data in ipv4:
        if program in data["name"]:
            normal_ipv4.append({
                "name": data["name"],
                "url": data["url"]
            })
    # ipv6节目
    '''
    for data in ipv6:
        if program in data["name"]:
            normal_ipv6.append({
                "name": program,
                "url": data["url"]
            })
    '''

with open("./py/TvSources/ipv4normal.txt", "w", encoding="utf-8") as file:
    for data in normal_ipv4:
        file.write(data["name"] + "," + data["url"] + "\n")

'''
with open("./py/TvSources/ipv6normal.txt", "w", encoding="utf-8") as file:
    for data in normal_ipv6:
        file.write(data["name"] + "," + data["url"] + "\n")
'''
