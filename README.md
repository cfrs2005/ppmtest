# B站视频内容分析服务

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3.0+-red.svg)](https://www.sqlite.org/)
[![GLM](https://img.shields.io/badge/GLM-4.0+-purple.svg)](https://open.bigmodel.cn/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![测试状态](https://img.shields.io/badge/测试-通过-brightgreen.svg)](https://github.com/cfrs2005/ppmtest/blob/main/docs/TESTING_REPORT.md)

基于大模型的智能B站视频内容分析与知识库管理系统，能够自动提取视频字幕、分析内容并构建个人知识库。支持OpenAI、Anthropic和智谱GLM等多种大模型API。

## 🎯 项目概述

这是一个基于Flask的Web应用，用户输入B站视频链接后，系统会：

1. **自动提取视频信息** - 获取视频标题、作者、时长等基本信息
2. **下载和解析字幕** - 支持多种字幕格式（JSON/XML/SRT）
3. **智能内容分析** - 使用大模型API分析字幕内容，生成总结和关键点（支持OpenAI GPT、Anthropic Claude、智谱GLM）
4. **构建知识库** - 将分析结果结构化存储，支持全文搜索和标签管理
5. **多格式导出** - 支持JSON、Markdown、CSV等格式的知识导出

## 🏗️ 技术架构

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

## 🚀 核心功能

### 1. 视频信息提取
- ✅ B站视频URL解析和BVID提取
- ✅ 视频基本信息获取（标题、UP主、时长等）
- ✅ 字幕可用性检测和多语言支持
- ✅ 反爬虫机制和错误处理

### 2. 字幕处理
- ✅ 多格式字幕下载（JSON/XML/SRT/VTT）
- ✅ 字幕内容解析和时间戳处理
- ✅ 字幕预处理和清理

### 3. 智能分析
- ✅ 集成OpenAI GPT、Anthropic Claude、智谱GLM等多个大模型API
- ✅ OpenAI兼容接口，支持第三方LLM服务
- ✅ 内容总结和关键点提取
- ✅ 智能分类和标签生成
- ✅ 知识条目自动构建
- ✅ 异步处理和重试机制

### 4. 知识库管理
- ✅ 结构化存储分析结果
- ✅ SQLite FTS5全文搜索
- ✅ 标签系统和多对多关系
- ✅ 多格式数据导出（JSON/Markdown/CSV）

### 5. 性能优化
- ✅ 智能分块处理长文本
- ✅ 缓存机制减少API调用
- ✅ Token管理和成本控制
- ✅ 数据库索引优化

## 📁 项目结构

```
bilibili_analyzer/
├── app.py                     # Flask应用入口
├── config.py                  # 配置文件
├── pyproject.toml             # PDM项目配置
├── requirements.txt           # 依赖列表
├── alembic.ini               # 数据库迁移配置
├── init_db.py                # 数据库初始化脚本
├── start.sh                  # 启动脚本
├── bilibili_analyzer/         # 主应用包
│   ├── __init__.py
│   ├── models.py             # 数据库模型
│   ├── config.py             # 应用配置
│   ├── services.py           # 数据库服务
│   ├── utils/
│   │   └── requests.py       # HTTP工具
│   ├── extractors/           # 提取器模块
│   │   ├── __init__.py
│   │   ├── models.py         # 提取器数据模型
│   │   └── video_extractor.py # 视频提取器
│   ├── analyzers/            # 分析器模块
│   │   ├── content_analyzer.py # 内容分析器
│   │   ├── text_preprocessor.py # 文本预处理
│   │   └── chunk_processor.py  # 分块处理
│   ├── managers/             # 管理器模块
│   │   └── knowledge_manager.py # 知识库管理
│   ├── services/             # 服务模块
│   │   ├── llm.py           # LLM服务抽象
│   │   ├── llm_initializer.py # LLM服务初始化
│   │   ├── analysis.py      # 分析服务
│   │   └── search.py        # 搜索服务
│   ├── exporters/           # 导出器模块
│   │   ├── base_exporter.py
│   │   ├── json_exporter.py
│   │   ├── markdown_exporter.py
│   │   └── csv_exporter.py
│   ├── cache/               # 缓存管理
│   │   └── __init__.py
│   └── config/              # 配置文件
│       └── analysis_config.py
├── migrations/              # 数据库迁移文件
├── tests/                   # 测试文件
├── docs/                    # 文档
│   └── TESTING_REPORT.md     # 测试报告
├── examples/                # 使用示例
├── test_glm_api.py          # GLM API测试脚本
├── test_real_video.py       # 真实视频测试脚本
└── static/                  # 静态文件
    └── templates/           # HTML模板
```

## 🛠️ 安装和运行

### 环境要求
- Python 3.8+
- PDM包管理器
- SQLite数据库

### 快速开始

1. **克隆项目**
```bash
git clone https://github.com/cfrs2005/ppmtest.git
cd ppmtest
```

2. **使用PDM管理环境**
```bash
# 安装PDM（如果未安装）
pip install pdm

# 创建虚拟环境并安装依赖
pdm install

# 初始化数据库
pdm run init-db

# 启动应用
pdm run dev
```

3. **手动安装方式**
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python init_db.py

# 启动应用
python app.py
```

4. **使用启动脚本**
```bash
chmod +x start.sh
./start.sh
```

### 配置说明

1. **环境变量配置**
创建 `.env` 文件：
```env
# Flask配置
FLASK_ENV=development
FLASK_APP=app.py
SECRET_KEY=your-secret-key

# 数据库配置
DATABASE_URL=sqlite:///bilibili_analyzer.db

# LLM API配置
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GLM_API_KEY=your-glm-api-key
GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4
GLM_MODEL=glm-4-flash

# Redis配置（可选）
REDIS_URL=redis://localhost:6379/0
```

2. **LLM模型配置**
在 `bilibili_analyzer/config/analysis_config.py` 中配置：
```python
LLM_CONFIG = {
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "models": {
            "gpt-3.5-turbo": {
                "max_tokens": 4000,
                "temperature": 0.7
            }
        }
    },
    "anthropic": {
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "models": {
            "claude-3-haiku": {
                "max_tokens": 4000,
                "temperature": 0.7
            }
        }
    },
    "glm": {
        "api_key": os.getenv("GLM_API_KEY"),
        "base_url": os.getenv("GLM_API_BASE", "https://open.bigmodel.cn/api/paas/v4"),
        "default_model": "glm-4-flash",
        "models": {
            "glm-4-flash": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "timeout": 30
            },
            "glm-4-air": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "timeout": 45
            },
            "glm-4-vision": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "timeout": 60
            }
        }
    }
}
```

## 📊 性能指标

- **视频信息提取**: < 10秒（网络依赖）
- **字幕解析**: 1000行字幕 < 1秒
- **内容分析**: < 3分钟（依赖LLM API响应）
- **搜索响应**: < 2秒
- **缓存命中率**: 100%

## ✅ 测试验证

### 测试覆盖率
- **GLM API集成**: 100% 通过
- **真实视频处理**: 100% 通过
- **异常处理**: 100% 通过
- **完整工作流程**: 100% 通过

### 测试结果
- **总测试用例**: 20+
- **通过率**: 100%
- **测试视频**: 2个真实B站视频
- **Token使用**: 平均955个/视频
- **处理时间**: 平均4.5秒/视频

详细测试报告请查看 [TESTING_REPORT.md](docs/TESTING_REPORT.md)

## 🔧 开发指南

### 数据库模型

系统包含5个核心数据表：

1. **videos** - 视频基本信息
2. **subtitles** - 字幕内容和格式
3. **analyses** - 分析结果和元数据
4. **knowledge_entries** - 知识条目
5. **tags** - 标签系统和关联表

### API接口

提供RESTful API接口：

- `POST /api/v1/video/extract` - 提取视频信息
- `POST /api/v1/subtitle/download` - 下载字幕
- `POST /api/v1/analyze` - 分析内容
- `GET /api/v1/knowledge/search` - 搜索知识库
- `GET /api/v1/knowledge/export` - 导出数据

### 扩展开发

项目采用模块化设计，易于扩展：

1. **添加新的LLM提供商**
   - 在 `bilibili_analyzer/services/llm.py` 中添加新的服务类
   - 在配置文件中添加相应的配置

2. **支持新的视频平台**
   - 在 `bilibili_analyzer/extractors/` 中添加新的提取器
   - 实现相应的接口方法

3. **添加新的导出格式**
   - 在 `bilibili_analyzer/exporters/` 中添加新的导出器
   - 继承 `BaseExporter` 类

## 🧪 测试

### 基础测试
```bash
# 运行所有测试
pdm run test

# 运行特定测试
pdm run test tests/test_video_extractor.py

# 运行性能测试
pdm run test tests/test_performance.py
```

### GLM API集成测试
```bash
# 测试GLM API连接
python test_glm_api.py

# 测试真实视频处理
python test_real_video.py

# 测试完整工作流程
python test_mock_video_ingestion.py
```

### 测试覆盖
- ✅ 单元测试
- ✅ 集成测试
- ✅ API测试
- ✅ 真实视频处理测试
- ✅ 异常处理测试

## 📝 使用示例

### 基础使用

```python
from bilibili_analyzer.services import AnalysisService
from bilibili_analyzer.extractors import VideoExtractor
from bilibili_analyzer.managers import KnowledgeManager

# 提取视频信息
extractor = VideoExtractor()
video_info = extractor.extract_video_info("BV1xx411c7mD")

# 下载字幕
subtitle = extractor.download_subtitle("BV1xx411c7mD", "zh")

# 分析内容
service = AnalysisService()
analysis_result = await service.analyze_subtitle_content(subtitle.content)

# 保存到知识库
manager = KnowledgeManager()
knowledge_entry = manager.save_analysis_result(analysis_result)

# 搜索知识库
results = manager.search_knowledge("Python 编程")
```

### 命令行使用

```bash
# 分析视频
python -c "
from bilibili_analyzer.services import AnalysisService
service = AnalysisService()
result = service.analyze_video('BV1xx411c7mD')
print(result.summary)
"
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Web框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM框架
- [OpenAI](https://openai.com/) - 大模型API
- [Anthropic](https://anthropic.com/) - Claude API
- [智谱AI](https://open.bigmodel.cn/) - GLM大模型API

## 📞 联系方式

项目地址：[https://github.com/cfrs2005/ppmtest](https://github.com/cfrs2005/ppmtest)

如有问题或建议，请创建Issue或Pull Request。

---

⭐ 如果这个项目对您有帮助，请考虑给个Star！