import urllib.request
from urllib.parse import urlparse
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import socket
import time
from datetime import datetime


# 读取文本方法
def read_txt_to_array(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            lines = [line.strip() for line in lines]
            return lines
    except FileNotFoundError:
        print(f"File '{file_name}' not found.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


# 准备支持 m3u 格式
def get_url_file_extension(url):
    # 解析 URL
    parsed_url = urlparse(url)
    # 获取路径部分
    path = parsed_url.path
    # 提取文件扩展名
    extension = os.path.splitext(path)[1]
    return extension


def convert_m3u_to_txt(m3u_content):
    # 分行处理
    lines = m3u_content.split('\n')
    txt_lines = []
    # 临时变量用于存储频道名称
    channel_name = ""
    for line in lines:
        # 过滤掉 #EXTM3U 开头的行
        if line.startswith("#EXTM3U"):
            continue
        # 处理 #EXTINF 开头的行
        if line.startswith("#EXTINF"):
            # 获取频道名称（假设频道名称在引号后）
            channel_name = line.split(',')[-1].strip()
        # 处理 URL 行
        elif line.startswith("http") or line.startswith("rtmp") or line.startswith("p3p"):
            txt_lines.append(f"{channel_name},{line.strip()}")
    # 将结果合并成一个字符串，以换行符分隔
    return '\n'.join(txt_lines)


# 处理带 $ 的 URL，把 $ 之后的内容都去掉（包括 $ 也去掉）
def clean_url(url):
    last_dollar_index = url.rfind('$')  # 安全起见找最后一个 $ 处理
    if last_dollar_index != -1:
        return url[:last_dollar_index]
    return url


# 处理所有 URL
def process_url(url, timeout=10):
    try:
        # 打开 URL 并读取内容
        start_time = time.time()
        with urllib.request.urlopen(url, timeout=timeout) as response:
            # 以二进制方式读取数据
            data = response.read()
            # 将二进制数据解码为字符串
            text = data.decode('utf-8')

            # 处理 m3u 和 m3u8，提取 channel_name 和 channel_address
            if get_url_file_extension(url) == ".m3u" or get_url_file_extension(url) == ".m3u8":
                text = convert_m3u_to_txt(text)

            # 逐行处理内容
            lines = text.split('\n')
            channel_count = 0  # 初始化频道计数器
            for line in lines:
                if "#genre#" not in line and "," in line and "://" in line:
                    # 拆分成频道名和 URL 部分
                    parts = line.split(',')
                    channel_name = parts[0]  # 获取频道名称
                    channel_address = parts[1]  # 获取频道地址
                    # 处理带 # 号源 = 予加速源
                    if "#" not in channel_address:
                        yield channel_name, clean_url(channel_address)  # 如果没有井号，则照常按照每行规则进行分发
                    else:
                        # 如果有 “#” 号，则根据 “#” 号分隔
                        url_list = channel_address.split('#')
                        for channel_url in url_list:
                            yield channel_name, clean_url(channel_url)
                    channel_count += 1  # 每处理一个频道，计数器加一

            print(f"正在读取URL: {url}")
            print(f"获取到频道列表: {channel_count} 条")  # 打印频道数量

    except Exception as e:
        print(f"处理 URL 时发生错误：{e}")
        return []


# 函数用于过滤和替换频道名称
def filter_and_modify_sources(corrections):
    filtered_corrections = []
    name_dict = ['购物', '理财', '导视', '指南', '测试', '芒果', 'CGTN']
    url_dict = []  # '2409:'留空不过滤ipv6频道

    for name, url in corrections:
        if any(word.lower() in name.lower() for word in name_dict) or any(word in url for word in url_dict):
            print("过滤频道:" + name + "," + url)
        else:
            # 进行频道名称的替换操作
            name = name.replace("FHD", "").replace("HD", "").replace("hd", "").replace("频道", "").replace("高清", "") \
                .replace("超清", "").replace("20M", "").replace("-", "").replace("4k", "").replace("4K", "") \
                .replace("4kR", "")
            filtered_corrections.append((name, url))
    return filtered_corrections


# 删除目录内所有 .txt 文件
def clear_txt_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"删除文件时发生错误: {e}")


# 主函数
def main():
    # 读取 URLs
    urls_file_path = os.path.join(os.getcwd(), 'config/urls.txt')
    urls = read_txt_to_array(urls_file_path)

    # 处理过滤和替换频道名称
    all_channels = []
    for url in urls:
        for channel_name, channel_url in process_url(url):
            all_channels.append((channel_name, channel_url))

    # 过滤和修改频道名称
    filtered_channels = filter_and_modify_sources(all_channels)

    # 去重
    unique_channels = list(set(filtered_channels))

    unique_channels_str = [f"{name},{url}" for name, url in unique_channels]

    # 写入 iptv.txt 文件
    iptv_file_path = os.path.join(os.getcwd(), 'iptv.txt')
    with open(iptv_file_path, 'w', encoding='utf-8') as f:
        for line in unique_channels_str:
            f.write(line + '\n')

    # 打印出本次写入iptv.txt文件的总频道列表数量
    with open(iptv_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        total_channels = len(lines)
        print(f"\n所有频道已保存到文件: {iptv_file_path}，共采集到频道数量: {total_channels} 条\n")

    def check_url(url, channel_name, timeout=6):
        start_time = time.time()
        elapsed_time = None
        success = False

        try:
            if url.startswith("http"):
                response = urllib.request.urlopen(url, timeout=timeout)
                if response.status == 200:
                    success = True
            elif url.startswith("p3p"):
                success = check_p3p_url(url, timeout)
            elif url.startswith("rtmp"):
                success = check_rtmp_url(url, timeout)
            elif url.startswith("rtp"):
                success = check_rtp_url(url, timeout)
            else:
                return None, False

            elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒
        except Exception as e:
            print(f"检测错误 {channel_name}: {url}: {e}")

        return elapsed_time, success

    # 以下是检测不同协议URL的函数
    def check_rtmp_url(url, timeout):
        try:
            result = subprocess.run(['ffprobe', '-v', 'error', '-rtmp_transport', 'tcp', '-i', url],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=timeout)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print(f"检测超时 {url}")
        except Exception as e:
            print(f"检测错误 {url}: {e}")
        return False

    def check_rtp_url(url, timeout):
        try:
            parsed_url = urlparse(url)
            host = parsed_url.hostname
            port = parsed_url.port

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(timeout)
                s.connect((host, port))
                s.sendto(b'', (host, port))
                s.recv(1)
            return True
        except (socket.timeout, socket.error):
            return False

    def check_p3p_url(url, timeout):
        try:
            parsed_url = urlparse(url)
            host = parsed_url.hostname
            port = parsed_url.port
            path = parsed_url.path

            with socket.create_connection((host, port), timeout=timeout) as s:
                request = f"GET {path} P3P/1.0\r\nHost: {host}\r\n\r\n"
                s.sendall(request.encode())
                response = s.recv(1024)
                return b"P3P" in response
        except Exception as e:
            print(f"检测错误 {url}: {e}")
        return False

    # 去掉文本'$'后面的内容
    def process_line(line):
        if "://" not in line:
            return None, None
        line = line.split('$')[0]
        parts = line.split(',')
        if len(parts) == 2:
            name, url = parts
            elapsed_time, is_valid = check_url(url.strip(), name)
            if is_valid:
                return elapsed_time, f"{name},{url}"
        return None, None

    def process_urls_multithreaded(lines, max_workers=200):
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_line, line): line for line in lines}
            for future in as_completed(futures):
                elapsed_time, result = future.result()
                if elapsed_time is not None:
                    results.append((elapsed_time, result))

        # 按照检测后的毫秒数升序排列
        results.sort()
        return results

    # 使用多线程检测URL
    results = process_urls_multithreaded(unique_channels_str)

    # 写入文件
    def write_list(file_path, data_list):
        with open(file_path, 'w', encoding='utf-8') as file:
            for item in data_list:
                elapsed_time, result = item
                channel_name, channel_url = result.split(',')
                file.write(f"{channel_name},{channel_url}\n")

    # 写入结果到文件
    iptv_speed_file_path = os.path.join(os.getcwd(), 'iptv_speed.txt')
    write_list(iptv_speed_file_path, results)

    # 打印结果
    for elapsed_time, result in results:
        channel_name, channel_url = result.split(',')
        print(f"检测成功  {channel_name},{channel_url}  响应时间 ：{elapsed_time:.0f} 毫秒")

    # 创建地方频道文件夹
    local_channels_directory = os.path.join(os.getcwd(), '地方频道')
    if not os.path.exists(local_channels_directory):
        os.makedirs(local_channels_directory)
        print(f"目录 '{local_channels_directory}' 已创建。")
    else:
        # 清空地方频道文件夹内所有的 .txt 文件
        clear_txt_files(local_channels_directory)

    # 遍历频道模板目录下的所有文件
    template_directory = os.path.join(os.getcwd(), '频道模板')
    if not os.path.exists(template_directory):
        os.makedirs(template_directory)
        print(f"目录 '{template_directory}' 已创建。")
    template_files = [f for f in os.listdir(template_directory) if f.endswith('.txt')]

    # 读取 iptv_speed.txt 文件中的频道列表
    iptv_speed_channels = read_txt_to_array(iptv_speed_file_path)

    # 对于每个模板文件，进行比对并写入结果
    for template_file in template_files:
        template_channels = read_txt_to_array(os.path.join(template_directory, template_file))
        template_name = os.path.splitext(template_file)[0]

        # 筛选出匹配的频道
        matched_channels = [channel for channel in iptv_speed_channels if
                            channel.split(',')[0] in template_channels]

        # 对 CCTV 频道进行排序
        def channel_key(channel_name):
            match = re.search(r'\d+', channel_name)
            if match:
                return int(match.group())
            else:
                return float('inf')  # 返回一个无穷大的数字作为关键字

        matched_channels.sort(key=lambda x: channel_key(x.split(',')[0]))
        matched_channels.sort(key=lambda x: channel_key(x[0]))

        # 写入对应地区命名的 _iptv.txt 文件中，保存在地方频道文件夹中
        output_file_path = os.path.join(local_channels_directory, f"{template_name}_iptv.txt")
        with open(output_file_path, 'w', encoding='utf-8') as f:
            # 写入标题行
            f.write(f"{template_name},#genre#\n")
            for channel in matched_channels:
                f.write(channel + '\n')
        print(f"频道列表已写入: {template_name}_iptv.txt")

    # 合并所有 _iptv.txt 文件
    def merge_iptv_files():
        merged_content = ""
        # 获取所有 _iptv.txt 文件的路径
        iptv_files = [f for f in os.listdir(local_channels_directory) if f.endswith('_iptv.txt')]
        # 确定央视频道和卫视频道的文件名
        central_channel_file = "央视频道_iptv.txt"
        satellite_channel_file = "卫视频道_iptv.txt"
        hunan_channel_file = "湖南频道_iptv.txt"
        hk_taiwan_channel_file = "港台频道_iptv.txt"
        # 创建一个有序的文件列表
        ordered_files = [central_channel_file, satellite_channel_file, hunan_channel_file, hk_taiwan_channel_file]

        # 按照指定的顺序合并文件内容
        for file_name in ordered_files:
            if file_name in iptv_files:
                file_path = os.path.join(local_channels_directory, file_name)
                with open(file_path, "r", encoding="utf-8") as file:
                    merged_content += file.read() + "\n"
                iptv_files.remove(file_name)

        # 添加剩余的频道
        for file_name in sorted(iptv_files):
            file_path = os.path.join(local_channels_directory, file_name)
            with open(file_path, "r", encoding="utf-8") as file:
                merged_content += file.read() + "\n"
        # 获取当前时间
        now = datetime.now()
        update_time_line = f"更新时间,#genre#\n{now.strftime('%Y-%m-%d')},url\n{now.strftime('%H:%M:%S')},url\n"

        # 将合并后的内容写入 iptv_list.txt 文件
        iptv_list_file_path = "iptv_list.txt"
        with open(iptv_list_file_path, "w", encoding="utf-8") as iptv_list_file:
            iptv_list_file.write(update_time_line)
            # 对每个频道名称的频道列表进行分组
            channels_grouped = {}
            for line in merged_content.split('\n'):
                if line:
                    parts = line.split(',')
                    channel_name = parts[0]
                    channel_url = parts[1]
                    if channel_name not in channels_grouped:
                        channels_grouped[channel_name] = []
                    channels_grouped[channel_name].append(line)

            # 只保留每个分组的前20个频道
            for channel_name in channels_grouped:
                channels_grouped[channel_name] = channels_grouped[channel_name][:200]

            # 将处理后的频道列表写入文件
            for channel_name in channels_grouped:
                for channel_line in channels_grouped[channel_name]:
                    iptv_list_file.write(channel_line + '\n')

        # 删除临时文件 iptv.txt 和 iptv_speed.txt
        try:
            os.remove('iptv.txt')
            os.remove('iptv_speed.txt')
            print(f"临时文件 iptv.txt 和 iptv_speed.txt 已删除。")
        except OSError as e:
            print(f"删除临时文件时发生错误: {e}")

        print(f"\n所有地区频道列表文件合并完成，文件保存为：{iptv_list_file_path}")
    # 调用合并文件的函数
    merge_iptv_files()


if __name__ == "__main__":
    main()
