"""
基础API路由
"""

from flask import request, current_app
from . import bp
from .utils import APIResponse, require_rate_limit

@bp.route('/v1/health', methods=['GET'])
@require_rate_limit
def health_check():
    """健康检查接口"""
    try:
        # 检查数据库连接
        from bilibili_analyzer.models import db
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {e}")
        db_status = 'unhealthy'
    
    health_data = {
        'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
        'timestamp': current_app.config.get('START_TIME', 'unknown'),
        'components': {
            'database': db_status,
            'api': 'healthy'
        },
        'version': '1.0.0'
    }
    
    return APIResponse.success(health_data, "Service is healthy")

@bp.route('/v1/info', methods=['GET'])
@require_rate_limit
def api_info():
    """API信息接口"""
    info = {
        'name': 'Bilibili Video Analysis API',
        'version': '1.0.0',
        'description': 'REST API for analyzing Bilibili video content and managing knowledge base',
        'endpoints': {
            'health': '/api/v1/health',
            'video': {
                'extract': '/api/v1/video/extract',
                'subtitle_download': '/api/v1/subtitle/download',
                'get_info': '/api/v1/video/<bvid>'
            },
            'analysis': {
                'analyze': '/api/v1/analyze',
                'get_result': '/api/v1/analysis/<id>',
                'batch_analyze': '/api/v1/analysis/batch'
            },
            'knowledge': {
                'search': '/api/v1/knowledge/search',
                'create': '/api/v1/knowledge',
                'get': '/api/v1/knowledge/<id>',
                'update': '/api/v1/knowledge/<id>',
                'delete': '/api/v1/knowledge/<id>',
                'export': '/api/v1/knowledge/export'
            },
            'tags': {
                'list': '/api/v1/tags',
                'create': '/api/v1/tags',
                'get_entry_tags': '/api/v1/knowledge/<id>/tags'
            },
            'stats': {
                'system': '/api/v1/stats'
            }
        },
        'documentation': '/api/docs'  # Swagger文档地址
    }
    
    return APIResponse.success(info, "API information")

@bp.route('/v1/ping', methods=['GET'])
@require_rate_limit
def ping():
    """ping接口"""
    return APIResponse.success({
        'message': 'pong',
        'timestamp': request.timestamp
    }, "Service is responsive")