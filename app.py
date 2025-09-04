#!/usr/bin/env python3
"""
Bilibili视频分析系统 - Flask应用入口
"""

import os
from dotenv import load_dotenv

from bilibili_analyzer import create_app
from bilibili_analyzer.config import Config

# 加载环境变量
load_dotenv()

# 创建应用实例
app = create_app(Config)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"🚀 启动Bilibili分析系统...")
    print(f"📡 服务地址: http://localhost:{port}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)