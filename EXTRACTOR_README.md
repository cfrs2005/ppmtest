# Bilibili视频信息提取模块

## 概述

本模块实现了B站视频信息提取功能，包括视频元数据获取、字幕可用性检测、字幕文件下载和多格式字幕解析。

## 功能特性

### 核心功能
- ✅ **视频信息提取**: 获取视频标题、作者、时长、发布时间、播放量等
- ✅ **字幕可用性检测**: 检查视频是否有字幕
- ✅ **字幕下载**: 支持多语言字幕下载
- ✅ **多格式字幕解析**: 支持JSON、SRT、VTT格式

### 反爬虫机制
- ✅ **User-Agent轮换**: 自动切换不同的User-Agent
- ✅ **请求延迟**: 随机延迟避免请求频率过高
- ✅ **会话管理**: 支持重试机制和错误处理
- ✅ **Referer设置**: 正确设置请求头

### 数据模型
- ✅ **VideoInfo**: 视频信息数据类
- ✅ **Subtitle**: 字幕数据类
- ✅ **SubtitleLine**: 字幕行数据类
- ✅ **SubtitleInfo**: 字幕信息数据类

### 错误处理
- ✅ **VideoNotFoundError**: 视频不存在异常
- ✅ **SubtitleNotFoundError**: 字幕不存在异常
- ✅ **NetworkError**: 网络异常
- ✅ **ParseError**: 解析异常
- ✅ **RateLimitError**: 请求频率限制异常

## 项目结构

```
bilibili_analyzer/
├── __init__.py
├── models.py                    # 数据库模型
├── config.py                    # 配置文件
├── services.py                  # 数据库服务
├── utils/
│   ├── __init__.py
│   └── requests.py             # HTTP请求工具
├── extractors/
│   ├── __init__.py
│   ├── models.py               # 数据模型
│   └── video_extractor.py       # 视频提取器
├── main/
├── api/
└── admin/
```

## 安装和使用

### 基本使用

```python
from bilibili_analyzer.extractors import VideoExtractor

# 创建提取器
extractor = VideoExtractor(delay_range=(1, 2))

# 提取视频信息
video_info = extractor.extract_video_info("BV1BW411j7y4")
print(f"视频标题: {video_info.title}")
print(f"视频作者: {video_info.author}")
print(f"视频时长: {video_info.duration}秒")

# 检查字幕可用性
subtitle_available = extractor.check_subtitle_available("BV1BW411j7y4")
print(f"字幕可用: {subtitle_available}")

# 下载字幕
if subtitle_available:
    subtitle = extractor.download_subtitle("BV1BW411j7y4", 'zh-CN')
    print(f"字幕语言: {subtitle.language}")
    print(f"字幕行数: {len(subtitle.lines)}")
```

### 批量处理

```python
from bilibili_analyzer.extractors import VideoExtractor

extractor = VideoExtractor(delay_range=(2, 3))

# 批量处理视频
video_list = ["BV1BW411j7y4", "BV1GJ411x7h7"]

for bvid in video_list:
    try:
        result = extractor.extract_all(bvid)
        if result['video_info']:
            print(f"视频: {result['video_info'].title}")
            print(f"字幕: {result['subtitle_available']}")
    except Exception as e:
        print(f"处理失败: {str(e)}")
```

### 字幕格式解析

```python
from bilibili_analyzer.extractors import VideoExtractor

extractor = VideoExtractor()

# JSON格式
json_content = '''{"body": [{"from": 0.0, "to": 5.0, "content": "字幕内容"}]}'''
lines = extractor.parse_subtitle_content(json_content, 'json')

# SRT格式
srt_content = '''1
00:00:00,000 --> 00:00:05,000
字幕内容'''
lines = extractor.parse_subtitle_content(srt_content, 'srt')

# VTT格式
vtt_content = '''WEBVTT

00:00:00.000 --> 00:00:05.000
字幕内容'''
lines = extractor.parse_subtitle_content(vtt_content, 'vtt')
```

### 数据库集成

```python
from bilibili_analyzer.services import DatabaseService

# 创建数据库服务
service = DatabaseService()

# 提取并保存视频信息
result = service.extract_and_save_video("BV1BW411j7y4", language='zh-CN')

if result['success']:
    video = result['video']
    subtitle = result['subtitle']
    print(f"视频已保存: {video.title}")
    if subtitle:
        print(f"字幕已保存: {subtitle.language}")
```

## 性能指标

- **字幕解析性能**: 1000行字幕解析 < 1秒
- **单个视频提取**: < 10秒（网络依赖）
- **内存使用**: 低内存占用
- **并发支持**: 支持批量处理

## 支持的字幕格式

1. **JSON格式**: B站原生JSON字幕格式
2. **SRT格式**: SubRip字幕格式
3. **VTT格式**: WebVTT字幕格式
4. **XML格式**: XML字幕格式

## 错误处理

模块提供完整的错误处理机制：

- `VideoNotFoundError`: 视频不存在
- `SubtitleNotFoundError`: 字幕不存在
- `NetworkError`: 网络请求失败
- `ParseError`: 字幕解析失败
- `RateLimitError`: 请求频率限制
- `ExtractionError`: 通用提取异常

## 测试

运行核心功能测试：

```bash
python3 tests/test_core.py
```

运行使用示例：

```bash
python3 examples/usage_example.py
```

## 配置选项

### VideoExtractor配置

```python
extractor = VideoExtractor(
    delay_range=(1, 3)  # 请求延迟范围（秒）
)
```

### BilibiliRequestHandler配置

```python
from bilibili_analyzer.utils.requests import BilibiliRequestHandler

handler = BilibiliRequestHandler(
    delay_range=(1, 3),    # 请求延迟范围
    max_retries=3         # 最大重试次数
)
```

## 注意事项

1. **请求频率**: 请合理设置延迟，避免对B站造成过大压力
2. **网络环境**: 确保网络连接正常，能够访问B站
3. **视频权限**: 部分视频可能需要登录或地区限制
4. **字幕限制**: 不是所有视频都有字幕
5. **使用规范**: 请遵守B站的使用条款和robots.txt

## 扩展功能

### 添加新的字幕格式

1. 在`SubtitleFormat`类中添加新格式
2. 在`VideoExtractor`中添加对应的解析方法
3. 更新`parse_subtitle_content`方法

### 添加新的数据源

1. 创建新的Extractor类
2. 实现相应的接口方法
3. 集成到DatabaseService中

## 许可证

本项目遵循MIT许可证。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。