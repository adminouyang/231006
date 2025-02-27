import re
import requests
import logging
from collections import OrderedDict
from datetime import datetime
import config
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("py/优质源/function.txt", "w", encoding="utf-8"), logging.StreamHandler()])


def parse_template(template_file):
    template_channels = OrderedDict()
    current_category = None

    with open(template_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "#genre#" in line:
                    current_category = line.split(",")[0].strip()
                    template_channels[current_category] = []
                elif current_category:
                    channel_name = line.split(",")[0].strip()
                    template_channels[current_category].append(channel_name)

    return template_channels

def filter_source_urls(template_file):
    template_channels = parse_template(template_file)
    source_urls = config.source_urls

    all_channels = OrderedDict()
    for url in source_urls:
        fetched_channels = fetch_channels(url)
        for category, channel_list in fetched_channels.items():
            if category in all_channels:
                all_channels[category].extend(channel_list)
            else:
                all_channels[category] = channel_list

    matched_channels = match_channels(template_channels, all_channels)

    return matched_channels, template_channels


# 数据清洗函数
def clean_channel_name(channel_name):
    # 使用正则表达式去掉非字母数字字符，但保留频道数字部分
    cleaned_name = re.sub(r'[$「」-]', '', channel_name)  # 去掉中括号、«», 和'-'字符
    cleaned_name = re.sub(r'\s+', '', cleaned_name)  # 去掉所有空白字符
    cleaned_name = re.sub(r'(\D*)(\d+)', lambda m: m.group(1) + str(int(m.group(2))),
                          cleaned_name)  # 将数字前面的部分保留，数字转换为整数
    return cleaned_name.upper()  # 转换为大写


def fetch_channels(url):
    channels = OrderedDict()

    try:
        response = requests.get(url, timeout=6)  # 增加超时处理
        response.raise_for_status()
        response.encoding = 'utf-8'
        if response.status_code == 200:
          lines = response.text.split("\n")
          current_category = None
          is_m3u = any("#EXTINF" in line for line in lines[:15])
          source_type = "m3u" if is_m3u else "txt"
          logging.info(f"url: {url} 获取成功，判断为{source_type}格式")

        if is_m3u:
            for line in lines:
                line = line.strip()
                if line.startswith("#EXTINF"):
                    match = re.search(r'group-title="(.*?)",(.*)', line)
                    if match:
                        current_category = match.group(1).strip()
                        channel_name = match.group(2).strip()
                        if channel_name and channel_name.startswith("CCTV"):  # 判断频道名称是否存在且以CCTV开头
                            channel_name = clean_channel_name(channel_name)  # 频道名称数据清洗

                        if current_category not in channels:
                            channels[current_category] = []
                elif line and not line.startswith("#"):
                    channel_url = line.strip()
                    if current_category and channel_name:
                        channels[current_category].append((channel_name, channel_url))
        else:
            for line in lines:
                line = line.strip()
                if "#genre#" in line:
                    current_category = line.split(",")[0].strip()
                    channels[current_category] = []
                elif current_category:
                    match = re.match(r"^(.*?),(.*?)$", line)
                    if match:
                        channel_name = match.group(1).strip()
                        if channel_name and channel_name.startswith("CCTV"):  # 判断频道名称是否存在且以CCTV开头
                            channel_name = clean_channel_name(channel_name)  # 频道名称数据清洗
                        # 提取频道URL，并分割成多个部分
                        channel_urls = match.group(2).strip().split('#')

                        # 存储每个分割出的URL
                        for channel_url in channel_urls:
                            channel_url = channel_url.strip()  # 去掉前后空白
                            channels[current_category].append((channel_name, channel_url))
                    elif line:
                        channels[current_category].append((line, ''))
        if channels:
            categories = ", ".join(channels.keys())
            logging.info(f"url: {url} 爬取成功✅，包含频道分类: {categories}")
    except requests.RequestException as e:
        logging.error(f"url: {url} 爬取失败❌, Error: {e}")

    return channels

def match_channels(template_channels, all_channels):
    matched_channels = OrderedDict()

    for category, channel_list in template_channels.items():
        matched_channels[category] = OrderedDict()
        for channel_name in channel_list:
            cur_channel_name = channel_name
            cur_list = [channel_name]
            if "|" in channel_name:
                cur_list = channel_name.split("|")
                cur_channel_name = cur_list[0]
            for online_category, online_channel_list in all_channels.items():
                for online_channel_name, online_channel_url in online_channel_list:
                    for item in cur_list:
                        if item == online_channel_name:
                            matched_channels[category].setdefault(cur_channel_name, []).append(
                                online_channel_url
                            )

    return matched_channels

def is_ipv6(url):
    return re.match(r'^http:\[[0-9a-fA-F:]+]', url) is not None

def updateChannelUrlsM3U(channels, template_channels):
    written_urls = set()

    current_date = datetime.now().strftime("%Y-%m-%d")
    for group in config.announcements:
        for announcement in group["entries"]:
            if announcement["name"] is None:
                announcement["name"] = current_date

    with open("py/优质源/live.m3u", "w", encoding="utf-8") as f_m3u:
        f_m3u.write(
            f"""#EXTM3U x-tvg-url={",".join(f'"{epg_url}"' for epg_url in config.epg_urls)}\n"""
        )

        with open("py/优质源/live.txt", "w", encoding="utf-8") as f_txt:
            for group in config.announcements:
                f_txt.write(f"{group['channel']},#genre#\n")
                for announcement in group["entries"]:
                    f_m3u.write(
                        f"""#EXTINF:-1 tvg-id="1" tvg-name="{announcement['name']}" tvg-logo="{announcement['logo']}" group-title="{group['channel']}",{announcement['name']}\n"""
                    )
                    f_m3u.write(f"{announcement['url']}\n")
                    f_txt.write(f"{announcement['name']},{announcement['url']}\n")
            count = 0
            for category, channel_list in template_channels.items():
                f_txt.write(f"{category},#genre#\n")
                if category in channels:
                    for channel_name in channel_list:
                        channel_name = channel_name.split("|")[0]
                        if channel_name in channels[category]:
                            sorted_urls = sorted(
                                channels[category][channel_name],
                                key=lambda url: (
                                    not is_ipv6(url)
                                    if config.ip_version_priority == "ipv6"
                                    else is_ipv6(url)
                                ),
                            )
                            # sorted_urls = channels[category][channel_name]
                            filtered_urls = []
                            for url in sorted_urls:
                                if (
                                    url
                                    and url not in written_urls
                                    and not any(
                                        blacklist in url for blacklist in config.url_blacklist
                                    )
                                ):
                                    filtered_urls.append(url)
                                    written_urls.add(url)

                            total_urls = len(filtered_urls)
                            for index, url in enumerate(filtered_urls, start=1):
                                if is_ipv6(url):
                                    url_suffix = (
                                        f"$IPV6"  #LR•
                                        if total_urls == 1
                                        else f"$IPV6『线路{index}』"    #LR•{total_urls}•
                                    )
                                else:
                                    url_suffix = (
                                        f"$IPV4"   #LR•
                                        if total_urls == 1
                                        else f"$IPV4『线路{index}』"  #LR•{total_urls}•
                                    )
                                if "$" in url:
                                    base_url = url.split("$", 1)[0]
                                else:
                                    base_url = url

                                new_url = f"{base_url}{url_suffix}"

                                f_m3u.write(
                                    f'#EXTINF:-1 tvg-id="{index}" tvg-name="{channel_name}" tvg-logo="https://live.fanmingming.com/tv/{channel_name}.png" group-title="{category}",{channel_name}\n'
                                )
                                f_m3u.write(new_url + "\n")
                                f_txt.write(f"{channel_name},{new_url}\n")
                                count += 1

            f_txt.write("\n")
            logging.info(f"爬取完成✅，共计频道数：{count}")
            
            
    # 打开文档并读取所有行 
    with open('py/优质源/live.txt', 'r', encoding="utf-8") as file:
      lines = file.readlines()
    # 使用列表来存储唯一的行的顺序 
      unique_lines = [] 
      seen_lines = set() 
    # 遍历每一行，如果是新的就加入unique_lines 
    for line in lines:
        if line not in seen_lines:
          unique_lines.append(line)
          seen_lines.add(line)
    # 将唯一的行写入新的文档 
    with open('py/优质源/live1.txt', 'w', encoding="utf-8") as file:
        file.writelines(unique_lines)
    #os.remove("py/优质源/live1.txt")


if __name__ == "__main__":
    template_file = "py/优质源//demo.txt"
    channels, template_channels = filter_source_urls(template_file)
    updateChannelUrlsM3U(channels, template_channels)



