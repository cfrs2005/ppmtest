"""
Bilibili视频分析系统 - HTTP请求工具类
"""

import time
import random
import requests
from typing import Optional, Dict, Any, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class BilibiliRequestHandler:
    """B站请求处理器，包含反爬虫机制"""
    
    # User-Agent列表
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    
    # 默认请求头
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    def __init__(self, delay_range: tuple = (1, 3), max_retries: int = 3):
        """
        初始化请求处理器
        
        Args:
            delay_range: 请求延迟范围（最小，最大）秒
            max_retries: 最大重试次数
        """
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.session = self._create_session()
        self.last_request_time = 0
        
    def _create_session(self) -> requests.Session:
        """创建配置好的会话"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.USER_AGENTS)
    
    def _get_delay(self) -> float:
        """获取随机延迟时间"""
        return random.uniform(*self.delay_range)
    
    def _apply_delay(self):
        """应用请求延迟"""
        current_time = time.time()
        if current_time - self.last_request_time < self._get_delay():
            time.sleep(self._get_delay() - (current_time - self.last_request_time))
        self.last_request_time = time.time()
    
    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None, 
                        referer: Optional[str] = None) -> Dict[str, str]:
        """准备请求头"""
        final_headers = self.DEFAULT_HEADERS.copy()
        final_headers['User-Agent'] = self._get_random_user_agent()
        
        if referer:
            final_headers['Referer'] = referer
            
        if headers:
            final_headers.update(headers)
            
        return final_headers
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None, referer: Optional[str] = None,
            timeout: int = 10) -> requests.Response:
        """
        发送GET请求
        
        Args:
            url: 请求URL
            params: 请求参数
            headers: 额外请求头
            referer: Referer值
            timeout: 超时时间
            
        Returns:
            响应对象
            
        Raises:
            requests.RequestException: 请求失败
        """
        self._apply_delay()
        
        final_headers = self._prepare_headers(headers, referer)
        
        try:
            response = self.session.get(
                url,
                params=params,
                headers=final_headers,
                timeout=timeout
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"请求失败: {url}, 错误: {str(e)}")
    
    def post(self, url: str, data: Optional[Dict[str, Any]] = None,
             json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None,
             referer: Optional[str] = None, timeout: int = 10) -> requests.Response:
        """
        发送POST请求
        
        Args:
            url: 请求URL
            data: 表单数据
            json: JSON数据
            headers: 额外请求头
            referer: Referer值
            timeout: 超时时间
            
        Returns:
            响应对象
            
        Raises:
            requests.RequestException: 请求失败
        """
        self._apply_delay()
        
        final_headers = self._prepare_headers(headers, referer)
        
        try:
            response = self.session.post(
                url,
                data=data,
                json=json,
                headers=final_headers,
                timeout=timeout
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"POST请求失败: {url}, 错误: {str(e)}")
    
    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None,
                 headers: Optional[Dict[str, str]] = None, referer: Optional[str] = None,
                 timeout: int = 10) -> Dict[str, Any]:
        """
        获取JSON数据
        
        Args:
            url: 请求URL
            params: 请求参数
            headers: 额外请求头
            referer: Referer值
            timeout: 超时时间
            
        Returns:
            JSON数据
            
        Raises:
            requests.RequestException: 请求失败
            ValueError: JSON解析失败
        """
        response = self.get(url, params, headers, referer, timeout)
        
        try:
            return response.json()
        except ValueError as e:
            raise ValueError(f"JSON解析失败: {str(e)}")
    
    def get_text(self, url: str, params: Optional[Dict[str, Any]] = None,
                 headers: Optional[Dict[str, str]] = None, referer: Optional[str] = None,
                 timeout: int = 10, encoding: Optional[str] = None) -> str:
        """
        获取文本内容
        
        Args:
            url: 请求URL
            params: 请求参数
            headers: 额外请求头
            referer: Referer值
            timeout: 超时时间
            encoding: 文本编码
            
        Returns:
            文本内容
            
        Raises:
            requests.RequestException: 请求失败
        """
        response = self.get(url, params, headers, referer, timeout)
        
        if encoding:
            response.encoding = encoding
            
        return response.text
    
    def close(self):
        """关闭会话"""
        self.session.close()

# 全局请求处理器实例
_request_handler = None

def get_request_handler() -> BilibiliRequestHandler:
    """获取全局请求处理器实例"""
    global _request_handler
    if _request_handler is None:
        _request_handler = BilibiliRequestHandler()
    return _request_handler

def close_request_handler():
    """关闭全局请求处理器"""
    global _request_handler
    if _request_handler is not None:
        _request_handler.close()
        _request_handler = None

# 便捷函数
def get(url: str, **kwargs) -> requests.Response:
    """便捷GET请求"""
    return get_request_handler().get(url, **kwargs)

def post(url: str, **kwargs) -> requests.Response:
    """便捷POST请求"""
    return get_request_handler().post(url, **kwargs)

def get_json(url: str, **kwargs) -> Dict[str, Any]:
    """便捷GET JSON请求"""
    return get_request_handler().get_json(url, **kwargs)

def get_text(url: str, **kwargs) -> str:
    """便捷GET文本请求"""
    return get_request_handler().get_text(url, **kwargs)