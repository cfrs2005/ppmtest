---
name: bilibili-video-analyzer
description: 技术实现计划：基于Flask的B站视频内容分析服务
status: planning
created: 2025-09-03T10:21:09Z
prd: .claude/prds/bilibili-video-analyzer.md
---

# Epic: bilibili-video-analyzer

## 技术架构概览

### 系统架构图
```
┌─────────────────────────────────────────────────────────────┐
│                    Web Interface (Flask)                    │
├─────────────────────────────────────────────────────────────┤
│  Video Input  │  Progress Display  │  Results & Knowledge  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  VideoExtractor  │  SubtitleProcessor  │  ContentAnalyzer   │
│  (B站API)        │  (格式处理)         │  (LLM API)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Knowledge Manager                         │
├─────────────────────────────────────────────────────────────┤
│  SQLite Database  │  Search Engine  │  File Storage        │
└─────────────────────────────────────────────────────────────┘
```

### 核心技术栈
- **后端框架**: Flask + Python 3.8+
- **包管理**: PDM
- **数据库**: SQLite (初期) / PostgreSQL (扩展)
- **AI服务**: OpenAI API / Claude API
- **前端**: HTML + CSS + JavaScript (Flask Templates)
- **任务队列**: Celery + Redis (可选，用于异步处理)

## 数据模型设计

### 核心实体关系
```
User (1) ─── (N) Video (1) ─── (N) Subtitle (1) ─── (N) Analysis
                                    │
                                    │
                               (N) Knowledge (N) ─── (N) Tag
```

### 数据库表结构

#### videos 表
```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bvid VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    author VARCHAR(100),
    duration INTEGER,
    publish_date DATETIME,
    thumbnail_url VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### subtitles 表
```sql
CREATE TABLE subtitles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    language VARCHAR(10),
    format VARCHAR(10),
    content TEXT NOT NULL,
    file_path VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id)
);
```

#### analyses 表
```sql
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    subtitle_id INTEGER NOT NULL,
    summary TEXT,
    key_points TEXT,
    categories TEXT,
    tags TEXT,
    analysis_time FLOAT,
    model_used VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id),
    FOREIGN KEY (subtitle_id) REFERENCES subtitles(id)
);
```

#### knowledge_entries 表
```sql
CREATE TABLE knowledge_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    knowledge_type VARCHAR(50),
    source_timestamp INTEGER,
    importance INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);
```

#### tags 表
```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#007bff',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### knowledge_tags 表 (关联表)
```sql
CREATE TABLE knowledge_tags (
    knowledge_entry_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (knowledge_entry_id, tag_id),
    FOREIGN KEY (knowledge_entry_id) REFERENCES knowledge_entries(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);
```

## 模块分解与实现策略

### 1. 项目初始化模块 (Project Setup)
**目标**: 建立项目基础结构和开发环境

**技术决策**:
- 使用PDM管理虚拟环境和依赖
- 采用Flask Blueprint组织代码结构
- 配置SQLite数据库和Alembic迁移

**关键文件**:
```
bilibili_analyzer/
├── pyproject.toml              # PDM配置
├── app.py                     # Flask应用入口
├── config.py                  # 配置文件
├── requirements.txt           # 依赖列表
├── migrations/                # 数据库迁移
├── static/                    # 静态文件
├── templates/                 # HTML模板
└── bilibili_analyzer/         # 应用包
    ├── __init__.py
    ├── models.py              # 数据模型
    ├── routes.py              # 路由定义
    └── utils.py               # 工具函数
```

### 2. B站视频处理模块 (VideoExtractor)
**目标**: 实现B站视频信息提取和字幕下载

**技术决策**:
- 使用requests + BeautifulSoup解析B站页面
- 处理B站的反爬虫机制（User-Agent、Referer等）
- 支持多种字幕格式（JSON、XML、SRT）

**核心功能**:
```python
class VideoExtractor:
    def extract_video_info(bvid: str) -> VideoInfo
    def check_subtitle_available(bvid: str) -> bool
    def download_subtitle(bvid: str, language: str = 'zh') -> Subtitle
    def parse_subtitle_content(content: str, format: str) -> List[SubtitleLine]
```

**技术风险**:
- B站API变化频繁，需要设计灵活的解析策略
- 需要处理登录限制和验证码
- 字幕URL可能有时间限制

### 3. 大模型分析模块 (ContentAnalyzer)
**目标**: 使用大模型API分析字幕内容

**技术决策**:
- 支持多个大模型提供商（OpenAI、Claude等）
- 实现内容分块处理，避免token限制
- 设计缓存机制，减少API调用成本

**核心功能**:
```python
class ContentAnalyzer:
    def analyze_subtitle(subtitle_content: str) -> AnalysisResult
    def generate_summary(content: str) -> str
    def extract_key_points(content: str) -> List[str]
    def categorize_content(content: str) -> str
    def generate_tags(content: str) -> List[str]
    def build_knowledge_base(analysis_result: AnalysisResult) -> List[KnowledgeEntry]
```

**分析策略**:
```
输入: 字幕内容 → 预处理 → 分块 → LLM分析 → 结果整合 → 知识库构建
```

### 4. 知识库管理模块 (KnowledgeManager)
**目标**: 管理分析结果和知识条目

**技术决策**:
- 使用SQLite进行数据持久化
- 实现全文搜索功能
- 支持标签系统和分类管理

**核心功能**:
```python
class KnowledgeManager:
    def save_analysis_result(analysis_result: AnalysisResult)
    def search_knowledge(query: str) -> List[KnowledgeEntry]
    def get_knowledge_by_tags(tags: List[str]) -> List[KnowledgeEntry]
    def update_knowledge_entry(entry_id: int, updates: dict)
    def delete_knowledge_entry(entry_id: int)
    def export_knowledge(format: str) -> str
```

### 5. Web界面模块 (WebInterface)
**目标**: 提供用户友好的Web界面

**技术决策**:
- 使用Flask Templates渲染HTML
- 实现响应式设计
- 使用AJAX处理异步操作

**页面结构**:
```
/                    # 首页 - 视频输入
/analysis/:id        # 分析结果页面
/knowledge           # 知识库浏览
/search              # 搜索页面
/settings            # 设置页面
```

## API设计

### 内部API接口

#### 视频处理API
```python
POST /api/v1/video/extract
{
    "bvid": "BV1xx411c7mD"
}
Response: {
    "video_info": {...},
    "subtitle_available": true,
    "subtitle_languages": ["zh", "en"]
}
```

#### 字幕下载API
```python
POST /api/v1/subtitle/download
{
    "bvid": "BV1xx411c7mD",
    "language": "zh"
}
Response: {
    "subtitle_id": 123,
    "content": "...",
    "format": "json"
}
```

#### 内容分析API
```python
POST /api/v1/analyze
{
    "subtitle_id": 123,
    "analysis_type": "full"
}
Response: {
    "analysis_id": 456,
    "summary": "...",
    "key_points": [...],
    "categories": [...],
    "tags": [...]
}
```

### 前端JavaScript API

#### 异步任务处理
```javascript
// 提交视频分析任务
async function submitAnalysis(bvid) {
    const response = await fetch('/api/v1/analysis/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({bvid})
    });
    return await response.json();
}

// 检查分析进度
async function checkProgress(taskId) {
    const response = await fetch(`/api/v1/analysis/status/${taskId}`);
    return await response.json();
}
```

## 错误处理与异常管理

### 错误分类
1. **网络错误**: B站访问失败、API调用超时
2. **数据错误**: 字幕格式错误、视频不存在
3. **业务错误**: 分析失败、存储空间不足
4. **系统错误**: 数据库连接失败、配置错误

### 错误处理策略
```python
class AnalysisError(Exception):
    """分析过程异常"""
    pass

class SubtitleDownloadError(Exception):
    """字幕下载异常"""
    pass

class BilibiliAPIError(Exception):
    """B站API调用异常"""
    pass

# 全局异常处理
@app.errorhandler(AnalysisError)
def handle_analysis_error(error):
    return jsonify({
        'error': str(error),
        'code': 'ANALYSIS_ERROR'
    }), 500
```

## 性能优化策略

### 数据库优化
- 为常用查询字段创建索引
- 使用连接池管理数据库连接
- 实现数据分页查询

### API调用优化
- 实现结果缓存机制
- 使用异步处理避免阻塞
- 设置合理的超时时间

### 前端优化
- 实现懒加载和分页
- 使用CDN加速静态资源
- 优化图片加载

## 安全考虑

### 数据安全
- 敏感配置使用环境变量
- API密钥加密存储
- 数据库访问权限控制

### 访问控制
- 实现请求频率限制
- 输入参数验证和过滤
- 防止SQL注入和XSS攻击

### 隐私保护
- 用户数据本地存储
- 不收集不必要的个人信息
- 提供数据删除功能

## 部署与运维

### 开发环境
```bash
# 使用PDM管理环境
pdm install
pdm run dev

# 数据库迁移
pdm run migrate

# 运行测试
pdm run test
```

### 生产环境
```bash
# 使用Gunicorn部署
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# 使用Systemd管理服务
sudo systemctl enable bilibili-analyzer
sudo systemctl start bilibili-analyzer
```

### 监控与日志
- 实现结构化日志记录
- 设置错误报警机制
- 定期数据备份

## 测试策略

### 单元测试
```python
# 测试视频信息提取
def test_video_extraction():
    extractor = VideoExtractor()
    result = extractor.extract_video_info("BV1xx411c7mD")
    assert result.title is not None

# 测试字幕解析
def test_subtitle_parsing():
    parser = SubtitleParser()
    result = parser.parse_subtitle(content, "json")
    assert len(result.lines) > 0
```

### 集成测试
- 测试完整的分析流程
- 验证数据库操作
- 测试API接口

### 用户界面测试
- 手动测试主要用户流程
- 验证错误处理机制
- 测试响应式设计

## 项目里程碑

### Phase 1: 基础框架 (1-2天)
- [ ] 项目初始化和依赖配置
- [ ] 数据库模型设计和迁移
- [ ] 基础Flask应用结构

### Phase 2: 核心功能 (3-4天)
- [ ] B站视频信息提取
- [ ] 字幕下载和解析
- [ ] 大模型分析集成

### Phase 3: 知识库管理 (2-3天)
- [ ] 分析结果存储
- [ ] 知识条目管理
- [ ] 搜索和检索功能

### Phase 4: 用户界面 (2-3天)
- [ ] 主要页面开发
- [ ] 交互功能实现
- [ ] 响应式设计

### Phase 5: 测试与优化 (1-2天)
- [ ] 功能测试
- [ ] 性能优化
- [ ] 错误处理完善

## 风险评估与缓解

### 技术风险
- **B站API变化**: 实现灵活的解析策略
- **大模型API成本**: 实现智能缓存和分块处理
- **性能问题**: 使用异步处理和优化数据库查询

### 业务风险
- **用户需求变化**: 保持代码结构灵活
- **数据安全**: 实施完整的安全措施
- **维护成本**: 编写清晰的文档和测试

## 后续扩展计划

### 短期扩展 (1-2个月)
- 批量视频分析功能
- 更丰富的分析维度
- 知识库导出功能

### 长期扩展 (3-6个月)
- 多平台视频支持
- 智能推荐系统
- 知识图谱可视化

这个技术实现计划提供了完整的开发指导，涵盖了从技术选型到具体实现的各个方面。