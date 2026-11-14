# -*- coding: utf-8 -*-
"""订阅源拉取与 txt / m3u 解析。"""

from __future__ import annotations

import re
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

# GitHub 加速前缀，按顺序尝试（空串表示直连）
GH_PREFIXES = (
    "",
    "https://gh-proxy.com/",
    "https://ghfast.top/",
    "https://gh.catmak.name/",
    "https://mirror.ghproxy.com/",
)
GH_HOSTS = (
    "raw.githubusercontent.com",
    "gist.githubusercontent.com",
    "github.com",
    "objects.githubusercontent.com",
)

# 允许的协议
HTTP_SCHEMES = ("http", "https")
OTHER_SCHEMES = ("rtmp", "rtsp", "rtp", "udp", "igmp", "p2p", "mitv", "p3p", "mms", "rtmps")


@dataclass
class Entry:
    """一条原始频道-地址记录。"""

    name: str
    url: str
    group: str = ""
    tvg_name: str = ""
    logo: str = ""
    source: str = ""


# --------------------------------------------------------------------------- #
# 网络
# --------------------------------------------------------------------------- #
_session: requests.Session | None = None


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        s.trust_env = True
        _session = s
    return _session


def decode_bytes(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "gb18030", "big5"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "ignore")


def fetch_text(url: str, timeout: float = 30.0) -> str:
    """下载订阅源，GitHub 链接自动尝试多个加速镜像；证书异常时降级重试。"""
    targets = [url]
    if any(h in url for h in GH_HOSTS) and not url.startswith(("https://gh-proxy.com/", "https://ghfast.top/")):
        targets = [p + url for p in GH_PREFIXES]

    headers = {"User-Agent": UA, "Accept": "*/*"}
    errors: list[str] = []
    for target in targets:
        try:
            try:
                resp = _get_session().get(target, timeout=(10.0, timeout), headers=headers)
            except requests.exceptions.SSLError:
                # 自签证书 / 证书链不完整的镜像站
                resp = _get_session().get(
                    target, timeout=(10.0, timeout), headers=headers, verify=False
                )
            if resp.status_code == 200 and resp.content:
                return decode_bytes(resp.content)
            errors.append(f"{target} -> HTTP {resp.status_code}")
        except Exception as exc:  # noqa: BLE001 - 源站异常种类太多，统一降级
            errors.append(f"{target} -> {type(exc).__name__}")
        time.sleep(0.3)
    raise RuntimeError("; ".join(errors[-3:]) or "unknown error")


# --------------------------------------------------------------------------- #
# 地址清洗
# --------------------------------------------------------------------------- #
def normalize_url(raw: str) -> str:
    """清理地址：去 $选项、补协议、校验 scheme。"""
    u = (raw or "").strip().strip('"').strip("'")
    if not u:
        return ""
    # 部分源在地址后面挂播放器参数： url$User-Agent=xx
    if "$" in u:
        u = u.split("$", 1)[0]
    u = u.strip()
    if u.startswith("//"):
        u = "http:" + u
    if "://" not in u:
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:", u):
            # 形如 1.2.3.4:8080/live.m3u8 或 [2408::1]:8080/live.m3u8
            u = "http://" + u

    parsed = urlparse(u)
    scheme = (parsed.scheme or "").lower()
    if scheme not in HTTP_SCHEMES and scheme not in OTHER_SCHEMES:
        return ""
    host = (parsed.hostname or "").strip()
    if not host:
        return ""
    # 过滤 "http://token" 这类由 # 切分产生的碎片地址
    if "." not in host and ":" not in host and host != "localhost":
        try:
            if parsed.port is None:
                return ""
        except ValueError:
            return ""
    return u


def url_host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def url_hostport(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if not host:
        return ""
    try:
        port = parsed.port
    except ValueError:
        port = None
    if not port:
        port = 443 if parsed.scheme.lower() == "https" else 80
    if ":" in host:  # IPv6
        return f"[{host}]:{port}"
    return f"{host}:{port}"


def is_http(url: str) -> bool:
    return urlparse(url).scheme.lower() in HTTP_SCHEMES


_dns_cache: dict[str, str] = {}


def classify_ipver(url: str) -> str:
    """判断属于 ipv4 还是 ipv6 源。"""
    host = url_host(url)
    if not host:
        return "ipv4"
    if ":" in host:  # 字面量 IPv6
        return "ipv6"
    if re.match(r"^\d+\.\d+\.\d+\.\d+$", host):
        return "ipv4"
    cached = _dns_cache.get(host)
    if cached:
        return cached
    result = "ipv4"
    old = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(4.0)
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
        families = {item[0] for item in infos}
        if socket.AF_INET not in families and socket.AF_INET6 in families:
            result = "ipv6"
    except Exception:  # noqa: BLE001
        result = "ipv4"
    finally:
        socket.setdefaulttimeout(old)
    _dns_cache[host] = result
    return result


# --------------------------------------------------------------------------- #
# 解析
# --------------------------------------------------------------------------- #
def _split_urls(text: str) -> list[str]:
    """一个频道后面可能挂多个地址：用 # 或空白分隔。"""
    parts = re.split(r"[#\s]+", text)
    out: list[str] = []
    for p in parts:
        u = normalize_url(p)
        if u:
            out.append(u)
    return out


def parse_txt(text: str, source: str = "") -> list[Entry]:
    """解析 txt：频道名,url1#url2 / 分组名,#genre#"""
    entries: list[Entry] = []
    group = ""
    for raw in text.splitlines():
        line = raw.strip().lstrip("\ufeff").strip()
        if not line or line.startswith("//"):
            continue
        if "#genre#" in line:
            group = line.split(",")[0].strip().strip("#").strip()
            continue
        if line.startswith("#"):
            continue
        if "," not in line:
            continue
        name, rest = line.split(",", 1)
        name = name.strip().strip('"')
        if not name:
            continue
        for url in _split_urls(rest):
            entries.append(Entry(name=name, url=url, group=group, source=source))
    return entries


_EXTINF_SPLIT_RE = re.compile(r',(?=(?:[^"]*"[^"]*")*[^"]*$)')


def _extinf_name(line: str) -> str:
    parts = _EXTINF_SPLIT_RE.split(line, maxsplit=1)
    if len(parts) < 2:
        return ""
    return parts[1].strip().strip('"')


def parse_m3u(text: str, source: str = "") -> list[Entry]:
    entries: list[Entry] = []
    cur: Entry | None = None
    for raw in text.splitlines():
        line = raw.strip().lstrip("\ufeff")
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("#EXTINF"):
            attrs = dict(re.findall(r'([A-Za-z0-9_-]+)="([^"]*)"', line))
            name = _extinf_name(line) or attrs.get("tvg-name", "")
            cur = Entry(
                name=name.strip(),
                url="",
                group=attrs.get("group-title", "").strip(),
                tvg_name=attrs.get("tvg-name", "").strip(),
                logo=attrs.get("tvg-logo", "").strip(),
                source=source,
            )
            continue
        if upper.startswith("#EXTGRP"):
            if cur is not None:
                cur.group = line.split(":", 1)[-1].strip()
            continue
        if line.startswith("#"):
            continue
        url = normalize_url(line)
        if not url:
            continue
        if cur is None:
            entries.append(Entry(name="", url=url, source=source))
        else:
            cur.url = url
            entries.append(cur)
            cur = None
    return entries


def looks_like_m3u(text: str) -> bool:
    head = text.lstrip()[:200].upper()
    return head.startswith("#EXTM3U") or "#EXTINF" in head


def parse_text(text: str, source: str = "") -> list[Entry]:
    if looks_like_m3u(text):
        return parse_m3u(text, source)
    return parse_txt(text, source)


def read_subscribe(path: Path) -> list[str]:
    if not path.exists():
        return []
    urls: list[str] = []
    for raw in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls
