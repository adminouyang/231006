#!/usr/bin/env python3
import aiohttp
import asyncio
from typing import List, Callable
from io import BytesIO

class SourceFetcher:
    """订阅源获取器"""
    
    def __init__(self, timeout: float, concurrency: int, retries: int = 3):
        """
        初始化订阅源获取器。

        :param timeout: 请求超时时间（秒）。
        :param concurrency: 并发请求数。
        :param retries: 请求失败时的重试次数。
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.semaphore = asyncio.Semaphore(concurrency)  # 使用并发数初始化信号量
        self.retries = retries

    async def fetch_all(self, urls: List[str], progress_cb: Callable) -> List[str]:
        """批量获取订阅源"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = [self._fetch_with_retry(session, url, progress_cb) for url in urls]
            return await asyncio.gather(*tasks)

    async def _fetch_with_retry(self, session: aiohttp.ClientSession, url: str, progress_cb: Callable) -> str:
        """带重试的单次请求处理"""
        for attempt in range(self.retries):
            try:
                result = await self._fetch(session, url, progress_cb)
                if result:
                    print(f"✅ 成功获取: {url}")  # 记录成功日志
                else:
                    print(f"⚠️ 获取成功但内容为空: {url}")  # 记录内容为空的日志
                return result
            except Exception as e:
                print(f"\n⚠️ 获取失败 (尝试 {attempt + 1}/{self.retries}): {url} ({str(e)})")
                if attempt == self.retries - 1:
                    print(f"❌ 最终失败: {url}")  # 记录最终失败日志
                    return ""
                await asyncio.sleep(1)  # 等待一段时间后重试

    async def _fetch(self, session: aiohttp.ClientSession, url: str, progress_cb: Callable) -> str:
        """单次请求处理"""
        async with self.semaphore:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
                async with session.get(url, headers=headers) as resp:
                    # 检查响应状态码
                    if resp.status != 200:
                        raise Exception(f"HTTP状态码: {resp.status}")
                    
                    # 读取原始内容
                    raw_content = await resp.read()
                    if not raw_content:
                        raise Exception("响应体为空")
                    
                    # 根据响应头中的编码解码内容
                    content_type = resp.headers.get('Content-Type', '')
                    if 'charset=' in content_type:
                        # 从 Content-Type 中提取编码
                        encoding = content_type.split('charset=')[-1].strip().lower()
                    else:
                        # 默认使用 utf-8
                        encoding = 'utf-8'
                    
                    # 解码内容
                    try:
                        content = raw_content.decode(encoding)
                    except UnicodeDecodeError:
                        # 如果解码失败，尝试其他常见编码
                        encodings = ['utf-8', 'gbk', 'latin-1']
                        for enc in encodings:
                            try:
                                content = raw_content.decode(enc)
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            raise Exception("无法解码响应内容")
                    
                    return content
            except Exception as e:
                raise e
            finally:
                progress_cb()
