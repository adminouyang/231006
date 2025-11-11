import os
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import socket
import re


class IPSpeedTester:
    def __init__(self, ip_folder="ip", template_folder="template", output_folder="IPTV", detected_folder="Detected",
                 test_timeout=8, download_size=1024 * 1000):  # 1000KB测试数据
        self.ip_folder = ip_folder
        self.template_folder = template_folder
        self.output_folder = output_folder
        self.detected_folder = detected_folder             
        self.test_timeout = test_timeout
        self.download_size = download_size

        # 城市到固定stream的映射
        self.city_streams = {
            "安徽电信": "rtp/238.1.79.27:4328",
            "北京市电信": "rtp/225.1.8.21:8002",
            "北京市联通": "rtp/239.3.1.241:8000",
            "江苏电信": "udp/239.49.8.19:9614",
            "四川电信": "udp/239.93.0.169:5140"
            "河南电信": "rtp/239.16.20.21:10210"
            "河北省电信": "rtp/239.254.200.174:6000"
            # 可以继续添加其他城市的映射
        }

        # 会话对象，支持连接复用
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        })

        # 确保输出文件夹存在
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.detected_folder, exist_ok=True)             

    def test_connection_speed(self, url, ip_port):
        """
        更准确的速度测试方法
        通过实际下载数据来测量速度
        """
        try:
            # 方法1: 测试连接建立时间（ping-like测试）
            start_connect = time.time()
            try:
                # 先测试基本的连接性
                ip, port = ip_port.split(':')
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((ip, int(port)))
                sock.close()
                connect_time = (time.time() - start_connect) * 1000  # 毫秒
            except:
                connect_time = 9999  # 连接失败

            # 方法2: 实际下载测试
            start_download = time.time()
            speed_kb = 0

            try:
                # 使用流式下载，只下载部分数据来测试速度
                response = self.session.get(
                    url,
                    timeout=self.test_timeout,
                    stream=True,
                    headers={'Range': f'bytes=0-{self.download_size - 1}'}
                )

                if response.status_code in [200, 206]:  # 200 OK 或 206 Partial Content
                    downloaded = 0
                    chunk_size = 8192  # 8KB chunks

                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:  # 过滤掉keep-alive的chunks
                            downloaded += len(chunk)
                            if downloaded >= self.download_size:
                                break

                    download_time = time.time() - start_download

                    if download_time > 0:
                        # 计算实际下载速度 (KB/s)
                        speed_kb = downloaded / 1024 / download_time
                    else:
                        speed_kb = 0

                    response.close()
                else:
                    return {
                        'ip_port': ip_port,
                        'url': url,
                        'speed': 0,
                        'speed_str': 'HTTP错误',
                        'connect_time': connect_time,
                        'status': 'failed'
                    }

            except requests.exceptions.Timeout:
                return {
                    'ip_port': ip_port,
                    'url': url,
                    'speed': 0,
                    'speed_str': '超时',
                    'connect_time': connect_time,
                    'status': 'timeout'
                }
            except Exception as e:
                return {
                    'ip_port': ip_port,
                    'url': url,
                    'speed': 0,
                    'speed_str': '连接错误',
                    'connect_time': connect_time,
                    'status': 'error'
                }

            # 格式化速度显示
            if speed_kb > 1024:
                speed_str = f"{speed_kb / 1024:.1f}MB/s"
            elif speed_kb > 0:
                speed_str = f"{speed_kb:.1f}KB/s"
            else:
                speed_str = "0KB/s"

            # 添加连接时间信息
            speed_str += f" (ping:{connect_time:.0f}ms)"

            return {
                'ip_port': ip_port,
                'url': url,
                'speed': speed_kb,
                'speed_str': speed_str,
                'connect_time': connect_time,
                'status': 'success'
            }

        except Exception as e:
            return {
                'ip_port': ip_port,
                'url': url,
                'speed': 0,
                'speed_str': '测试异常',
                'connect_time': 9999,
                'status': 'exception'
            }

    def advanced_speed_test(self, url, ip_port, retries=2):
        """
        高级速度测试：包含重试机制和多重测试
        """
        best_result = None

        for attempt in range(retries + 1):
            result = self.test_connection_speed(url, ip_port)

            # 如果是第一次成功的结果，或者比之前的结果更好
            if best_result is None or result['speed'] > best_result['speed']:
                best_result = result

            # 如果速度很好，不需要重试
            if result['speed'] > 500:  # 如果速度大于500KB/s，认为足够好
                break

            # 如果不是最后一次尝试，等待一下再重试
            if attempt < retries:
                time.sleep(1)

        return best_result

    def test_city_ips(self, city_name, max_workers=8):  # 减少并发数避免带宽竞争
        """测试指定城市的所有IP"""
        ip_file = os.path.join(self.ip_folder, f"{city_name}.txt")
        if not os.path.exists(ip_file):
            print(f"IP文件不存在: {ip_file}")
            return []

        # 读取IP列表
        with open(ip_file, 'r', encoding='utf-8') as f:
            ip_list = [line.strip() for line in f if line.strip()]

        if not ip_list:
            print(f"{city_name} 没有可用的IP地址")
            return []

        # 获取该城市的固定stream
        stream_path = self.city_streams.get(city_name)
        if not stream_path:
            print(f"未找到 {city_name} 的stream配置")
            return []

        print(f"开始测试 {city_name} 的 {len(ip_list)} 个IP...")
        print(f"测试URL模板: http://IP:PORT/{stream_path}")

        results = []
        successful_tests = 0

        # 使用线程池并发测试，但减少并发数
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ip = {}

            for ip_port in ip_list:
                # 构建测试URL
                test_url = f"http://{ip_port}/{stream_path}"
                future = executor.submit(self.advanced_speed_test, test_url, ip_port)
                future_to_ip[future] = ip_port

            # 收集结果
            completed = 0
            for future in as_completed(future_to_ip):
                completed += 1
                result = future.result()
                results.append(result)

                if result['status'] == 'success':
                    successful_tests += 1
                    status_icon = "✓"
                else:
                    status_icon = "✗"

                print(f"{status_icon} {city_name}: {completed}/{len(ip_list)} - "
                      f"{result['ip_port']} - {result['speed_str']}")

        # 按速度排序（从大到小）
        valid_results = [r for r in results if r['status'] == 'success']
        valid_results.sort(key=lambda x: (x['speed'], -x['connect_time']), reverse=True)  # 速度优先，连接时间其次

        # 保存详细结果到文件
        output_file = os.path.join(self.detected_folder, f"{city_name}_ip.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {city_name} IP速度测试结果 - 有效IP {len(valid_results)}/{len(ip_list)}\n")
            f.write(f"# 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# IP:端口 速度 连接时间(ms)\n")

            for result in valid_results:
                f.write(f"{result['ip_port']} \n#{result['speed_str']}\n")

            # 添加失败统计
            failed_results = [r for r in results if r['status'] != 'success']
            if failed_results:
                f.write(f"\n# 失败统计 ({len(failed_results)}个):\n")
                for result in failed_results[:10]:  # 只显示前10个失败项
                    f.write(f"# {result['ip_port']} - {result['speed_str']}\n")

        print(f"\n{city_name}: 成功 {successful_tests}/{len(ip_list)}，"
              f"平均速度: {sum(r['speed'] for r in valid_results) / max(len(valid_results), 1):.1f}KB/s")
        print(f"结果已保存到 {output_file}")

        return valid_results

    def generate_final_files(self):
        """生成最终的频道文件"""
        if not os.path.exists(self.detected_folder) or not os.path.exists(self.template_folder):
            print("Detected文件夹或template文件夹不存在")
            return

        # 获取所有城市文件
        city_files = [f for f in os.listdir(self.template_folder) if f.endswith('.txt')]
        cities = [os.path.splitext(f)[0] for f in city_files]

        for city in cities:
            # 读取最快的3个IP（从Detected文件夹）
            ip_result_file = os.path.join(self.detected_folder, f"{city}_ip.txt")
            if not os.path.exists(ip_result_file):
                print(f"未找到 {city} 的IP测试结果文件")
                continue

            # 读取IP结果文件，跳过注释行
            with open(ip_result_file, 'r', encoding='utf-8') as f:
                ip_lines = [line.strip() for line in f
                            if line.strip() and not line.startswith('#')]

            # 取前3个最快的IP（只取IP:端口部分）
            top_ips = []
            for line in ip_lines[:3]:
                parts = line.split()
                if parts:
                    top_ips.append(parts[0])

            if not top_ips:
                print(f"{city} 没有可用的IP")
                continue

            print(f"{city}: 使用最快IP - {', '.join(top_ips)}")

            # 读取RTP频道文件
            rtp_file = os.path.join(self.template_folder, f"{city}.txt")
            if not os.path.exists(rtp_file):
                print(f"未找到 {city} 的RTP文件")
                continue

            with open(rtp_file, 'r', encoding='utf-8') as f:
                rtp_lines = [line.strip() for line in f if line.strip()]

            # 生成最终文件内容 - 修改为每行一个链接
            output_lines = []
            output_lines.append(f"# {city} 频道列表 - 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            output_lines.append(f"# 使用IP: {', '.join(top_ips)}")
            output_lines.append("")

            for line in rtp_lines:
                if ',' in line:
                    parts = line.split(',', 1)
                    channel_name = parts[0].strip()
                    rtp_url = parts[1].strip()

                    # 从RTP URL中提取路径部分
                    if '://' in rtp_url:
                        path = rtp_url.split('://', 1)[1]
                    else:
                        path = rtp_url

                    # 为每个IP生成单独的HTTP URL行
                    for ip in top_ips:
                        http_url = f"http://{ip}/{path}"
                        output_line = f"{channel_name},{http_url}"
                        output_lines.append(output_line)

            # 保存最终文件
            output_file = os.path.join(self.output_folder, f"{city}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_lines))

            print(f"{city}: 已生成频道文件，包含 {len(output_lines)} 行链接")

    def run(self):
        """运行完整的处理流程"""
        print("=" * 50)
        print("开始IP有效性检测和速度测试...")
        print("=" * 50)

        start_time = time.time()

        # 处理所有城市
        if not os.path.exists(self.ip_folder):
            print(f"IP文件夹不存在: {self.ip_folder}")
            return

        city_files = [f for f in os.listdir(self.ip_folder)
                      if f.endswith('.txt') and not f.endswith('_ip.txt')]

        cities = [os.path.splitext(f)[0] for f in city_files]

        for city in cities:
            if city in self.city_streams:
                print(f"\n处理城市: {city}")
                self.test_city_ips(city)
                print("-" * 30)

        print("\n" + "=" * 50)
        print("开始生成最终频道文件...")
        print("=" * 50)

        self.generate_final_files()

        total_time = time.time() - start_time
        print(f"\n处理完成！总耗时: {total_time:.1f}秒")


def main():
    # 配置参数
    config = {
        'ip_folder': 'py/测试/ip',
        'template_folder': 'py/测试/template',
        'output_folder': 'py/测试/IPTV',
        'detected_folder': 'py/测试/Detected',
        'test_timeout': 8,  # 增加超时时间
        'max_workers': 6  # 减少并发数，避免带宽竞争
    }

    # 创建测试器并运行
    tester = IPSpeedTester(
        ip_folder=config['ip_folder'],
        template_folder=config['template_folder'],
        output_folder=config['output_folder'],
        detected_folder=config['detected_folder'],
        test_timeout=config['test_timeout']
    )

    try:
        tester.run()
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"程序执行出错: {e}")


if __name__ == "__main__":
    main()
