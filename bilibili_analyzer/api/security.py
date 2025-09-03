"""
API安全和中间件模块
"""

import re
import json
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app, g
from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden, TooManyRequests

class SecurityMiddleware:
    """安全中间件类"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # 注册安全相关配置
        app.config.setdefault('SECURITY_ENABLED', True)
        app.config.setdefault('RATE_LIMIT_ENABLED', True)
        app.config.setdefault('CORS_ENABLED', True)
        app.config.setdefault('API_KEY_REQUIRED', False)
        
        # 安全头部
        app.config.setdefault('SECURITY_HEADERS', {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'"
        })
    
    def before_request(self):
        """请求前处理"""
        if not current_app.config.get('SECURITY_ENABLED', True):
            return
        
        # 添加安全头部
        self._add_security_headers()
        
        # API密钥验证
        if current_app.config.get('API_KEY_REQUIRED', False):
            if not self._validate_api_key():
                return Unauthorized('Invalid or missing API key')
        
        # 请求大小限制
        if not self._validate_request_size():
            return BadRequest('Request too large')
        
        # 内容类型验证
        if not self._validate_content_type():
            return BadRequest('Invalid content type')
        
        # SQL注入防护
        if not self._validate_sql_injection():
            return BadRequest('Potential SQL injection detected')
        
        # XSS防护
        if not self._validate_xss():
            return BadRequest('Potential XSS attack detected')
    
    def after_request(self, response):
        """请求后处理"""
        if not current_app.config.get('SECURITY_ENABLED', True):
            return response
        
        # 添加安全头部
        for header, value in current_app.config.get('SECURITY_HEADERS', {}).items():
            response.headers[header] = value
        
        # 移除服务器信息
        response.headers.pop('Server', None)
        
        # 添加CORS头部
        if current_app.config.get('CORS_ENABLED', True):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key'
        
        return response
    
    def _add_security_headers(self):
        """添加安全头部到请求上下文"""
        g.security_headers = current_app.config.get('SECURITY_HEADERS', {})
    
    def _validate_api_key(self):
        """验证API密钥"""
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if not api_key:
            return False
        
        # 这里应该从数据库或配置中验证API密钥
        # 简化实现，只检查是否为空
        valid_keys = current_app.config.get('VALID_API_KEYS', [])
        return api_key in valid_keys
    
    def _validate_request_size(self):
        """验证请求大小"""
        max_size = current_app.config.get('MAX_REQUEST_SIZE', 10 * 1024 * 1024)  # 10MB
        
        if request.content_length and request.content_length > max_size:
            return False
        
        return True
    
    def _validate_content_type(self):
        """验证内容类型"""
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.content_type or ''
            
            # 允许的内容类型
            allowed_types = [
                'application/json',
                'application/x-www-form-urlencoded',
                'multipart/form-data'
            ]
            
            if not any(allowed_type in content_type for allowed_type in allowed_types):
                return False
        
        return True
    
    def _validate_sql_injection(self):
        """SQL注入防护"""
        # 检查查询参数
        for key, value in request.args.items():
            if self._contains_sql_injection(str(value)):
                return False
        
        # 检查JSON数据
        if request.is_json:
            data = request.get_json()
            if isinstance(data, dict):
                for key, value in data.items():
                    if self._contains_sql_injection(str(value)):
                        return False
        
        return True
    
    def _validate_xss(self):
        """XSS防护"""
        # 检查查询参数
        for key, value in request.args.items():
            if self._contains_xss(str(value)):
                return False
        
        # 检查JSON数据
        if request.is_json:
            data = request.get_json()
            if isinstance(data, dict):
                for key, value in data.items():
                    if self._contains_xss(str(value)):
                        return False
        
        return True
    
    def _contains_sql_injection(self, text):
        """检查是否包含SQL注入特征"""
        sql_patterns = [
            r'(union|select|insert|update|delete|drop|create|alter|exec|execute)\s+',
            r'(\s|^)(or|and)\s+\d+\s*=\s*\d+',
            r'(\s|^)(or|and)\s+\'[^\']*\'\s*=\s*\'[^\']*\'',
            r';\s*(drop|delete|update|insert)',
            r'\/\*.*\*\/',
            r'--.*$',
            r'0x[0-9a-fA-F]+',
            r'char\s*\(',
            r'concat\s*\(',
            r'load_file\s*\(',
            r'into\s+(outfile|dumpfile)'
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                return True
        
        return False
    
    def _contains_xss(self, text):
        """检查是否包含XSS攻击特征"""
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'expression\s*\(',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'eval\s*\(',
            r'setTimeout\s*\(',
            r'setInterval\s*\('
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False

class AdvancedRateLimiter:
    """高级限流器"""
    
    def __init__(self):
        self.requests = {}  # {ip: {endpoint: [timestamps]}}
        self.blocked_ips = {}  # {ip: unblock_time}
        self.suspicious_ips = {}  # {ip: score}
    
    def is_allowed(self, ip, endpoint, limit=100, window=60):
        """检查是否允许请求"""
        # 检查IP是否被封禁
        if self._is_ip_blocked(ip):
            return False
        
        # 检查可疑IP
        if self._is_ip_suspicious(ip):
            # 降低限制
            limit = limit // 2
        
        # 清理过期记录
        self._cleanup_expired_records(ip, endpoint, window)
        
        # 检查请求数量
        request_count = self._get_request_count(ip, endpoint)
        
        if request_count >= limit:
            # 标记为可疑IP
            self._mark_suspicious_ip(ip)
            return False
        
        # 记录请求
        self._record_request(ip, endpoint)
        
        return True
    
    def _is_ip_blocked(self, ip):
        """检查IP是否被封禁"""
        if ip in self.blocked_ips:
            if datetime.utcnow() < self.blocked_ips[ip]:
                return True
            else:
                # 解封IP
                del self.blocked_ips[ip]
        
        return False
    
    def _is_ip_suspicious(self, ip):
        """检查IP是否可疑"""
        return ip in self.suspicious_ips and self.suspicious_ips[ip] > 5
    
    def _cleanup_expired_records(self, ip, endpoint, window):
        """清理过期记录"""
        if ip not in self.requests:
            self.requests[ip] = {}
        
        if endpoint not in self.requests[ip]:
            self.requests[ip][endpoint] = []
        
        now = time.time()
        cutoff = now - window
        
        self.requests[ip][endpoint] = [
            timestamp for timestamp in self.requests[ip][endpoint]
            if timestamp > cutoff
        ]
    
    def _get_request_count(self, ip, endpoint):
        """获取请求数量"""
        if ip not in self.requests:
            return 0
        
        if endpoint not in self.requests[ip]:
            return 0
        
        return len(self.requests[ip][endpoint])
    
    def _record_request(self, ip, endpoint):
        """记录请求"""
        if ip not in self.requests:
            self.requests[ip] = {}
        
        if endpoint not in self.requests[ip]:
            self.requests[ip][endpoint] = []
        
        self.requests[ip][endpoint].append(time.time())
    
    def _mark_suspicious_ip(self, ip):
        """标记可疑IP"""
        if ip not in self.suspicious_ips:
            self.suspicious_ips[ip] = 0
        
        self.suspicious_ips[ip] += 1
        
        # 如果分数过高，封禁IP
        if self.suspicious_ips[ip] > 10:
            self.blocked_ips[ip] = datetime.utcnow() + timedelta(hours=1)
    
    def block_ip(self, ip, duration_hours=1):
        """封禁IP"""
        self.blocked_ips[ip] = datetime.utcnow() + timedelta(hours=duration_hours)
    
    def unblock_ip(self, ip):
        """解封IP"""
        if ip in self.blocked_ips:
            del self.blocked_ips[ip]
        if ip in self.suspicious_ips:
            del self.suspicious_ips[ip]

class RequestValidator:
    """请求验证器"""
    
    @staticmethod
    def validate_bvid(bvid):
        """验证BV号格式"""
        if not bvid:
            return False
        
        # BV号格式：BV1开头，后面跟着数字和字母
        pattern = r'^BV[1-9A-HJ-NP-Za-km-z]+$'
        return re.match(pattern, bvid) is not None
    
    @staticmethod
    def validate_language_code(language):
        """验证语言代码"""
        if not language:
            return False
        
        # 支持的语言代码
        supported_languages = ['zh-CN', 'zh-TW', 'en', 'ja', 'ko']
        return language in supported_languages
    
    @staticmethod
    def validate_export_format(format_type):
        """验证导出格式"""
        if not format_type:
            return False
        
        supported_formats = ['json', 'csv', 'markdown']
        return format_type.lower() in supported_formats
    
    @staticmethod
    def validate_importance(importance):
        """验证重要性等级"""
        try:
            importance = int(importance)
            return 1 <= importance <= 5
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_knowledge_type(knowledge_type):
        """验证知识类型"""
        if not knowledge_type:
            return False
        
        supported_types = ['concept', 'fact', 'method', 'tip']
        return knowledge_type.lower() in supported_types
    
    @staticmethod
    def validate_hex_color(color):
        """验证十六进制颜色"""
        if not color:
            return False
        
        pattern = r'^#[0-9A-Fa-f]{6}$'
        return re.match(pattern, color) is not None
    
    @staticmethod
    def sanitize_text(text):
        """清理文本"""
        if not text:
            return ""
        
        # 移除危险字符
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
        
        return text.strip()

# 全局实例
security_middleware = SecurityMiddleware()
advanced_rate_limiter = AdvancedRateLimiter()
request_validator = RequestValidator()

def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_app.config.get('API_KEY_REQUIRED', False):
            return f(*args, **kwargs)
        
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if not api_key:
            return Unauthorized('API key required')
        
        valid_keys = current_app.config.get('VALID_API_KEYS', [])
        if api_key not in valid_keys:
            return Unauthorized('Invalid API key')
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_rate_limit(limit=100, window=60):
    """限流装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr
            endpoint = request.endpoint
            
            if not advanced_rate_limiter.is_allowed(ip, endpoint, limit, window):
                return TooManyRequests('Rate limit exceeded')
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_json(schema=None):
    """JSON验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return BadRequest('Request must be JSON')
            
            data = request.get_json()
            if not data:
                return BadRequest('No JSON data provided')
            
            # 如果提供了schema，进行验证
            if schema:
                errors = validate_schema(data, schema)
                if errors:
                    return BadRequest({'errors': errors})
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_schema(data, schema):
    """验证数据schema"""
    errors = []
    
    for field, rules in schema.items():
        if rules.get('required', False) and field not in data:
            errors.append(f"Field '{field}' is required")
            continue
        
        if field in data:
            value = data[field]
            
            # 类型验证
            if 'type' in rules:
                expected_type = rules['type']
                if not isinstance(value, expected_type):
                    errors.append(f"Field '{field}' must be of type {expected_type.__name__}")
            
            # 长度验证
            if 'min_length' in rules and len(str(value)) < rules['min_length']:
                errors.append(f"Field '{field}' must be at least {rules['min_length']} characters long")
            
            if 'max_length' in rules and len(str(value)) > rules['max_length']:
                errors.append(f"Field '{field}' must be at most {rules['max_length']} characters long")
            
            # 数值范围验证
            if 'min_value' in rules and value < rules['min_value']:
                errors.append(f"Field '{field}' must be at least {rules['min_value']}")
            
            if 'max_value' in rules and value > rules['max_value']:
                errors.append(f"Field '{field}' must be at most {rules['max_value']}")
            
            # 枚举验证
            if 'enum' in rules and value not in rules['enum']:
                errors.append(f"Field '{field}' must be one of {rules['enum']}")
            
            # 自定义验证
            if 'validator' in rules:
                validator = rules['validator']
                if not validator(value):
                    errors.append(f"Field '{field}' is invalid")
    
    return errors