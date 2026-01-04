#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPG数据下载和合并脚本
从epg.txt读取EPG源地址，按demo.txt中的频道名称排序，输出为指定格式的epg.xml
"""

import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO
import os
import json
import time
import re
from datetime import datetime
import urllib3
from collections import defaultdict

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def read_epg_sources(file_path='py/TV/EPG/epg.txt'):
    """从文件读取EPG订阅源地址"""
    sources = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    sources.append(line)
        print(f"✓ 从 {file_path} 读取到 {len(sources)} 个EPG源")
        return sources
    except Exception as e:
        print(f"✗ 读取EPG源文件失败: {str(e)}")
        return []


def read_channel_names_template(template_file='py/TV/EPG/demo.txt'):
    """从模板文件读取频道名称列表"""
    channel_names = []
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    channel_names.append(line)

        print(f"✓ 从 {template_file} 读取到 {len(channel_names)} 个频道名称模板")
        return channel_names
    except FileNotFoundError:
        print(f"✗ 模板文件 {template_file} 不存在")
        return []
    except Exception as e:
        print(f"✗ 读取模板文件失败: {str(e)}")
        return []


def download_epg_data(url, timeout=30):
    """下载EPG数据"""
    try:
        print(f"正在下载: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/xml,application/x-gzip,*/*',
            'Accept-Encoding': 'gzip, deflate',
        }

        response = requests.get(url, headers=headers, timeout=timeout, verify=False)
        response.raise_for_status()

        print(f"✓ 下载成功: {len(response.content)} 字节")
        return response.content
    except Exception as e:
        print(f"✗ 下载失败: {str(e)}")
        return None


def decompress_content(content, url):
    """解压内容（如果是gzip压缩）"""
    try:
        if url.endswith('.gz') or (len(content) >= 2 and content[:2] == b'\x1f\x8b'):
            print("  检测到GZIP压缩，正在解压...")
            with gzip.GzipFile(fileobj=BytesIO(content)) as gz_file:
                decompressed = gz_file.read()
            print(f"  解压完成: {len(decompressed)} 字节")
            return decompressed
        else:
            return content
    except Exception as e:
        print(f"✗ 解压失败: {str(e)}")
        return content


def normalize_channel_name(name):
    """标准化频道名称以便比较"""
    if not name:
        return ""
    # 移除空格、标点，转换为小写
    name = name.lower()
    # 移除常见的标点符号和空格
    name = re.sub(r'[-\s_—]', '', name)
    # 处理常见的中英文差异
    name = name.replace('cctv', 'cctv')
    name = name.replace('央视', 'cctv')
    return name


def parse_epg_data(xml_content, template_names):
    """解析EPG数据，提取频道和节目信息"""
    channels = []  # 列表，每个元素是 (channel_id, display_name, normalized_name)
    programmes = defaultdict(list)  # channel_id -> [programmes]
    name_to_channel_map = {}  # 标准化名称 -> channel_info

    try:
        # 清理XML内容
        xml_str = xml_content.decode('utf-8', errors='ignore')
        xml_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', xml_str)

        # 解析XML
        root = ET.fromstring(xml_str.encode('utf-8'))

        # 提取频道信息
        for channel_elem in root.findall('.//channel'):
            channel_id = channel_elem.get('id')
            if not channel_id:
                continue

            # 获取频道名称
            display_name = None
            display_name_elem = channel_elem.find('display-name')
            if display_name_elem is not None and display_name_elem.text:
                display_name = display_name_elem.text.strip()

            if not display_name:
                continue

            # 标准化名称用于匹配
            normalized_name = normalize_channel_name(display_name)

            # 检查是否在模板中
            in_template = any(normalize_channel_name(template_name) == normalized_name
                              for template_name in template_names)

            channels.append({
                'id': channel_id,
                'name': display_name,
                'normalized': normalized_name,
                'in_template': in_template
            })

            # 建立名称到频道的映射
            if normalized_name not in name_to_channel_map:
                name_to_channel_map[normalized_name] = []
            name_to_channel_map[normalized_name].append({
                'id': channel_id,
                'name': display_name
            })

        # 提取节目信息
        for prog_elem in root.findall('.//programme'):
            channel_id = prog_elem.get('channel')
            start_time = prog_elem.get('start')
            stop_time = prog_elem.get('stop')

            if not all([channel_id, start_time, stop_time]):
                continue

            # 标准化时间格式
            start_norm = normalize_time(start_time)
            stop_norm = normalize_time(stop_time)

            if not start_norm or not stop_norm:
                continue

            # 获取节目标题
            title = None
            title_elem = prog_elem.find('title')
            if title_elem is not None and title_elem.text:
                title = title_elem.text.strip()

            if not title:
                continue

            # 添加到节目列表
            programmes[channel_id].append({
                'start': start_norm,
                'stop': stop_norm,
                'title': title
            })

        print(f"  解析到 {len(channels)} 个频道，总计 {sum(len(progs) for progs in programmes.values())} 个节目")
        return channels, programmes, name_to_channel_map

    except Exception as e:
        print(f"✗ 解析EPG数据失败: {str(e)}")
        return [], defaultdict(list), {}


def normalize_time(time_str):
    """标准化时间格式为: YYYYMMDDHHMMSS +0800"""
    if not time_str:
        return None

    # 如果已经是标准格式
    if re.match(r'^\d{14} [+-]\d{4}$', time_str):
        return time_str

    # 尝试提取数字
    nums = re.findall(r'\d+', time_str)
    if len(nums) >= 6:
        year = nums[0].zfill(4)[:4]
        month = nums[1].zfill(2)[:2] if len(nums) > 1 else '01'
        day = nums[2].zfill(2)[:2] if len(nums) > 2 else '01'
        hour = nums[3].zfill(2)[:2] if len(nums) > 3 else '00'
        minute = nums[4].zfill(2)[:2] if len(nums) > 4 else '00'
        second = nums[5].zfill(2)[:2] if len(nums) > 5 else '00'

        return f"{year}{month}{day}{hour}{minute}{second} +0800"

    return None


def find_best_match_channel(template_name, name_to_channel_map, used_channel_ids):
    """为模板名称找到最佳匹配的频道"""
    template_normalized = normalize_channel_name(template_name)

    # 首先尝试精确匹配
    if template_normalized in name_to_channel_map:
        for channel in name_to_channel_map[template_normalized]:
            if channel['id'] not in used_channel_ids:
                return channel

    # 然后尝试模糊匹配（模板名称是频道名称的一部分）
    for normalized_name, channels in name_to_channel_map.items():
        if template_normalized in normalized_name or normalized_name in template_normalized:
            for channel in channels:
                if channel['id'] not in used_channel_ids:
                    return channel

    # 最后尝试部分匹配
    for normalized_name, channels in name_to_channel_map.items():
        # 检查是否有共同的部分
        template_parts = set(re.findall(r'[a-z0-9]+', template_normalized))
        channel_parts = set(re.findall(r'[a-z0-9]+', normalized_name))

        if template_parts.intersection(channel_parts):
            for channel in channels:
                if channel['id'] not in used_channel_ids:
                    return channel

    return None


def merge_and_sort_by_template(channels, programmes, template_names):
    """按照模板频道名称合并和排序数据"""
    sorted_channels = []
    used_channel_ids = set()

    # 建立名称到频道的映射
    name_to_channel_map = {}
    for channel in channels:
        if channel['normalized'] not in name_to_channel_map:
            name_to_channel_map[channel['normalized']] = []
        name_to_channel_map[channel['normalized']].append({
            'id': channel['id'],
            'name': channel['name']
        })

    # 按照模板顺序添加频道
    for template_name in template_names:
        matched_channel = find_best_match_channel(template_name, name_to_channel_map, used_channel_ids)
        if matched_channel:
            sorted_channels.append((matched_channel['id'], matched_channel['name']))
            used_channel_ids.add(matched_channel['id'])
            print(f"  ✓ 匹配: {template_name} -> {matched_channel['name']} (ID: {matched_channel['id']})")
        else:
            print(f"  ✗ 未找到匹配: {template_name}")

    # 添加剩余的频道
    remaining_channels = []
    for channel in channels:
        if channel['id'] not in used_channel_ids:
            remaining_channels.append((channel['id'], channel['name']))

    # 对剩余频道按名称排序
    remaining_channels.sort(key=lambda x: x[1])
    sorted_channels.extend(remaining_channels)

    # 对每个频道的节目按开始时间排序
    for channel_id in programmes:
        programmes[channel_id].sort(key=lambda x: x['start'])

    print(f"✓ 排序完成: {len(sorted_channels)} 个频道")
    return sorted_channels, programmes


def create_output_xml(sorted_channels, programmes, output_file='epg.xml'):
    """创建符合格式要求的XML输出"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入XML声明和根元素
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')

            # 写入频道信息
            # for channel_id, display_name in sorted_channels:
            #     f.write(f'<channel id="{channel_id}">')
            #     f.write(f'<display-name lang="zh">{display_name}</display-name>')
            #     f.write('</channel>')

            # 写入节目信息
            for channel_id, display_name in sorted_channels:
                f.write(f'<channel id="{channel_id}">\n')
                f.write(f'<display-name lang="zh">{display_name}</display-name>\n')
                f.write('</channel>\n')
                if channel_id in programmes:
                    for prog in programmes[channel_id]:
                        f.write(f'<programme channel="{display_name}" start="{prog["start"]}" stop="{prog["stop"]}" channel="{channel_id}">\n')
                        f.write(f'<title lang="zh">{prog["title"]}</title>\n')
                        f.write('</programme>\n')

            # 关闭根元素
            f.write('</tv>')

        file_size = os.path.getsize(output_file)
        print(f"✓ XML文件已保存: {output_file}")
        print(f"  文件大小: {file_size:,} 字节 ({file_size / 1024 / 1024:.2f} MB)")

        return True
    except Exception as e:
        print(f"✗ 保存XML文件失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("EPG数据下载和合并工具 (按频道名称排序)")
    print("=" * 60)

    # 1. 读取频道名称模板
    template_names = read_channel_names_template('py/TV/EPG/demo.txt')

    if not template_names:
        print("✗ 无法读取频道名称模板，程序退出")
        return

    # 显示前10个模板名称
    print(f"模板频道 (前10个): {', '.join(template_names[:10])}{'...' if len(template_names) > 10 else ''}")

    # 2. 读取EPG源列表
    epg_sources = read_epg_sources('py/TV/EPG/epg.txt')

    if not epg_sources:
        print("ℹ 使用默认EPG源")
        epg_sources = [
            "https://e.erw.cc/all.xml.gz",
            #"http://epg.51zmt.top:8000/api/all.xml"
        ]

    all_channels_list = []
    all_programmes_list = []
    all_name_maps = []

    # 3. 下载并解析每个EPG源
    for i, source_url in enumerate(epg_sources, 1):
        print(f"\n[{i}/{len(epg_sources)}] 处理源: {source_url}")

        # 下载数据
        content = download_epg_data(source_url)
        if not content:
            print(f"⚠ 跳过此源: {source_url}")
            continue

        # 解压（如果需要）
        decompressed = decompress_content(content, source_url)
        if not decompressed:
            print(f"⚠ 解压失败: {source_url}")
            continue

        # 解析EPG数据
        channels, programmes, name_map = parse_epg_data(decompressed, template_names)
        if channels or programmes:
            all_channels_list.append(channels)
            all_programmes_list.append(programmes)
            all_name_maps.append(name_map)
        else:
            print(f"⚠ 未提取到有效数据: {source_url}")

        # 避免请求过快
        if i < len(epg_sources):
            time.sleep(1)

    # 检查是否获取到数据
    if not all_channels_list and not all_programmes_list:
        print("\n✗ 错误: 未能从任何源获取有效数据")
        return

    # 4. 合并数据
    print("\n" + "=" * 60)
    print("合并EPG数据...")

    # 合并所有源的数据
    merged_channels = []
    merged_programmes = defaultdict(list)
    merged_name_map = {}

    for channels, programmes, name_map in zip(all_channels_list, all_programmes_list, all_name_maps):
        # 合并频道
        existing_ids = {channel['id'] for channel in merged_channels}
        for channel in channels:
            if channel['id'] not in existing_ids:
                merged_channels.append(channel)
                existing_ids.add(channel['id'])

        # 合并节目
        for channel_id, prog_list in programmes.items():
            if channel_id not in merged_programmes:
                merged_programmes[channel_id] = []

            # 去重：按开始时间和标题去重
            existing_keys = set()
            for prog in merged_programmes[channel_id]:
                existing_keys.add(f"{prog['start']}_{prog['title']}")

            for prog in prog_list:
                key = f"{prog['start']}_{prog['title']}"
                if key not in existing_keys:
                    merged_programmes[channel_id].append(prog)
                    existing_keys.add(key)

        # 合并名称映射
        for normalized_name, channels_list in name_map.items():
            if normalized_name not in merged_name_map:
                merged_name_map[normalized_name] = []
            for channel in channels_list:
                if channel['id'] not in {c['id'] for c in merged_name_map[normalized_name]}:
                    merged_name_map[normalized_name].append(channel)

    # 5. 按模板排序
    print("\n" + "=" * 60)
    print("按模板频道名称排序...")
    sorted_channels, final_programmes = merge_and_sort_by_template(merged_channels, merged_programmes, template_names)

    if not sorted_channels:
        print("✗ 错误: 合并后没有频道数据")
        return

    # 6. 生成输出XML
    print("\n" + "=" * 60)
    print("生成XML文件...")
    if create_output_xml(sorted_channels, final_programmes, 'py/TV/EPG/epg.xml'):
        print("\n" + "=" * 60)
        print("✓ 处理完成!")
        print(f"   输出文件: epg.xml")
        print(f"   频道数量: {len(sorted_channels)}")

        # 统计匹配模板的情况
        matched_count = 0
        for template_name in template_names:
            for channel_id, channel_name in sorted_channels[:len(template_names)]:
                if normalize_channel_name(template_name) == normalize_channel_name(channel_name):
                    matched_count += 1
                    break

        print(f"   匹配模板频道: {matched_count} 个 (共 {len(template_names)} 个模板)")
        print(f"   额外频道: {len(sorted_channels) - matched_count} 个")

        total_programs = sum(len(progs) for progs in final_programmes.values())
        print(f"   节目数量: {total_programs}")
        print("=" * 60)

        # 显示前20个频道的排序
        print("\n频道排序 (前20个):")
        for i, (channel_id, name) in enumerate(list(sorted_channels)[:20], 1):
            in_template = i <= len(template_names)
            template_mark = "✓" if in_template else " "
            print(f"  {i:2d}. [{template_mark}] {channel_id}: {name}")

    else:
        print("\n✗ 处理失败!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
    except Exception as e:
        print(f"\n✗ 程序执行出错: {str(e)}")

