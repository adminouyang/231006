#!/usr/bin/env python3
import re
from typing import Generator
from .models import Channel
import logging

class PlaylistParser:
    """M3U解析器，使用生成器逐条处理数据"""
    
    CHANNEL_REGEX = re.compile(r'^(.*?),(http.*)$', re.MULTILINE)
    EXTINF_REGEX = re.compile(r'#EXTINF:-?[\d.]*,?(.*?)\n(.*)')

    def parse(self, content: str) -> Generator[Channel, None, None]:
        """解析内容生成频道列表（生成器）"""
        channel_matches = self.CHANNEL_REGEX.findall(content)
        if channel_matches:
            for name, url in channel_matches:
                # 清理 URL，去除 $ 及其后面的参数
                clean_url = self._clean_url(url)
                yield Channel(name=self._clean_name(name), url=clean_url)
        else:
            for name, url in self.EXTINF_REGEX.findall(content):
                # 清理 URL，去除 $ 及其后面的参数
                clean_url = self._clean_url(url)
                yield Channel(name=self._clean_name(name), url=clean_url)

    def _clean_name(self, raw_name: str) -> str:
        """清理频道名称"""
        return raw_name.split(',')[-1].strip()

    def _clean_url(self, raw_url: str) -> str:
        """清理 URL，去除 $ 及其后面的参数"""
        return raw_url.split('$')[0].strip()
