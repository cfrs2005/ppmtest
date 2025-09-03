#!/bin/bash

# Bilibili视频分析系统启动脚本

echo "🚀 启动Bilibili视频分析系统..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖..."
pip install -r requirements.txt

# 初始化数据库
echo "🗄️ 初始化数据库..."
python init_db.py

# 启动应用
echo "🌟 启动Flask应用..."
python app.py