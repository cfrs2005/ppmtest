# Bilibili视频分析系统 - 项目结构

## 📁 项目目录结构

```
ppmtest/
├── 📄 app.py                          # Flask应用入口
├── 📄 config.py                       # 配置文件（已移至bilibili_analyzer/）
├── 📄 pyproject.toml                  # PDM项目配置
├── 📄 requirements.txt                # Python依赖列表
├── 📄 alembic.ini                     # Alembic迁移配置
├── 📄 init_db.py                      # 数据库初始化脚本
├── 📄 start.sh                        # 启动脚本
├── 📄 .env                            # 环境变量
├── 📄 .gitignore                      # Git忽略文件
├── 📄 venv/                           # 虚拟环境
│
├── 📁 bilibili_analyzer/              # 主应用包
│   ├── 📄 __init__.py                 # 包初始化文件
│   ├── 📄 models.py                   # 数据库模型
│   ├── 📄 config.py                   # 配置文件
│   ├── 📁 main/                       # 主页面蓝图
│   │   └── 📄 __init__.py
│   ├── 📁 api/                        # API蓝图
│   │   └── 📄 __init__.py
│   └── 📁 admin/                      # 管理后台蓝图
│       └── 📄 __init__.py
│
└── 📁 migrations/                     # 数据库迁移
    ├── 📄 env.py                      # 迁移环境
    ├── 📄 script.py.mako              # 迁移模板
    └── 📁 versions/                   # 迁移版本文件
```

## 🚀 快速启动

### 方式1：使用启动脚本
```bash
./start.sh
```

### 方式2：手动启动
```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
python init_db.py

# 4. 启动应用
python app.py
```

## 🔧 技术栈

- **Web框架**: Flask 2.3.0
- **数据库**: SQLite (可配置为PostgreSQL/MySQL)
- **ORM**: SQLAlchemy
- **数据库迁移**: Alembic
- **包管理**: PDM / pip
- **环境管理**: python-dotenv

## 📊 数据模型

### 频道 (Channel)
- 频道基本信息
- 粉丝数、视频数统计
- 创建和更新时间

### 视频 (Video)
- 视频基本信息
- 播放量、点赞数、评论数等
- 关联频道

### 分析结果 (AnalysisResult)
- 视频分析数据
- 支持多种分析类型
- 置信度评分

### 用户 (User)
- 用户管理
- 权限控制

## 🌐 API接口

### 频道管理
- `GET /api/channels` - 获取频道列表
- `POST /api/channels` - 创建频道
- `GET /api/channels/<id>` - 获取单个频道
- `PUT /api/channels/<id>` - 更新频道
- `DELETE /api/channels/<id>` - 删除频道

### 视频管理
- `GET /api/videos` - 获取视频列表
- `POST /api/videos` - 创建视频
- `GET /api/videos/<id>` - 获取单个视频

### 分析结果
- `GET /api/analysis/<video_id>` - 获取视频分析结果
- `POST /api/analysis` - 创建分析结果

### 统计信息
- `GET /api/stats` - 获取系统统计

## 🎯 项目特性

### ✅ 已完成
- [x] Flask应用基础架构
- [x] 数据库模型设计
- [x] Blueprint模块化结构
- [x] RESTful API接口
- [x] 数据库迁移系统
- [x] 环境变量配置
- [x] 虚拟环境设置
- [x] 基础启动脚本

### 🔧 下一步
- [ ] 添加Bilibili数据爬取
- [ ] 实现视频分析算法
- [ ] 创建前端界面
- [ ] 添加用户认证
- [ ] 配置Celery任务队列
- [ ] 添加日志系统
- [ ] 部署配置

## 📝 开发说明

### 添加新的API接口
1. 在相应的蓝图目录下创建新的路由
2. 在`models.py`中添加数据模型（如需要）
3. 运行数据库迁移
4. 测试新接口

### 数据库迁移
```bash
# 创建迁移
flask db migrate -m "描述"

# 应用迁移
flask db upgrade
```

### 环境配置
复制`.env`文件并根据需要修改配置：
```bash
cp .env.example .env
```

## 📄 许可证

MIT License