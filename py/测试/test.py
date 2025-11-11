import os
import re
import requests
import time
import concurrent.futures
import subprocess
from datetime import datetime, timezone, timedelta

# ===============================
# 配置区
FOFA_URLS = {
    "https://fofa.info/result?qbase64=InVkcHh5IiAmJiBjb3VudHJ5PSJDTiI%3D": "ip.txt",
    #"https://fofa.info/result?qbase64=InVkcHh5IiAmJiByZWdpb249IkFuaHVpIiAmJiBvcmc9IkNoaW5hbmV0IiAmJiBwcm90b2NvbD0iaHR0cCI%3D": "安徽ip.txt",
    #"https://fofa.info/result?qbase64=InVkcHh5IiAmJiByZWdpb249IkJlaWppbmciICYmIG9yZz0iQ0hJTkEgVU5JQ09NIENoaW5hMTY5IEJhY2tib25lIiAmJiBwcm90b2NvbD0iaHR0cCI%3D": "北京ip.txt"
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

IP_DIR = "py/测试/ip"

# 创建IP目录
if not os.path.exists(IP_DIR):
    os.makedirs(IP_DIR)

# IP 运营商判断（改进版）
def get_isp(ip):
    # 更准确的IP段匹配
    telecom_pattern = r"^(1\.|14\.|27\.|36\.|39\.|42\.|49\.|58\.|60\.|101\.|106\.|110\.|111\.|112\.|113\.|114\.|115\.|116\.|117\.|118\.|119\.|120\.|121\.|122\.|123\.|124\.|125\.|126\.|171\.|175\.|182\.|183\.|202\.|203\.|210\.|211\.|218\.|219\.|220\.|221\.|222\.)"
    unicom_pattern = r"^(42\.1[0-9]{0,2}|43\.|58\.|59\.|60\.|61\.|110\.|111\.|112\.|113\.|114\.|115\.|116\.|117\.|118\.|119\.|120\.|121\.|122\.|123\.|124\.|125\.|126\.|171\.8[0-9]|171\.9[0-9]|171\.1[0-9]{2}|175\.|182\.|183\.|210\.|211\.|218\.|219\.|220\.|221\.|222\.)"
    mobile_pattern = r"^(36\.|37\.|38\.|39\.1[0-9]{0,2}|42\.2|42\.3|47\.|106\.|111\.|112\.|113\.|114\.|115\.|116\.|117\.|118\.|119\.|120\.|121\.|122\.|123\.|124\.|125\.|126\.|134\.|135\.|136\.|137\.|138\.|139\.|150\.|151\.|152\.|157\.|158\.|159\.|170\.|178\.|182\.|183\.|184\.|187\.|188\.|189\.)"
    
    if re.match(telecom_pattern, ip):
        return "电信"
    elif re.match(unicom_pattern, ip):
        return "联通"
    elif re.match(mobile_pattern, ip):
        return "移动"
    else:
        return "未知"

# 获取IP地理信息
def get_ip_info(ip_port):
    try:
        ip = ip_port.split(":")[0]
        # 添加重试机制
        for attempt in range(3):
            try:
                res = requests.get(f"http://ip-api.com/json/{ip}?lang=zh-CN", 
                                  timeout=10, headers=HEADERS)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("status") == "success":
                        province = data.get("regionName", "未知")
                        isp = get_isp(ip)
                        return province, isp, ip_port
                break
            except requests.RequestException:
                if attempt == 2:  # 最后一次尝试失败
                    return None, None, ip_port
                time.sleep(1)
    except Exception:
        pass
    return None, None, ip_port

# 第一阶段：爬取和分类
def first_stage():
    all_ips = set()
    
    for url, filename in FOFA_URLS.items():
        print(f"📡 正在爬取 {filename} ...")
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            # 改进的正则表达式匹配
            urls_all = re.findall(r'<a href="http://(.*?)"', r.text)
            # 过滤出有效的IP:端口格式
            for u in urls_all:
                u = u.strip()
                if re.match(r'\d+\.\d+\.\d+\.\d+:\d+', u):
                    all_ips.add(u)
            print(f"✅ 从 {filename} 获取到 {len(urls_all)} 个IP")
        except Exception as e:
            print(f"❌ 爬取失败：{e}")
        time.sleep(3)
    
    print(f"🔍 总共获取到 {len(all_ips)} 个有效IP")
    
    # 使用多线程加速IP信息查询
    province_isp_dict = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ip = {executor.submit(get_ip_info, ip): ip for ip in all_ips}
        
        for future in concurrent.futures.as_completed(future_to_ip):
            province, isp, ip_port = future.result()
            if province and isp and isp != "未知":
                fname = f"{province}{isp}.txt"
                province_isp_dict.setdefault(fname, set()).add(ip_port)
    
    # 保存到文件
    for fname, ip_set in province_isp_dict.items():
        filepath = os.path.join(IP_DIR, fname)
        with open(filepath, 'w', encoding='utf-8') as f:
            for ip in ip_set:
                f.write(ip + '\n')
        print(f"💾 已保存 {len(ip_set)} 个IP到 {fname}")
    
    # 保存所有IP到总文件
    all_ip_file = os.path.join(IP_DIR, "all_ips.txt")
    with open(all_ip_file, 'w', encoding='utf-8') as f:
        for ip in all_ips:
            f.write(ip + '\n')
    print(f"💾 所有IP已保存到 {all_ip_file}")

# 主函数
if __name__ == "__main__":
    print("🚀 开始IP爬取和分类...")
    first_stage()
    print("✅ 任务完成！")
