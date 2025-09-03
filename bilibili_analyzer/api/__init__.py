"""
Bilibili视频分析系统 - API蓝图
"""

from flask import Blueprint

# 创建API蓝图
bp = Blueprint('api', __name__)

# 导入路由
from . import routes
from . import video_routes
from . import analysis_routes
from . import knowledge_routes
from . import tag_routes
from . import stats_routes
from . import dashboard_routes