"""
Bilibili视频分析系统 - 主应用包
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 数据库实例
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=None):
    """应用工厂函数"""
    app = Flask(__name__)
    
    if config_class:
        app.config.from_object(config_class)
    else:
        from .config import Config
        app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 注册蓝图
    try:
        from .main_simple import bp as main_bp
        app.register_blueprint(main_bp)
    except ImportError:
        pass
    
    try:
        from .auth_simple import bp as auth_bp
        app.register_blueprint(auth_bp)
    except ImportError:
        pass
    
    try:
        from .api import bp as api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
    except ImportError:
        pass
    
    try:
        from .admin import bp as admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
    except ImportError:
        pass
    
    return app