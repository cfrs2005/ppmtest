# Bilibili视频分析系统API文档

## 📖 概述

Bilibili视频分析系统API是一个功能完整的RESTful API，提供了从Bilibili视频信息提取、字幕下载、内容分析到知识库管理的全套功能。

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd ppmtest

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库初始化

```bash
# 初始化数据库
python init_db.py
```

### 3. 启动服务

```bash
# 使用启动脚本（推荐）
./start_api.sh

# 或手动启动
python app.py
```

### 4. 验证服务

```bash
# 运行验证脚本
python validate_api.py

# 运行功能测试
python test_api.py

# 运行性能测试
python test_api_performance.py
```

## 📚 API文档

### Swagger UI

访问 http://localhost:5000/api/docs 查看交互式API文档。

### OpenAPI规范

访问 http://localhost:5000/api/docs/openapi.json 获取OpenAPI规范。

## 🔑 认证和安全

### API密钥认证（可选）

如果启用了API密钥认证，需要在请求头中包含：

```http
X-API-Key: your-api-key
```

### 限流

- 默认限制：每IP每分钟100个请求
- 超过限制会返回429状态码
- 错误响应中包含`Retry-After`头部

### 安全特性

- SQL注入防护
- XSS攻击防护
- CSRF保护
- 安全头部设置
- 请求大小限制
- 内容类型验证

## 📋 主要API端点

### 系统管理

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| GET | `/api/v1/ping` | Ping测试 |
| GET | `/api/v1/info` | API信息 |
| GET | `/api/v1/stats` | 系统统计 |

### 视频处理

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/video/extract` | 提取视频信息 |
| POST | `/api/v1/subtitle/download` | 下载字幕 |
| GET | `/api/v1/video/{bvid}` | 获取视频信息 |
| GET | `/api/v1/video/{bvid}/subtitle` | 获取视频字幕 |
| GET | `/api/v1/videos` | 获取视频列表 |

### 内容分析

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/analyze` | 分析内容 |
| GET | `/api/v1/analysis/{id}` | 获取分析结果 |
| POST | `/api/v1/analysis/batch` | 批量分析 |
| GET | `/api/v1/analyses` | 获取分析列表 |
| GET | `/api/v1/analysis/{id}/knowledge` | 获取分析知识 |

### 知识库管理

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/knowledge/search` | 搜索知识库 |
| GET | `/api/v1/knowledge` | 获取知识条目列表 |
| POST | `/api/v1/knowledge` | 创建知识条目 |
| GET | `/api/v1/knowledge/{id}` | 获取知识条目 |
| PUT | `/api/v1/knowledge/{id}` | 更新知识条目 |
| DELETE | `/api/v1/knowledge/{id}` | 删除知识条目 |
| GET | `/api/v1/knowledge/export` | 导出知识库 |
| GET | `/api/v1/knowledge/stats` | 知识库统计 |

### 标签管理

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/tags` | 获取标签列表 |
| POST | `/api/v1/tags` | 创建标签 |
| GET | `/api/v1/tags/{id}` | 获取标签 |
| PUT | `/api/v1/tags/{id}` | 更新标签 |
| DELETE | `/api/v1/tags/{id}` | 删除标签 |
| GET | `/api/v1/knowledge/{id}/tags` | 获取知识条目标签 |
| POST | `/api/v1/knowledge/{id}/tags` | 添加知识条目标签 |
| DELETE | `/api/v1/knowledge/{id}/tags/{tag_id}` | 移除知识条目标签 |

### 统计监控

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/stats` | 系统统计 |
| GET | `/api/v1/stats/analysis` | 分析统计 |
| GET | `/api/v1/stats/knowledge` | 知识库统计 |
| GET | `/api/v1/stats/performance` | 性能统计 |
| GET | `/api/v1/health/detailed` | 详细健康状态 |

## 📖 使用示例

### 1. 提取视频信息

```bash
curl -X POST http://localhost:5000/api/v1/video/extract \
  -H "Content-Type: application/json" \
  -d '{"bvid": "BV1GJ411x7h7"}'
```

### 2. 下载字幕

```bash
curl -X POST http://localhost:5000/api/v1/subtitle/download \
  -H "Content-Type: application/json" \
  -d '{"bvid": "BV1GJ411x7h7", "language": "zh-CN"}'
```

### 3. 分析内容

```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"bvid": "BV1GJ411x7h7", "language": "zh-CN"}'
```

### 4. 搜索知识库

```bash
curl -X GET "http://localhost:5000/api/v1/knowledge/search?q=机器学习&limit=10"
```

### 5. 创建知识条目

```bash
curl -X POST http://localhost:5000/api/v1/knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "title": "机器学习基础概念",
    "content": "机器学习是人工智能的一个分支，通过算法让计算机从数据中学习。",
    "knowledge_type": "concept",
    "importance": 4,
    "tags": ["机器学习", "AI", "概念"]
  }'
```

### 6. 获取系统统计

```bash
curl -X GET http://localhost:5000/api/v1/stats
```

## 📊 响应格式

### 成功响应

```json
{
  "success": true,
  "message": "操作成功",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "data": {
    // 响应数据
  }
}
```

### 分页响应

```json
{
  "success": true,
  "message": "操作成功",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "data": {
    "items": [],
    "pagination": {
      "total": 100,
      "page": 1,
      "per_page": 20,
      "pages": 5
    }
  }
}
```

### 错误响应

```json
{
  "success": false,
  "message": "错误描述",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "error_code": "ERROR_CODE",
  "details": {} // 可选的详细信息
}
```

## 🚨 错误代码

| 状态码 | 错误代码 | 描述 |
|--------|----------|------|
| 400 | BAD_REQUEST | 请求参数错误 |
| 401 | UNAUTHORIZED | 未授权访问 |
| 403 | FORBIDDEN | 禁止访问 |
| 404 | NOT_FOUND | 资源不存在 |
| 405 | METHOD_NOT_ALLOWED | 方法不允许 |
| 409 | CONFLICT | 资源冲突 |
| 429 | RATE_LIMIT_EXCEEDED | 请求频率限制 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

## ⚡ 性能要求

- **响应时间**: 95%的请求应在1秒内完成
- **并发处理**: 支持100个并发用户
- **可用性**: 99.9%的服务可用性
- **限流**: 每IP每分钟100个请求

## 🔧 配置选项

### 环境变量

```bash
# Flask配置
FLASK_DEBUG=True
FLASK_ENV=development
PORT=5000

# 数据库配置
DATABASE_URL=sqlite:///instance/app.db

# API密钥配置
API_KEY_REQUIRED=False
VALID_API_KEYS=key1,key2,key3

# 限流配置
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# 安全配置
SECURITY_ENABLED=True
MAX_REQUEST_SIZE=10485760  # 10MB
CORS_ENABLED=True
```

### 配置文件

```python
# bilibili_analyzer/config.py
class Config:
    # 基础配置
    SECRET_KEY = 'your-secret-key'
    DEBUG = False
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API配置
    API_VERSION = 'v1'
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    
    # 安全配置
    SECURITY_ENABLED = True
    API_KEY_REQUIRED = False
    VALID_API_KEYS = []
    
    # 限流配置
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 60
```

## 🧪 测试

### 功能测试

```bash
# 运行所有测试
python test_api.py

# 测试特定端点
python test_api.py http://localhost:5000
```

### 性能测试

```bash
# 运行性能测试
python test_api_performance.py

# 生成性能报告
python test_api_performance.py http://localhost:5000
```

### 验证脚本

```bash
# 快速验证
python validate_api.py
```

## 📈 监控

### 健康检查

```bash
# 基础健康检查
curl http://localhost:5000/api/v1/health

# 详细健康状态
curl http://localhost:5000/api/v1/health/detailed
```

### 系统统计

```bash
# 获取系统统计
curl http://localhost:5000/api/v1/stats

# 获取分析统计
curl http://localhost:5000/api/v1/stats/analysis

# 获取性能统计
curl http://localhost:5000/api/v1/stats/performance
```

## 🔍 故障排除

### 常见问题

1. **服务无法启动**
   - 检查端口是否被占用
   - 确认依赖已正确安装
   - 检查数据库配置

2. **API响应慢**
   - 检查网络连接
   - 确认B站API可访问
   - 检查数据库性能

3. **分析失败**
   - 确认LLM服务配置正确
   - 检查API密钥是否有效
   - 查看日志文件

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log
```

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个API！

## 📄 许可证

MIT License

## 📞 支持

如有问题，请通过以下方式联系：

- GitHub Issues
- Email: support@example.com

---

**注意**: 使用本API时请遵守B站的相关规定和robots.txt文件的要求。