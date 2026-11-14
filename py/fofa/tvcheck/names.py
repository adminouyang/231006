# -*- coding: utf-8 -*-
"""demo.txt 解析：频道别名校正、分组归属、排序顺序。"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

# 归一化时直接丢弃的符号（括号、连字符、空白等）
_PUNCT_RE = re.compile(r"[\s\u3000\-_·•.,，、/\\|()（）\[\]【】<>《》\"'’‘“”;；:：!！?？~]+")

# 归一化时逐层剥离的“画质 / 修饰”后缀
_QUALITY_SUFFIXES = (
    "高清版", "超清版", "标清版", "高清", "超清", "标清", "蓝光", "超高清",
    "1080p60", "1080p", "720p", "540p", "2160p", "4k", "8k",
    "uhd", "fhd", "hd", "sd", "h265", "hevc", "avc",
    "测试", "备用", "流畅", "直播", "频道", "台",
)

# 未命中模板的频道统一归入的兜底分组。
# 优先使用 demo.txt 里已有的名字（常见写法有 其它 / 其他 / 其它频道 / 其他频道），
# 都没有时才新建 DEFAULT_GROUP。
DEFAULT_GROUP = "其它频道"
_DEFAULT_GROUP_NAMES = ("其它频道", "其他频道", "其它", "其他")

# 解析 demo.txt 时忽略的表头
_HEADER_PREFIXES = ("主频道名", "#", "//")


def normalize(text: str) -> str:
    """把频道名压成可比较的 key：全半角统一、小写、去符号。"""
    if not text:
        return ""
    s = unicodedata.normalize("NFKC", str(text)).lower()
    s = _PUNCT_RE.sub("", s)
    return s.strip()


def _keys(name: str) -> list[str]:
    """一个名字可能对应的若干 key（含逐层剥离画质后缀的结果）。"""
    base = normalize(name)
    if not base:
        return []
    keys = [base]
    cur = base
    for _ in range(3):
        for suf in _QUALITY_SUFFIXES:
            if cur.endswith(suf) and len(cur) > len(suf):
                cur = cur[: -len(suf)]
                if cur not in keys:
                    keys.append(cur)
                break
        else:
            break
    return keys


def clean_name(raw: str) -> str:
    """输出用的展示名：压空白、去掉尾部画质后缀。"""
    s = re.sub(r"\s+", " ", (raw or "").strip())
    if not s:
        return ""
    for suf in ("高清", "超清", "标清", "蓝光", "HD", "hd", "4K", "8K", "1080P", "720P", "UHD", "FHD"):
        if s.endswith(suf) and len(s) > len(suf) + 1:
            s = s[: -len(suf)].strip()
            break
    return s.strip(" -_·|")


@dataclass
class ChannelInfo:
    name: str      # 标准名
    group: str     # 所属分组
    key: str       # 归一化 key
    order: int     # 在 demo.txt 中的顺序


class ChannelDB:
    """demo.txt 的内存模型。"""

    def __init__(self) -> None:
        self.alias: dict[str, ChannelInfo] = {}
        self.groups: list[str] = []
        self._group_alias: dict[str, str] = {}
        self._group_index: dict[str, int] = {}
        self.default_group = DEFAULT_GROUP

    # ---------------- 构建 ----------------
    @classmethod
    def load(cls, path: Path) -> "ChannelDB":
        db = cls()
        if not path.exists():
            return db
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        db.feed(text)
        return db

    def feed(self, text: str) -> None:
        group = ""
        order = 0
        for raw in text.splitlines():
            line = raw.strip().lstrip("\ufeff")
            if not line:
                continue
            if "#genre#" in line:
                name = line.split(",")[0].strip().strip("#").strip()
                if name:
                    group = name
                    if name not in self.groups:
                        self.groups.append(name)
                        self._group_index[name] = len(self.groups)
                    self._group_alias.setdefault(normalize(name), name)
                continue
            if line.startswith(_HEADER_PREFIXES):
                continue
            if "|" not in line:
                continue

            parts = [p.strip() for p in line.split("|")]
            parts = [p for p in parts if p]
            if not parts:
                continue
            name = parts[0]
            key = normalize(name)
            if not key:
                continue
            gname = group or DEFAULT_GROUP
            info = self.alias.get(key) or ChannelInfo(name=name, group=gname, key=key, order=order)
            # 同一个标准名可能出现多次，保留首次的分组与顺序
            if key not in self.alias:
                self.alias[key] = info
                order += 1
            for a in parts[1:]:
                for k in _keys(a):
                    self.alias.setdefault(k, info)
            for k in _keys(name):
                self.alias.setdefault(k, info)

        self._resolve_default_group()

    def _resolve_default_group(self) -> None:
        """模板里的兜底分组：优先沿用 demo.txt 已有的 其它/其他，找不到才新建。"""
        for name in _DEFAULT_GROUP_NAMES:
            if name in self.groups:
                self.default_group = name
                return
        self.default_group = DEFAULT_GROUP
        if DEFAULT_GROUP not in self.groups:
            self.groups.append(DEFAULT_GROUP)
            self._group_index[DEFAULT_GROUP] = len(self.groups)

    # ---------------- 查询 ----------------
    def match(self, *names: str) -> ChannelInfo | None:
        for name in names:
            if not name:
                continue
            for key in _keys(name):
                info = self.alias.get(key)
                if info is not None:
                    return info
        return None

    def order_of(self, key: str) -> int:
        info = self.alias.get(key)
        return info.order if info is not None else 10 ** 6

    def group_for(self, raw: str) -> str:
        """源里的分组名不参与输出分组，未命中 demo.txt 的频道统一进兜底分组。"""
        return self.default_group

    def group_index(self, group: str) -> int:
        # 严格按 demo.txt 的分组顺序输出；模板里没有的分组（理论上不会出现）排到最后
        if group in self._group_index:
            return self._group_index[group]
        return 9000 + sum(ord(c) for c in group) % 999
