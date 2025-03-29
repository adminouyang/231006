#!/usr/bin/env python3
from dataclasses import dataclass

@dataclass
class Channel:
    """频道数据模型"""
    name: str
    url: str
    category: str = "未分类"
    status: str = "pending"
    response_time: float = 0.0
    download_speed: float = 0.0
