#!/usr/bin/env python3
# core/__init__.py

# 导出 core 模块中的所有类
from .fetcher import SourceFetcher
from .parser import PlaylistParser
from .matcher import AutoCategoryMatcher
from .tester import SpeedTester
from .exporter import ResultExporter
from .models import Channel

# 如果需要，可以在这里定义其他模块级别的变量或常量
__all__ = [
    'SourceFetcher',
    'PlaylistParser',
    'AutoCategoryMatcher',
    'SpeedTester',
    'ResultExporter',
    'Channel',
]
