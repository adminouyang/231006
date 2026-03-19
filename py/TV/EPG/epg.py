#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPG数据下载和合并脚本
从epg.txt读取EPG源地址，按demo.txt中的频道名称排序，输出为指定格式的epg.xml
说明：demo.txt中，每行第一列为主频道名，后续以“|”分隔的为别名。
     脚本将使用主频道名和所有别名进行匹配，但最终输出的频道名称统一为主频道名。
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
    """
    从模板文件读取频道名称列表
    新格式：每行第一列为主频道名，后续以‘|’分隔的为别名。
    返回：列表，每个元素是一个字典 {'primary': 主频道名, 'all_names': [主频道名, 别名1, 别名2...]}
    """
    channel_entries = []
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行、注释行和分类行（如“央视频道,#genre#”）
                if not line or line.startswith('#') or line.endswith('#genre#'):
                    continue
                
                # 按‘|’分割，第一部分是主频道名
                parts = line.split('|')
                primary_name = parts[0].strip()
                if not primary_name:
                    continue  # 主频道名为空则跳过
                
                # 收集所有名称（主频道名 + 后续非空别名）
                all_names = [primary_name]
                for alias in parts[1:]:
                    alias = alias.strip()
                    if alias:  # 只添加非空别名
                        all_names.append(alias)
                
                channel_entries.append({
                    'primary': primary_name,
                    'all_names': all_names
                })

        print(f"✓ 从 {template_file} 解析到 {len(channel_entries)} 个频道模板条目")
        return channel_entries
    except FileNotFoundError:
        print(f"✗ 模板文件 {template_file} 不存在")
        return []
    except Exception as e:
        print(f"✗ 读取/解析模板文件失败: {str(e)}")
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


def parse_epg_data(xml_content, template_entries):
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

        # 为模板中的所有名称（主频道名+别名）创建标准化集合，用于快速判断“是否在模板中”
        all_template_normalized_names = set()
        for entry in template_entries:
            for name in entry['all_names']:
                all_template_normalized_names.add(normalize_channel_name(name))

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

            # 检查是否在模板中（匹配主频道名或任意别名）
            in_template = normalized_name in all_template_normalized_names

            channels.append({
                'id': channel_id,
                'name': display_name,
                'normalized': normalized_name,
                'in_template': in_template
            })

            # 建立标准化名称到频道的映射
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


def find_best_match_for_template_entry(template_entry, name_to_channel_map, used_channel_ids):
    """
    为模板条目找到最佳匹配的EPG频道。
    template_entry: 字典，包含'primary'(主频道名)和'all_names'(所有名称列表)
    优先使用精确匹配（标准化后的名称完全一致），其次尝试模糊/部分匹配。
    返回匹配到的 (channel_id, channel_display_name)，但输出时应使用 template_entry['primary']。
    若未找到，返回 None。
    """
    primary_name = template_entry['primary']
    all_names = template_entry['all_names']

    # 1. 精确匹配：遍历该条目的所有名称（主频道名+别名），检查是否有标准化的EPG频道名与之完全一致
    for name_to_try in all_names:
        template_normalized = normalize_channel_name(name_to_try)
        if template_normalized in name_to_channel_map:
            for channel in name_to_channel_map[template_normalized]:
                if channel['id'] not in used_channel_ids:
                    # 匹配成功！记录匹配到的原始EPG频道名用于日志
                    matched_source_name = channel['name']
                    # 但返回的主频道名是我们想要输出的名字
                    print(f"  ✓ 匹配成功: 模板“{primary_name}” (通过名称“{name_to_try}”) -> EPG频道“{matched_source_name}”")
                    return {
                        'id': channel['id'],
                        'source_name': matched_source_name,  # EPG中的原名，用于日志
                        'output_name': primary_name          # 最终输出到XML的名称
                    }

    # 2. 如果精确匹配失败，尝试模糊匹配（模板名称是EPG频道名称的一部分，或反之）
    # 这里采用与原先脚本类似的逻辑，但遍历的是模板条目的所有名称
    for name_to_try in all_names:
        template_normalized = normalize_channel_name(name_to_try)
        for epg_normalized_name, channels in name_to_channel_map.items():
            if template_normalized in epg_normalized_name or epg_normalized_name in template_normalized:
                for channel in channels:
                    if channel['id'] not in used_channel_ids:
                        matched_source_name = channel['name']
                        print(f"  ⚠ 模糊匹配: 模板“{primary_name}” (通过名称“{name_to_try}”) -> EPG频道“{matched_source_name}”")
                        return {
                            'id': channel['id'],
                            'source_name': matched_source_name,
                            'output_name': primary_name
                        }

    # 3. 部分匹配（名称有共同部分）
    for name_to_try in all_names:
        template_normalized = normalize_channel_name(name_to_try)
        template_parts = set(re.findall(r'[a-z0-9]+', template_normalized))
        for epg_normalized_name, channels in name_to_channel_map.items():
            channel_parts = set(re.findall(r'[a-z0-9]+', epg_normalized_name))
            if template_parts.intersection(channel_parts):
                for channel in channels:
                    if channel['id'] not in used_channel_ids:
                        matched_source_name = channel['name']
                        print(f"  ⚠ 部分匹配: 模板“{primary_name}” (通过名称“{name_to_try}”) -> EPG频道“{matched_source_name}”")
                        return {
                            'id': channel['id'],
                            'source_name': matched_source_name,
                            'output_name': primary_name
                        }

    # 4. 没有找到任何匹配
    print(f"  ✗ 未找到匹配: 模板“{primary_name}” (尝试了: {', '.join(all_names)})")
    return None


def merge_and_sort_by_template(channels, programmes, template_entries):
    """
    按照模板条目合并和排序数据。
    对每个模板条目，尝试匹配EPG频道。匹配成功后，输出频道名使用条目的主频道名(primary_name)。
    """
    sorted_channels = []  # 元素为 (channel_id, output_display_name)
    used_channel_ids = set()

    # 建立标准化名称到频道的映射 (复用之前解析EPG时建立的映射，这里为了逻辑清晰再构建一次)
    name_to_channel_map = {}
    for channel in channels:
        normalized = channel['normalized']
        if normalized not in name_to_channel_map:
            name_to_channel_map[normalized] = []
        name_to_channel_map[normalized].append({
            'id': channel['id'],
            'name': channel['name']  # EPG中的原始显示名
        })

    # 按照模板条目的顺序，为每个条目寻找匹配的EPG频道
    for template_entry in template_entries:
        matched = find_best_match_for_template_entry(template_entry, name_to_channel_map, used_channel_ids)
        if matched:
            # 使用匹配到的频道ID，但输出名称使用模板的主频道名
            sorted_channels.append((matched['id'], matched['output_name']))
            used_channel_ids.add(matched['id'])

    # 添加剩余的、未匹配任何模板的EPG频道
    remaining_channels = []
    for channel in channels:
        if channel['id'] not in used_channel_ids:
            # 对于未匹配的频道，使用其EPG中的原始名称
            remaining_channels.append((channel['id'], channel['name']))

    # 对剩余频道按名称排序
    remaining_channels.sort(key=lambda x: x[1])
    sorted_channels.extend(remaining_channels)

    # 对每个频道的节目按开始时间排序
    for channel_id in programmes:
        programmes[channel_id].sort(key=lambda x: x['start'])

    print(f"✓ 排序完成: {len(sorted_channels)} 个频道 (其中 {len(used_channel_ids)} 个通过模板匹配)")
    return sorted_channels, programmes


def create_output_xml(sorted_channels, programmes, output_file='epg.xml'):
    """创建符合格式要求的XML输出"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入XML声明和根元素
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<tv>\n')

            # 写入频道信息
            for channel_id, display_name in sorted_channels:
                f.write(f'  <channel id="{channel_id}">\n')
                f.write(f'    <display-name lang="zh">{display_name}</display-name>\n')
                f.write('  </channel>\n')

            # 写入节目信息
            for channel_id, display_name in sorted_channels:
                if channel_id in programmes:
                    for prog in programmes[channel_id]:
                        f.write(f'  <programme start="{prog["start"]}" stop="{prog["stop"]}" channel="{channel_id}">\n')
                        f.write(f'    <title lang="zh">{prog["title"]}</title>\n')
                        f.write('  </programme>\n')

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
    print("EPG数据下载和合并工具 (按模板主频道名输出)")
    print("=" * 60)

    # 1. 读取并解析频道名称模板
    template_entries = read_channel_names_template('py/TV/EPG/demo.txt')
    if not template_entries:
        print("✗ 无法解析频道名称模板，程序退出")
        return

    # 显示前几个模板条目
    print("模板频道条目 (前5个):")
    for i, entry in enumerate(template_entries[:5]):
        print(f"  {i+1}. 主名: {entry['primary']}, 所有名称: {entry['all_names']}")
    if len(template_entries) > 5:
        print(f"  ... 还有 {len(template_entries) - 5} 个条目")

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
        channels, programmes, name_map = parse_epg_data(decompressed, template_entries)
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
    print("按模板频道名称排序并统一输出主频道名...")
    sorted_channels, final_programmes = merge_and_sort_by_template(merged_channels, merged_programmes, template_entries)

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
        print(f"   频道总数: {len(sorted_channels)}")

        # 统计匹配模板的情况（前N个频道是模板匹配的）
        matched_by_template_count = 0
        for channel_id, output_name in sorted_channels:
            # 检查这个输出名是否是某个模板条目的主频道名
            if any(entry['primary'] == output_name for entry in template_entries):
                matched_by_template_count += 1

        print(f"   通过模板匹配的频道: {matched_by_template_count} 个 (共 {len(template_entries)} 个模板条目)")
        print(f"   额外频道: {len(sorted_channels) - matched_by_template_count} 个")

        total_programs = sum(len(progs) for progs in final_programmes.values())
        print(f"   节目总数: {total_programs}")
        print("=" * 60)

        # 显示前20个频道的排序
        print("\n频道排序 (前20个，[T]表示来自模板):")
        for i, (channel_id, output_name) in enumerate(list(sorted_channels)[:20], 1):
            from_template = any(entry['primary'] == output_name for entry in template_entries)
            template_mark = "T" if from_template else " "
            print(f"  {i:2d}. [{template_mark}] {channel_id}: {output_name}")

    else:
        print("\n✗ 处理失败!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
    except Exception as e:
        print(f"\n✗ 程序执行出错: {str(e)}")
