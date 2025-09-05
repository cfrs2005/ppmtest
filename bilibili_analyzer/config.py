"""
Bilibili视频分析系统 - 配置文件
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置类"""
    
    # 基础Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Session配置
    PERMANENT_SESSION_LIFETIME = 3600  # 1小时
    SESSION_TYPE = 'filesystem'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 应用配置
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Bilibili API配置
    BILIBILI_API_BASE = os.environ.get('BILIBILI_API_BASE', 'https://api.bilibili.com')
    BILIBILI_USER_AGENT = os.environ.get('BILIBILI_USER_AGENT', 
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Redis配置（用于Celery）
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # 分析配置
    MAX_VIDEOS_PER_CHANNEL = int(os.environ.get('MAX_VIDEOS_PER_CHANNEL', 100))
    ANALYSIS_INTERVAL_HOURS = int(os.environ.get('ANALYSIS_INTERVAL_HOURS', 6))
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}