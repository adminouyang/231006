#!/usr/bin/env python3
import os
import asyncio
import configparser
from pathlib import Path
from typing import List, Set
import re
import logging
from core import (
    SourceFetcher,
    PlaylistParser,
    AutoCategoryMatcher,
    SpeedTester,
    ResultExporter
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StageProgress:
    """阶段进度显示器"""
    
    def __init__(self, stage_name: str, total: int, update_interval: int = 10):
        self.stage = stage_name
        self.total = max(total, 1)
        self.current = 0
        self.bar_length = 30
        self.update_interval = update_interval

    def update(self, n=1):
        self.current = min(self.current + n, self.total)
        if self.current % self.update_interval == 0 or self.current == self.total:
            percent = self.current / self.total * 100
            filled = int(self.bar_length * self.current / self.total)
            bar = '▊' * filled + ' ' * (self.bar_length - filled)
            print(f"\r{self.stage} [{bar}] {percent:.1f}%", end='', flush=True)

    def complete(self):
        bar = '▊' * self.bar_length
        print(f"\r{self.stage} [{bar}] 100.0%")


def is_blacklisted(channel, blacklist):
    """检查频道是否在黑名单中"""
    for entry in blacklist:
        if entry in channel.url or channel.url == entry or channel.name == entry:
            return True
    return False


def write_failed_urls(failed_urls: Set[str], config):
    """将失败的 URL 写入文件"""
    try:
        # 从配置文件中获取失败 URL 的路径
        failed_urls_path = Path(config.get('PATHS', 'failed_urls_path', fallback='config/failed_urls.txt'))
        
        # 确保目录存在
        failed_urls_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入失败的 URL
        with open(failed_urls_path, 'w', encoding='utf-8') as f:
            for url in failed_urls:
                f.write(f"{url}\n")
        logger.info(f"📝 失败的 URL 已写入: {failed_urls_path}")
    except Exception as e:
        logger.error(f"❌ 写入失败 URL 文件时出错: {str(e)}")


def classify_and_write_ips(channels: List['Channel'], config, output_dir: Path, matcher):
    """
    分类 IPv4 和 IPv6 地址，并将结果写入文件。
    文件格式：
    分类名称,#genre#
    频道名称,URL
    """
    # 首先对频道按照模板顺序进行排序
    sorted_channels = matcher.sort_channels_by_template(channels)

    ipv4_channels = []
    ipv6_channels = []

    # 正则表达式匹配 IPv4 和 IPv6 地址
    ipv4_pattern = re.compile(r'http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
    ipv6_pattern = re.compile(r'http://\[[a-fA-F0-9:]+]')

    # 统计每个分类的频道数量
    category_counts = {}
    for channel in sorted_channels:
        if ipv4_pattern.search(channel.url):
            ipv4_channels.append(channel)
            category_counts[channel.category] = category_counts.get(channel.category, 0) + 1
        elif ipv6_pattern.search(channel.url):
            ipv6_channels.append(channel)
            category_counts[channel.category] = category_counts.get(channel.category, 0) + 1

    # 写入 IPv4 地址
    ipv4_output_path = Path(config.get('PATHS', 'ipv4_output_path', fallback='ipv4.txt'))
    with open(output_dir / ipv4_output_path, 'w', encoding='utf-8') as f:
        current_category = None
        for channel in ipv4_channels:
            # 如果分类发生变化，写入分类行
            if channel.category != current_category:
                if current_category is not None:
                    f.write("\n")  # 在分类之间添加空行
                f.write(f"{channel.category},#genre#\n")
                current_category = channel.category
            # 写入频道信息
            f.write(f"{channel.name},{channel.url}\n")
    logger.info(f"📝 IPv4 地址已写入: {output_dir / ipv4_output_path}")

    # 写入 IPv6 地址
    ipv6_output_path = Path(config.get('PATHS', 'ipv6_output_path', fallback='ipv6.txt'))
    with open(output_dir / ipv6_output_path, 'w', encoding='utf-8') as f:
        current_category = None
        for channel in ipv6_channels:
            # 如果分类发生变化，写入分类行
            if channel.category != current_category:
                if current_category is not None:
                    f.write("\n")  # 在分类之间添加空行
                f.write(f"{channel.category},#genre#\n")
                current_category = channel.category
            # 写入频道信息
            f.write(f"{channel.name},{channel.url}\n")
    logger.info(f"📝 IPv6 地址已写入: {output_dir / ipv6_output_path}")


async def main():
    """主工作流程"""
    try:
        # 初始化配置
        config = configparser.ConfigParser()
        config_path = Path('config/config.ini')
        if not config_path.exists():
            raise FileNotFoundError(f"❌ 配置文件不存在: {config_path}")
        config.read(config_path, encoding='utf-8')

        # 获取 output_dir
        output_dir = Path(config.get('MAIN', 'output_dir', fallback='outputs'))
        output_dir.mkdir(parents=True, exist_ok=True)

        # 读取 FETCHER 配置
        fetcher_timeout = float(config.get('FETCHER', 'timeout', fallback=15))
        fetcher_concurrency = int(config.get('FETCHER', 'concurrency', fallback=5))

        # 读取 TESTER 配置
        tester_timeout = float(config.get('TESTER', 'timeout', fallback=5))
        tester_concurrency = int(config.get('TESTER', 'concurrency', fallback=4))
        tester_max_attempts = int(config.get('TESTER', 'max_attempts', fallback=3))
        tester_min_download_speed = float(config.get('TESTER', 'min_download_speed', fallback=0.01))
        tester_enable_logging = config.getboolean('TESTER', 'enable_logging', fallback=False)

        # 读取 EXPORTER 配置
        enable_history = config.getboolean('EXPORTER', 'enable_history', fallback=False)

        # 读取 BLACKLIST 配置
        blacklist_path = Path(config.get('BLACKLIST', 'blacklist_path', fallback='config/blacklist.txt'))
        if blacklist_path.exists():
            with open(blacklist_path, 'r', encoding='utf-8') as f:
                blacklist = set(line.strip() for line in f if line.strip() and not line.startswith('#'))
        else:
            blacklist = set()

        # 读取 PATHS 配置
        urls_path = Path(config.get('PATHS', 'urls_path', fallback='config/urls.txt'))
        templates_path = Path(config.get('PATHS', 'templates_path', fallback='config/templates.txt'))

        # 检查文件是否存在
        if not urls_path.exists():
            raise FileNotFoundError(f"❌ 缺少订阅源文件: {urls_path}")
        if not templates_path.exists():
            raise FileNotFoundError(f"❌ 缺少分类模板文件: {templates_path}")

        # 阶段1: 获取订阅源
        with open(urls_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        fetcher = SourceFetcher(
            timeout=fetcher_timeout,
            concurrency=fetcher_concurrency
        )
        progress = StageProgress("🌐 获取源数据", len(urls), update_interval=10)
        contents = await fetcher.fetch_all(urls, progress.update)
        progress.complete()

        # 阶段2: 解析频道
        parser = PlaylistParser()
        valid_contents = [c for c in contents if c.strip()]
        progress = StageProgress("🔍 解析频道", len(valid_contents), update_interval=20)
        channels = []
        for content in valid_contents:
            channels.extend(parser.parse(content))
            progress.update()
        progress.complete()

        # 阶段3: 智能分类
        matcher = AutoCategoryMatcher(str(templates_path))
        progress = StageProgress("🏷️ 分类频道", len(channels), update_interval=50)
        for chan in channels:
            chan.name = matcher.normalize_channel_name(chan.name)
            chan.category = matcher.match(chan.name)
            progress.update()
        progress.complete()

        # 过滤频道：仅保留模板中定义的频道
        filtered_channels = [chan for chan in channels if matcher.is_in_template(chan.name)]
        logger.info(f"过滤后频道数量: {len(filtered_channels)}/{len(channels)}")

        # 过滤黑名单
        filtered_channels = [chan for chan in filtered_channels if not is_blacklisted(chan, blacklist)]
        logger.info(f"过滤黑名单后频道数量: {len(filtered_channels)}")

        # 阶段4: 测速测试
        unique_channels = []
        seen_urls = set()
        for chan in filtered_channels:
            if chan.url not in seen_urls:
                unique_channels.append(chan)
                seen_urls.add(chan.url)
        logger.info(f"去重后频道数量: {len(unique_channels)}/{len(filtered_channels)}")

        tester = SpeedTester(
            timeout=tester_timeout,
            concurrency=tester_concurrency,
            max_attempts=tester_max_attempts,
            min_download_speed=tester_min_download_speed,
            enable_logging=tester_enable_logging
        )
        progress = StageProgress("⏱️ 测速测试", len(unique_channels), update_interval=100)
        failed_urls = set()
        await tester.test_channels(unique_channels, progress.update, failed_urls)
        progress.complete()
        logger.info("测速测试完成")

        # 写入失败的 URL
        if failed_urls:
            write_failed_urls(failed_urls, config)

        # 阶段5: 结果导出
        exporter = ResultExporter(
            output_dir=str(output_dir),
            enable_history=enable_history,
            template_path=str(templates_path),
            config=config,
            matcher=matcher  # 添加 matcher 参数
        )
        progress = StageProgress("💾 导出结果", 2, update_interval=1)
        exporter.export(unique_channels, progress.update)
        progress.complete()

        # 分类并写入 IPv4 和 IPv6 地址
        classify_and_write_ips(unique_channels, config, output_dir, matcher)

        # 输出生成的文件路径
        m3u_filename = config.get('EXPORTER', 'm3u_filename', fallback='all.m3u')
        txt_filename = config.get('EXPORTER', 'txt_filename', fallback='all.txt')
        ipv4_output_path = config.get('PATHS', 'ipv4_output_path', fallback='ipv4.txt')
        ipv6_output_path = config.get('PATHS', 'ipv6_output_path', fallback='ipv6.txt')

        logger.info(f"📄 生成的 M3U 文件: {(output_dir / m3u_filename).resolve()}")
        logger.info(f"📄 生成的 TXT 文件: {(output_dir / txt_filename).resolve()}")
        logger.info(f"📄 生成的 IPv4 地址文件: {(output_dir / ipv4_output_path).resolve()}")
        logger.info(f"📄 生成的 IPv6 地址文件: {(output_dir / ipv6_output_path).resolve()}")

        # 输出摘要
        online = sum(1 for c in unique_channels if c.status == 'online')
        logger.info(f"✅ 任务完成！在线频道: {online}/{len(unique_channels)}")
        logger.info(f"📂 输出目录: {output_dir.resolve()}")

    except Exception as e:
        logger.error(f"❌ 发生错误: {str(e)}")
        logger.info("💡 排查建议:")
        logger.info("1. 检查 config 目录下的文件是否存在")
        logger.info("2. 确认订阅源URL可访问")
        logger.info("3. 验证分类模板格式是否正确")

if __name__ == "__main__":
    if os.name == 'nt':
        from asyncio import WindowsSelectorEventLoopPolicy
        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ 全局异常捕获: {str(e)}")
