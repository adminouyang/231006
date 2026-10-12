#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPTV组播源爬虫 - 地区提取修复版 (端口修正版 v3)
功能：
  1. 从 tonkiang.us 提取 IP 和地区（优先从详情页获取）
  2. 支持多页爬取（默认2页）
  3. 访问 getall26.php 页面提取端口，自动跳过失效源
  4. 输出合并文件 ips.txt，格式: IP:端口$地区
  5. 去重规则：地区相同时，IP前两段+端口相同则去重
用法：
  python iptv_crawler.py                     # 完整爬取（2页）
  python iptv_crawler.py --pages 5           # 爬取5页
  python iptv_crawler.py --update-ports summary.json   # 回填端口
"""

import re
import os
import time
import json
import html as html_mod
import argparse
from urllib.parse import urljoin, urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup


def clean_region(region):
    """清理地区字段，去除IP、括号等无效字符"""
    if not region:
        return "未知地区"
    if re.match(r"^\d+\.\d+\.\d+\.\d+$", region):
        return "未知地区"
    cleaned = re.sub(r"[\(（]?\d+\.\d+\.\d+\.\d+(:\d+)?[\)）]?", "", region).strip()
    cleaned = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9\s]", "", cleaned).strip()
    return cleaned or "未知地区"


def get_ip_prefix(ip):
    """提取IP地址的前两段，如 '117.8'"""
    parts = ip.split('.')
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return ip


class IPTVProxyCrawler:
    def __init__(self, base_url="https://tonkiang.us", delay=0.5):
        self.base_url = base_url
        self.delay = delay
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        })
        self._last_request_time = 0
        self._debug_dir = None

    def _get(self, url, referer=None):
        """带礼貌延迟的GET请求，强制UTF-8解码"""
        wait = self.delay - (time.time() - self._last_request_time)
        if wait > 0:
            time.sleep(wait)
        self._last_request_time = time.time()

        headers = {"Referer": referer} if referer else {}
        try:
            resp = self._session.get(url, timeout=15, headers=headers)
        except requests.RequestException as e:
            print(f"请求异常: {url} -> {e}")
            return None

        if resp.status_code != 200:
            print(f"请求失败: {url} -> {resp.status_code}")
            return None

        try:
            text = resp.content.decode("utf-8")
        except UnicodeDecodeError:
            text = resp.content.decode("gbk", errors="replace")
            print("警告: UTF-8解码失败，已尝试GBK")

        if self._debug_dir:
            os.makedirs(self._debug_dir, exist_ok=True)
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', url[:80])
            with open(os.path.join(self._debug_dir, safe_name + ".html"), "w", encoding="utf-8") as f:
                f.write(text)

        return text

    @staticmethod
    def _is_invalid_page(html_text):
        invalid_keywords = ["暂时失效", "源暂时失效", "的源暂时失效"]
        return any(kw in html_text for kw in invalid_keywords)

    def extract_region_from_getall(self, html_text):
        """从 getall26.php 页面中提取地区信息（如 '天津联通'）"""
        soup = BeautifulSoup(html_text, "html.parser")
        result_div = soup.find("div", class_="result")
        if result_div:
            b_tag = result_div.find("b")
            if b_tag:
                text = b_tag.get_text(strip=True)
                if text:
                    return text
        return None

    def extract_ip_links(self, html_content):
        """
        提取IP链接及地区，构造 getall26.php 的完整 URL。
        """
        soup = BeautifulSoup(html_content, "html.parser")
        ip_links = []

        for div in soup.find_all("div", class_="result"):
            a = div.find("a", href=re.compile(r"channellist\.html\?ip="))
            if not a or "href" not in a.attrs:
                continue
            href = a["href"]
            parsed = urlparse(href)
            params = parse_qs(parsed.query)
            ip = params.get("ip", [None])[0]
            tk = params.get("tk", [None])[0]
            p = params.get("p", [None])[0]
            if not ip:
                continue

            query_parts = [f"ip={ip}"]
            if tk:
                query_parts.append(f"tk={tk}")
            if p:
                query_parts.append(f"p={p}")
            new_query = "&".join(query_parts)
            full_url = f"{self.base_url}/getall26.php?{new_query}"

            region = ""
            b_tag = div.find("b")
            if b_tag:
                b_text = b_tag.get_text(strip=True)
                region = clean_region(b_text)

            if not region or region == "未知地区":
                i_tag = div.find("i")
                if i_tag:
                    i_text = i_tag.get_text(strip=True)
                    m = re.search(r"组播源\s*([^\s<>（）()]+)", i_text)
                    if m:
                        region = clean_region(m.group(1))

            if not region or region == "未知地区":
                div_text = div.get_text(strip=True)
                m = re.search(r"来自([^\s<>()（）]+?)(?:的组播源|的源|的组播)", div_text)
                if m:
                    region = clean_region(m.group(1))

            if not region:
                region = "未知地区"

            ip_links.append({
                "ip": ip,
                "region": region,
                "full_url": full_url,
                "relative_url": href,
            })

        return ip_links

    def extract_ports_from_getall(self, html_text):
        """从 getall26.php 返回的页面中提取端口"""
        decoded = html_mod.unescape(html_text)
        ports = set()

        for m in re.finditer(r"http://\d+\.\d+\.\d+\.\d+:(\d{2,5})/", decoded):
            ports.add(int(m.group(1)))

        if not ports:
            for m in re.finditer(r"\((\d+\.\d+\.\d+\.\d+):(\d{2,5})\)", decoded):
                ports.add(int(m.group(2)))

        if not ports:
            for token in re.findall(r"(?<!\d)(\d{4,5})(?!\d)", decoded):
                p = int(token)
                if 1024 <= p <= 65535:
                    ports.add(p)

        return sorted(ports)

    def fetch_channel_page(self, ip_info):
        url = ip_info["full_url"]
        referer = self.base_url + "/iptvmulticast.php"

        ports = []
        status = "error"
        region = ip_info["region"]

        for attempt in range(2):
            html_text = self._get(url, referer=referer)
            if html_text is None:
                print(f"第{attempt+1}次请求失败: {ip_info['ip']}")
                time.sleep(1)
                continue

            if self._is_invalid_page(html_text):
                print(f"跳过失效源: {ip_info['ip']}")
                status = "invalid"
                break

            ports = self.extract_ports_from_getall(html_text)
            # 从详情页提取更准确的地区
            new_region = self.extract_region_from_getall(html_text)
            if new_region:
                region = clean_region(new_region)

            if ports:
                status = "valid"
                break
            else:
                print(f"第{attempt+1}次未提取到端口，重试: {ip_info['ip']}")
                time.sleep(1)
                continue
        else:
            if not ports:
                print(f"无法获取端口: {ip_info['ip']} (两次尝试均失败或无端口)")
                status = "invalid"

        return {
            "ip": ip_info["ip"],
            "region": region,
            "ports": ports,
            "source_url": url,
            "status": status,
        }

    def crawl_all_ips(self, ip_links, max_workers=3):
        """处理所有IP链接，返回结果列表"""
        print(f"开始处理 {len(ip_links)} 个IP")
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.fetch_channel_page, info): info
                for info in ip_links
            }
            for f in as_completed(futures):
                result = f.result()
                results.append(result)
                print(f"完成: {result['ip']} -> 端口 {result['ports']} 地区 {result['region']}")
        return results

    def save_results(self, results, output_dir="py/udpxy/iptv_udp_results"):
        """保存结果，应用去重规则"""
        os.makedirs(output_dir, exist_ok=True)

        # 去重规则：地区相同且IP前两段+端口相同则去重
        seen = set()
        deduped_items = []
        for item in results:
            if item.get("status") != "valid" or not item["ports"]:
                continue
            region = clean_region(item["region"]) or "未知地区"
            ip_prefix = get_ip_prefix(item["ip"])
            for port in item["ports"]:
                key = (region, ip_prefix, port)
                if key not in seen:
                    seen.add(key)
                    deduped_items.append((item["ip"], port, region))

        ips_path = os.path.join(output_dir, "ips.txt")
        with open(ips_path, "w", encoding="utf-8") as f:
            for ip, port, region in deduped_items:
                f.write(f"{ip}:{port}${region}\n")
        print(f"有效端口已保存: {ips_path} ({len(deduped_items)} 条记录，去重后)")

        summary = {
            "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_ips": len(results),
            "valid_ips": len(deduped_items),
            "results": results,
        }
        summary_path = os.path.join(output_dir, "summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"汇总已保存: {summary_path}")

    def update_ports_from_summary(self, summary_path, output_path=None):
        """从已有summary.json回填端口"""
        with open(summary_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        new_results = []
        for idx, item in enumerate(data["results"]):
            print(f"[{idx+1}/{len(data['results'])}] 处理 {item['ip']}")
            old_url = item.get("source_url", "")
            if "channellist.html" in old_url:
                new_url = old_url.replace("channellist.html", "getall26.php")
                item["full_url"] = new_url
            else:
                item["full_url"] = old_url
            result = self.fetch_channel_page(item)
            new_results.append(result)
            time.sleep(1)

        data["results"] = new_results
        data["update_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        out = output_path or summary_path
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"更新完成: {out}")

        # 回填后同样应用去重规则
        valid_items = [r for r in new_results if r.get("status") == "valid" and r["ports"]]
        seen = set()
        lines = []
        for item in valid_items:
            region = clean_region(item["region"]) or "未知地区"
            ip_prefix = get_ip_prefix(item["ip"])
            for port in item["ports"]:
                key = (region, ip_prefix, port)
                if key not in seen:
                    seen.add(key)
                    lines.append(f"{item['ip']}:{port}${region}\n")

        ips_path = os.path.join(os.path.dirname(out), "ips.txt")
        with open(ips_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"ips.txt 已更新: {ips_path} ({len(lines)} 条)")


def main():
    parser = argparse.ArgumentParser(description="IPTV组播源爬虫 - 多页 + 去重版")
    parser.add_argument("--output", default="py/udpxy/iptv_udp_results")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--delay", type=float, default=1.0, help="请求间隔秒数")
    parser.add_argument("--pages", type=int, default=2, help="爬取页数（默认2页）")
    parser.add_argument("--update-ports", metavar="summary.json", help="从已有summary.json回填端口")
    parser.add_argument("--debug", action="store_true", help="保存每个页面HTML到debug_html/")
    args = parser.parse_args()

    crawler = IPTVProxyCrawler(delay=args.delay)
    if args.debug:
        crawler._debug_dir = "debug_html"

    if args.update_ports:
        crawler.update_ports_from_summary(args.update_ports)
        return

    # 多页爬取
    all_ip_links = []
    for page in range(1, args.pages + 1):
        if page == 1:
            url = "https://tonkiang.us/iptvmulticast.php"
        else:
            url = f"https://tonkiang.us/iptvmulticast.php?page={page}"
        print(f"\n--- 正在获取第 {page} 页: {url} ---")
        html_text = crawler._get(url)
        if not html_text:
            print(f"第 {page} 页获取失败，跳过")
            continue
        ip_links = crawler.extract_ip_links(html_text)
        print(f"第 {page} 页找到 {len(ip_links)} 个IP")
        all_ip_links.extend(ip_links)
        time.sleep(1)  # 页间延迟

    # 去重IP链接（基于IP+region初步去重，避免重复抓取）
    unique_links = {}
    for link in all_ip_links:
        key = (link["ip"], link["region"])
        if key not in unique_links:
            unique_links[key] = link
    all_ip_links = list(unique_links.values())
    print(f"\n合并后共 {len(all_ip_links)} 个唯一IP")

    if not all_ip_links:
        print("未获取到任何IP")
        return

    results = crawler.crawl_all_ips(all_ip_links, max_workers=args.workers)
    if results:
        crawler.save_results(results, args.output)
    else:
        print("未获取到任何有效结果")


if __name__ == "__main__":
    main()
