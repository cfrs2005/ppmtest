"""
Bilibili视频分析系统 - 主应用包
"""

import logging
import logging.handlers
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
    
    # 配置日志系统
    _setup_logging(app)
    
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


def _setup_logging(app):
    """配置日志系统"""
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    log_file = app.config.get('LOG_FILE', 'app.log')
    
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（如果配置了日志文件）
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    app.logger.info(f"日志系统已配置，级别: {log_level}")