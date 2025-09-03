"""
API工具类 - 统一响应格式和错误处理
"""

import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from flask import jsonify, Response, request
from werkzeug.exceptions import HTTPException

class APIResponse:
    """统一API响应格式"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200) -> Response:
        """成功响应"""
        response = {
            'success': True,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        return jsonify(response), status_code
    
    @staticmethod
    def error(message: str, status_code: int = 500, error_code: str = None, details: Any = None) -> Response:
        """错误响应"""
        response = {
            'success': False,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'error_code': error_code or f'ERROR_{status_code}'
        }
        
        if details:
            response['details'] = details
        
        return jsonify(response), status_code
    
    @staticmethod
    def paginated(data: list, total: int, page: int, per_page: int, message: str = "Success") -> Response:
        """分页响应"""
        response = {
            'success': True,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'data': {
                'items': data,
                'pagination': {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        }
        return jsonify(response), 200

class APIErrorHandler:
    """API错误处理器"""
    
    @staticmethod
    def register_handlers(app):
        """注册错误处理器"""
        
        @app.errorhandler(HTTPException)
        def handle_http_exception(e):
            """处理HTTP异常"""
            return APIResponse.error(
                message=e.description,
                status_code=e.code,
                error_code=f'HTTP_{e.code}'
            )
        
        @app.errorhandler(400)
        def handle_bad_request(e):
            """处理400错误"""
            return APIResponse.error(
                message="Bad Request",
                status_code=400,
                error_code='BAD_REQUEST',
                details=str(e)
            )
        
        @app.errorhandler(401)
        def handle_unauthorized(e):
            """处理401错误"""
            return APIResponse.error(
                message="Unauthorized",
                status_code=401,
                error_code='UNAUTHORIZED'
            )
        
        @app.errorhandler(403)
        def handle_forbidden(e):
            """处理403错误"""
            return APIResponse.error(
                message="Forbidden",
                status_code=403,
                error_code='FORBIDDEN'
            )
        
        @app.errorhandler(404)
        def handle_not_found(e):
            """处理404错误"""
            return APIResponse.error(
                message="Resource not found",
                status_code=404,
                error_code='NOT_FOUND'
            )
        
        @app.errorhandler(405)
        def handle_method_not_allowed(e):
            """处理405错误"""
            return APIResponse.error(
                message="Method not allowed",
                status_code=405,
                error_code='METHOD_NOT_ALLOWED'
            )
        
        @app.errorhandler(429)
        def handle_rate_limit(e):
            """处理429错误"""
            return APIResponse.error(
                message="Too many requests",
                status_code=429,
                error_code='RATE_LIMIT_EXCEEDED'
            )
        
        @app.errorhandler(500)
        def handle_internal_error(e):
            """处理500错误"""
            return APIResponse.error(
                message="Internal server error",
                status_code=500,
                error_code='INTERNAL_ERROR',
                details=str(e) if app.debug else None
            )
        
        @app.errorhandler(Exception)
        def handle_generic_exception(e):
            """处理通用异常"""
            if app.debug:
                # 调试模式下返回详细错误信息
                return APIResponse.error(
                    message=str(e),
                    status_code=500,
                    error_code='GENERIC_ERROR',
                    details={
                        'traceback': traceback.format_exc(),
                        'type': type(e).__name__
                    }
                )
            else:
                # 生产环境下只返回通用错误信息
                return APIResponse.error(
                    message="An unexpected error occurred",
                    status_code=500,
                    error_code='GENERIC_ERROR'
                )

class APIValidator:
    """API请求验证器"""
    
    @staticmethod
    def validate_json(required_fields: list = None) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """验证JSON请求体"""
        if not request.is_json:
            return False, "Request must be JSON", None
        
        data = request.get_json()
        if not data:
            return False, "No JSON data provided", None
        
        if required_fields:
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}", None
        
        return True, None, data
    
    @staticmethod
    def validate_query_params(required_params: list = None) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """验证查询参数"""
        params = request.args.to_dict()
        
        if required_params:
            missing_params = []
            for param in required_params:
                if param not in params:
                    missing_params.append(param)
            
            if missing_params:
                return False, f"Missing required query parameters: {', '.join(missing_params)}", None
        
        return True, None, params
    
    @staticmethod
    def validate_pagination_params() -> Tuple[int, int]:
        """验证分页参数"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 限制每页最大数量
        per_page = min(per_page, 100)
        
        # 确保页码和每页数量为正数
        page = max(1, page)
        per_page = max(1, per_page)
        
        return page, per_page

class APIRateLimiter:
    """简单的API限流器（基于内存，生产环境建议使用Redis）"""
    
    def __init__(self):
        self.requests = {}  # {ip: [timestamp1, timestamp2, ...]}
        self.window_size = 60  # 时间窗口（秒）
        self.max_requests = 100  # 最大请求数
    
    def is_allowed(self, ip: str) -> bool:
        """检查是否允许请求"""
        now = datetime.utcnow().timestamp()
        
        # 清理过期记录
        if ip in self.requests:
            self.requests[ip] = [ts for ts in self.requests[ip] if now - ts < self.window_size]
        
        # 检查请求数量
        if ip not in self.requests:
            self.requests[ip] = []
        
        if len(self.requests[ip]) >= self.max_requests:
            return False
        
        # 记录新请求
        self.requests[ip].append(now)
        return True

# 全局限流器实例
rate_limiter = APIRateLimiter()

def require_rate_limit(f):
    """限流装饰器"""
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        if not rate_limiter.is_allowed(ip):
            return APIResponse.error(
                message="Rate limit exceeded",
                status_code=429,
                error_code='RATE_LIMIT_EXCEEDED'
            )
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function