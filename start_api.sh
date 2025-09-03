#!/bin/bash
# API启动和测试脚本

set -e

echo "🚀 Bilibili视频分析系统API启动和测试"
echo "========================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📚 安装依赖..."
pip install -r requirements.txt

# 初始化数据库
echo "🗄️  初始化数据库..."
python init_db.py

# 启动应用（后台运行）
echo "🌟 启动应用..."
python app.py &
APP_PID=$!

# 等待应用启动
echo "⏳ 等待应用启动..."
sleep 5

# 检查应用是否运行
if curl -s http://localhost:5000/api/v1/health > /dev/null; then
    echo "✅ 应用启动成功"
    
    # 运行基础测试
    echo "🧪 运行API测试..."
    python test_api.py http://localhost:5000
    
    # 显示API文档地址
    echo ""
    echo "📚 API文档地址:"
    echo "   - Swagger UI: http://localhost:5000/api/docs"
    echo "   - OpenAPI JSON: http://localhost:5000/api/docs/openapi.json"
    
    echo ""
    echo "🔗 主要API端点:"
    echo "   - 健康检查: GET /api/v1/health"
    echo "   - 系统信息: GET /api/v1/info"
    echo "   - 系统统计: GET /api/v1/stats"
    echo "   - 视频提取: POST /api/v1/video/extract"
    echo "   - 字幕下载: POST /api/v1/subtitle/download"
    echo "   - 内容分析: POST /api/v1/analyze"
    echo "   - 知识搜索: GET /api/v1/knowledge/search"
    echo "   - 标签管理: GET/POST /api/v1/tags"
    
    echo ""
    echo "🎯 应用正在运行，PID: $APP_PID"
    echo "💡 按 Ctrl+C 停止应用"
    
    # 等待用户中断
    wait $APP_PID
else
    echo "❌ 应用启动失败"
    kill $APP_PID 2>/dev/null || true
    exit 1
fi