import requests
import os
import time
import concurrent.futures
from typing import List, Tuple, Dict, Set, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal
import sys

# 配置日志（只输出到控制台）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 组播流配置
CITY_STREAMS = {
    "安徽电信": ["udp/238.1.78.150:7072"],
    "北京市电信": ["rtp/225.1.8.21:8002"],
    "北京市联通": ["rtp/239.3.1.241:8000"],
    "江苏电信": ["rtp/239.49.8.138:6000"],
    "四川电信": ["udp/239.94.0.59:5140"],
    "四川移动": ["rtp/239.11.0.78:5140"],
    "四川联通": ["rtp/239.0.0.1:5140"],
    "上海市电信": ["rtp/233.18.204.51:5140"],
    "云南电信": ["rtp/239.200.200.145:8840"],
    "内蒙古电信": ["rtp/239.29.0.2:5000"],
    "吉林电信": ["rtp/239.37.0.125:5540"],
    "天津市电信": ["rtp/239.5.1.1:5000"],
    "天津市联通": ["rtp/225.1.1.111:5002"],
    "宁夏电信": ["rtp/239.121.4.94:8538"],
    "山东电信": ["udp/239.21.1.87:5002"],
    "山东联通": ["rtp/239.253.254.78:8000"],
    "山西电信": ["udp/239.1.1.1:8001"],
    "山西联通": ["rtp/226.0.2.152:9128"],
    "广东电信": ["udp/239.77.1.19:5146"],
    "广东移动": ["rtp/239.20.0.101:2000"],
    "广东联通": ["udp/239.0.1.1:5001"],
    "广西电信": ["udp/239.81.0.107:4056"],
    "新疆电信": ["udp/238.125.3.174:5140"],
    "江西电信": ["udp/239.252.220.63:5140"],
    "河北省电信": ["rtp/239.254.200.174:6000"],
    "河南电信": ["rtp/239.16.20.21:10210"],    
    "河南联通": ["rtp/225.1.4.98:1127"],
    "浙江电信": ["udp/233.50.201.100:5140"],
    "海南电信": ["rtp/239.253.64.253:5140"],
    "湖北电信": ["rtp/239.254.96.115:8664"],
    "湖北联通": ["rtp/228.0.0.60:6108"],
    "湖南电信": ["udp/239.76.253.101:9000"],
    "甘肃电信": ["udp/239.255.30.249:8231"],
    "福建省电信": ["rtp/239.61.2.132:8708"],
    "贵州电信": ["rtp/238.255.2.1:5999"],
    "辽宁联通": ["rtp/232.0.0.126:1234"],
    "重庆市电信": ["rtp/235.254.196.249:1268"],
    "重庆市联通": ["udp/225.0.4.187:7980"],
    "陕西电信": ["rtp/239.111.205.35:5140"],
    "青海电信": ["rtp/239.120.1.64:8332"],
    "黑龙江联通": ["rtp/229.58.190.150:5000"],
}

# 配置参数
CONFIG = {
    'timeout': 3,  # 超时时间
    'max_workers': 20,  # 最大并发线程数
    'chunk_size': 102400,  # 每次下载块大小
    'max_download_size': 1024 * 1024,  # 最大下载大小 1MB
    'ip_dir': 'py/fofa/ip',  # IP文件目录
    'max_retry_times': 2,  # 失败重试次数
}

# 信号处理
shutdown_flag = False
def signal_handler(signum, frame):
    global shutdown_flag
    shutdown_flag = True
    logger.info("收到停止信号，正在保存当前进度...")

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class IPManager:
    """IP管理器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.session = None
        self.stats = {
            'total_tested': 0,
            'successful': 0,
            'failed': 0,
            'cities_processed': 0
        }
        
    def get_session(self):
        """获取或创建requests session"""
        if self.session is None:
            self.session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=100,
                pool_maxsize=100
            )
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)
        return self.session
    
    def read_ip_file(self, filepath: str) -> List[str]:
        """读取IP文件"""
        ips = []
        if not os.path.exists(filepath):
            return ips
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 移除可能的速度信息
                        ip = line.split('#')[0].strip()
                        if ':' in ip:  # 确保是IP:PORT格式
                            ips.append(ip)
        except Exception as e:
            logger.error(f"读取文件 {filepath} 失败: {e}")
        
        return ips
    
    def write_ip_file(self, filepath: str, ips: List[str]):
        """写入IP文件"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                for ip in ips:
                    f.write(f"{ip}\n")
            return True
        except Exception as e:
            logger.error(f"写入文件 {filepath} 失败: {e}")
            return False
    
    def test_single_url(self, url: str, timeout: int = 3) -> Tuple[float, str]:
        """测试单个URL的速度"""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout, stream=True)
            
            if response.status_code != 200:
                return 0, f"HTTP {response.status_code}"
            
            # 下载一小段数据来计算速度
            downloaded = 0
            chunk_size = 102400
            max_size = 1024 * 1024  # 最多下载1MB
            
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    downloaded += len(chunk)
                
                if downloaded >= chunk_size * 10:  # 下载大约1000KB就够判断速度了
                    break
                
                if downloaded >= max_size:
                    break
            
            response.close()
            
            elapsed = time.time() - start_time
            if elapsed <= 0:
                return 0, "time error"
            
            speed_kbps = (downloaded / 1024) / elapsed
            return speed_kbps, ""
            
        except requests.exceptions.Timeout:
            return 0, "timeout"
        except Exception as e:
            return 0, str(e)
    
    def test_ip_with_streams(self, ip: str, streams: List[str]) -> tuple:
        """测试单个IP的所有流，返回是否成功、速度和使用的流地址"""
        ip_speed = 0
        used_stream = ""
        
        for stream in streams:
            if shutdown_flag:
                break
                
            url = f"http://{ip}/{stream}"
            speed, error = self.test_single_url(url, timeout=self.config['timeout'])
            
            if error:
                logger.debug(f"{ip} 测试失败: {error} (流: {stream})")
            else:
                ip_speed = speed
                used_stream = stream
                logger.info(f"{ip} 测试成功: {speed:.2f} KB/s (流: {stream})")
                return True, ip_speed, used_stream
        
        # 如果所有流都失败
        logger.info(f"{ip} 所有流测试失败")
        return False, 0, ""
    
    def process_city(self, city: str, streams: List[str]) -> dict:
        """处理单个城市/运营商的测试"""
        logger.info(f"开始处理: {city}")
        
        successful_ips = []  # 存储(ip, speed, stream)元组
        
        # 1. 首先测试上一次保存的result_ip文件
        result_file = os.path.join(self.config['ip_dir'], f"{city}_result_ip.txt")
        previous_fast_ips = self.read_ip_file(result_file)
        
        if previous_fast_ips:
            logger.info(f"找到上一次保存的result_ip文件: {len(previous_fast_ips)} 个IP")
            
            # 使用多线程测试上一次的IP
            with ThreadPoolExecutor(max_workers=min(self.config['max_workers'], len(previous_fast_ips))) as executor:
                future_to_ip = {executor.submit(self.test_ip_with_streams, ip, streams): ip for ip in previous_fast_ips}
                
                for future in concurrent.futures.as_completed(future_to_ip):
                    if shutdown_flag:
                        break
                        
                    ip = future_to_ip[future]
                    try:
                        success, speed, stream = future.result()
                        self.stats['total_tested'] += 1
                        
                        if success:
                            successful_ips.append((ip, speed, stream))
                            self.stats['successful'] += 1
                            logger.info(f"result_ip中的IP {ip} 仍然有效: {speed:.2f} KB/s")
                        else:
                            self.stats['failed'] += 1
                            logger.info(f"result_ip中的IP {ip} 已失效")
                            
                    except Exception as e:
                        logger.error(f"测试IP {ip} 时发生错误: {e}")
                        self.stats['failed'] += 1
        
        # 2. 读取原始IP文件进行测试
        ip_file = os.path.join(self.config['ip_dir'], f"{city}.txt")
        all_ips = self.read_ip_file(ip_file)
        
        if not all_ips:
            logger.warning(f"无原始IP地址: {ip_file}")
        else:
            logger.info(f"从原始文件读取到 {len(all_ips)} 个IP")
            
            # 排除已经在result_ip中测试过的IP
            already_tested_ips = {item[0] for item in successful_ips}
            new_ips_to_test = [ip for ip in all_ips if ip not in already_tested_ips]
            
            logger.info(f"需要测试的新IP: {len(new_ips_to_test)} 个")
            
            if new_ips_to_test and not shutdown_flag:
                failed_new_ips = []
                
                # 使用多线程测试新的IP
                with ThreadPoolExecutor(max_workers=min(self.config['max_workers'], len(new_ips_to_test))) as executor:
                    future_to_ip = {executor.submit(self.test_ip_with_streams, ip, streams): ip for ip in new_ips_to_test}
                    
                    for future in concurrent.futures.as_completed(future_to_ip):
                        if shutdown_flag:
                            break
                            
                        ip = future_to_ip[future]
                        try:
                            success, speed, stream = future.result()
                            self.stats['total_tested'] += 1
                            
                            if success:
                                successful_ips.append((ip, speed, stream))
                                self.stats['successful'] += 1
                                logger.info(f"新IP {ip} 测试成功: {speed:.2f} KB/s")
                            else:
                                failed_new_ips.append(ip)
                                self.stats['failed'] += 1
                                
                        except Exception as e:
                            logger.error(f"测试IP {ip} 时发生错误: {e}")
                            self.stats['failed'] += 1
                            failed_new_ips.append(ip)
                
                # 3. 从原始IP文件中删除失败的IP
                if failed_new_ips:
                    original_count = len(all_ips)
                    # 从原始IP列表中移除失败的IP
                    all_ips = [ip for ip in all_ips if ip not in failed_new_ips]
                    remaining_count = len(all_ips)
                    
                    if remaining_count > 0:
                        self.write_ip_file(ip_file, all_ips)
                        logger.info(f"{city} - 从原始文件中删除 {original_count - remaining_count} 个失败IP，剩余 {remaining_count} 个IP")
                    else:
                        # 如果所有IP都失败，保留原文件但写入注释
                        self.write_ip_file(ip_file, ["# 所有IP测试失败，请检查网络或重新扫描"])
                        logger.warning(f"{city} - 所有IP测试失败，文件已清空")
        
        # 4. 保存所有有效的IP到result_ip文件（按速度排序）
        os.makedirs(self.config['ip_dir'], exist_ok=True)
        
        if successful_ips:
            # 按速度排序
            successful_ips.sort(key=lambda x: x[1], reverse=True)
            
            # 写入result_ip文件
            with open(result_file, 'w', encoding='utf-8') as f:
                for ip, speed, stream in successful_ips:
                    f.write(f"{ip}\n")
            
            # 记录前5个最快IP
            for i, (ip, speed, stream) in enumerate(successful_ips[:5]):
                if i == 0:
                    logger.info(f"{city} - 最快IP: {ip} (速度: {speed:.2f} KB/s, 流: {stream})")
                elif i < 5:
                    logger.info(f"{city} - 第{i+1}快IP: {ip} (速度: {speed:.2f} KB/s)")
            
            logger.info(f"{city} - 结果已保存到 {result_file}: 共 {len(successful_ips)} 个有效IP")
        else:
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write(f"# {city} 无可用IP\n")
            logger.warning(f"{city} - 无可用IP，已保存空结果")
        
        self.stats['cities_processed'] += 1
        
        return {
            'city': city,
            'total_tested': len(previous_fast_ips) + (len(all_ips) if all_ips else 0),
            'valid_count': len(successful_ips),
            'best_speed': successful_ips[0][1] if successful_ips else 0
        }
    
    def print_summary(self):
        """打印统计摘要"""
        logger.info("=" * 50)
        logger.info("测试完成！")
        logger.info(f"已处理城市: {self.stats['cities_processed']}")
        logger.info(f"总测试IP数: {self.stats['total_tested']}")
        logger.info(f"成功IP数: {self.stats['successful']}")
        logger.info(f"失败IP数: {self.stats['failed']}")
        if self.stats['total_tested'] > 0:
            success_rate = (self.stats['successful'] / self.stats['total_tested']) * 100
            logger.info(f"成功率: {success_rate:.1f}%")
        logger.info("=" * 50)

def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("组播流IP测试工具启动")
    logger.info(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"配置: 超时={CONFIG['timeout']}s, 并发数={CONFIG['max_workers']}")
    logger.info("=" * 50)
    
    # 创建管理器
    ip_manager = IPManager(CONFIG)
    
    # 确保目录存在
    os.makedirs(CONFIG['ip_dir'], exist_ok=True)
    
    # 处理所有城市
    all_results = []
    for city, streams in CITY_STREAMS.items():
        if shutdown_flag:
            logger.info("收到停止信号，提前结束")
            break
            
        logger.info(f"处理城市: {city}")
        logger.info(f"流地址: {streams}")
        
        result = ip_manager.process_city(city, streams)
        all_results.append(result)
    
    # 打印摘要
    ip_manager.print_summary()
    
    # 打印各城市结果摘要
    if all_results:
        logger.info("\n各城市测试结果:")
        logger.info("-" * 80)
        logger.info(f"{'城市':<15} {'测试数':<8} {'有效数':<8} {'最快速度(KB/s)':<15}")
        logger.info("-" * 80)
        
        for result in all_results:
            logger.info(f"{result['city']:<15} {result['total_tested']:<8} "
                       f"{result['valid_count']:<8} {result['best_speed']:<15.2f}")
    
    logger.info("=" * 50)
    logger.info(f"结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        if shutdown_flag:
            logger.info("程序已安全停止")
        sys.exit(0)
