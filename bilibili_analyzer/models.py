"""
Bilibili视频分析系统 - 数据库模型
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON
import json

# 创建数据库实例
db = SQLAlchemy()

class Channel(db.Model):
    """Bilibili频道模型（保留以向后兼容）"""
    __tablename__ = 'channels'
    
    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    avatar_url = db.Column(db.String(500))
    follower_count = db.Column(db.Integer, default=0)
    video_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Channel {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'channel_id': self.channel_id,
            'name': self.name,
            'description': self.description,
            'avatar_url': self.avatar_url,
            'follower_count': self.follower_count,
            'video_count': self.video_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }

class Video(db.Model):
    """Bilibili视频模型"""
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True)
    bvid = db.Column(db.String(20), unique=True, nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    author = db.Column(db.String(100))
    duration = db.Column(db.Integer)  # 视频时长（秒）
    publish_date = db.Column(db.DateTime)
    thumbnail_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    subtitles = db.relationship('Subtitle', backref='video', lazy='dynamic', cascade='all, delete-orphan')
    analyses = db.relationship('Analysis', backref='video', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Video {self.title}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'bvid': self.bvid,
            'title': self.title,
            'author': self.author,
            'duration': self.duration,
            'publish_date': self.publish_date.isoformat() if self.publish_date else None,
            'thumbnail_url': self.thumbnail_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_latest_subtitle(self):
        """获取最新字幕"""
        return self.subtitles.order_by(Subtitle.created_at.desc()).first()
    
    def get_latest_analysis(self):
        """获取最新分析结果"""
        return self.analyses.order_by(Analysis.created_at.desc()).first()

class Subtitle(db.Model):
    """字幕模型"""
    __tablename__ = 'subtitles'
    
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    language = db.Column(db.String(10))  # zh, en, etc.
    format = db.Column(db.String(10))  # json, xml, srt
    content = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    analyses = db.relationship('Analysis', backref='subtitle', lazy='dynamic', cascade='all, delete-orphan')
    
    # 索引
    __table_args__ = (
        Index('idx_subtitle_video_id', 'video_id'),
        Index('idx_subtitle_language', 'language'),
    )
    
    def __repr__(self):
        return f'<Subtitle {self.id} for Video {self.video_id}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'language': self.language,
            'format': self.format,
            'content': self.content,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_content_lines(self):
        """获取字幕内容行"""
        if self.format == 'json':
            try:
                data = json.loads(self.content)
                return data.get('body', []) if isinstance(data, dict) else []
            except json.JSONDecodeError:
                return []
        elif self.format == 'srt':
            # 简单的SRT解析
            lines = []
            current_entry = {}
            for line in self.content.split('\n'):
                line = line.strip()
                if line.isdigit():
                    if current_entry:
                        lines.append(current_entry)
                    current_entry = {'index': int(line)}
                elif '-->' in line:
                    time_parts = line.split('-->')
                    current_entry['start_time'] = time_parts[0].strip()
                    current_entry['end_time'] = time_parts[1].strip()
                elif line and current_entry:
                    current_entry['text'] = current_entry.get('text', '') + line + '\n'
            if current_entry:
                lines.append(current_entry)
            return lines
        return []

class Analysis(db.Model):
    """分析结果模型"""
    __tablename__ = 'analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    subtitle_id = db.Column(db.Integer, db.ForeignKey('subtitles.id'), nullable=False)
    summary = db.Column(db.Text)
    key_points = db.Column(db.Text)  # JSON格式的关键点数组
    categories = db.Column(db.Text)  # JSON格式的分类数组
    tags = db.Column(db.Text)  # JSON格式的标签数组
    analysis_time = db.Column(db.Float)  # 分析耗时（秒）
    model_used = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    knowledge_entries = db.relationship('KnowledgeEntry', backref='analysis', lazy='dynamic', cascade='all, delete-orphan')
    
    # 索引
    __table_args__ = (
        Index('idx_analysis_video_id', 'video_id'),
        Index('idx_analysis_subtitle_id', 'subtitle_id'),
        Index('idx_analysis_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f'<Analysis {self.id} for Video {self.video_id}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'subtitle_id': self.subtitle_id,
            'summary': self.summary,
            'key_points': self.get_key_points(),
            'categories': self.get_categories(),
            'tags': self.get_tags(),
            'analysis_time': self.analysis_time,
            'model_used': self.model_used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_key_points(self):
        """获取关键点列表"""
        if self.key_points:
            try:
                return json.loads(self.key_points)
            except json.JSONDecodeError:
                return []
        return []
    
    def get_categories(self):
        """获取分类列表"""
        if self.categories:
            try:
                return json.loads(self.categories)
            except json.JSONDecodeError:
                return []
        return []
    
    def get_tags(self):
        """获取标签列表"""
        if self.tags:
            try:
                return json.loads(self.tags)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_key_points(self, points):
        """设置关键点列表"""
        self.key_points = json.dumps(points) if points else None
    
    def set_categories(self, categories):
        """设置分类列表"""
        self.categories = json.dumps(categories) if categories else None
    
    def set_tags(self, tags):
        """设置标签列表"""
        self.tags = json.dumps(tags) if tags else None

class KnowledgeEntry(db.Model):
    """知识条目模型"""
    __tablename__ = 'knowledge_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('analyses.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    knowledge_type = db.Column(db.String(50))  # concept, fact, method, etc.
    source_timestamp = db.Column(db.Integer)  # 源视频时间戳（秒）
    importance = db.Column(db.Integer, default=1)  # 重要性等级 1-5
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    tags = db.relationship('Tag', secondary='knowledge_tags', backref='knowledge_entries', lazy='dynamic')
    
    # 索引
    __table_args__ = (
        Index('idx_knowledge_analysis_id', 'analysis_id'),
        Index('idx_knowledge_type', 'knowledge_type'),
        Index('idx_knowledge_importance', 'importance'),
        Index('idx_knowledge_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f'<KnowledgeEntry {self.title}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'title': self.title,
            'content': self.content,
            'knowledge_type': self.knowledge_type,
            'source_timestamp': self.source_timestamp,
            'importance': self.importance,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tags': [tag.name for tag in self.tags]
        }
    
    def add_tag(self, tag_name):
        """添加标签"""
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag_name):
        """移除标签"""
        tag = Tag.query.filter_by(name=tag_name).first()
        if tag and tag in self.tags:
            self.tags.remove(tag)

class Tag(db.Model):
    """标签模型"""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    color = db.Column(db.String(7), default='#007bff')  # 十六进制颜色
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Tag {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# 知识条目与标签的关联表
knowledge_tags = db.Table('knowledge_tags',
    db.Column('knowledge_entry_id', db.Integer, db.ForeignKey('knowledge_entries.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
    db.Index('idx_knowledge_tags_entry_id', 'knowledge_entry_id'),
    db.Index('idx_knowledge_tags_tag_id', 'tag_id')
)

# 辅助函数和查询方法
def get_or_create_tag(tag_name, color=None):
    """获取或创建标签"""
    tag = Tag.query.filter_by(name=tag_name).first()
    if not tag:
        tag = Tag(name=tag_name, color=color or '#007bff')
        db.session.add(tag)
    return tag

def search_knowledge_entries(query, limit=50):
    """搜索知识条目"""
    # 简单的全文搜索，可以后续优化为使用全文索引
    return KnowledgeEntry.query.filter(
        db.or_(
            KnowledgeEntry.title.contains(query),
            KnowledgeEntry.content.contains(query)
        )
    ).order_by(KnowledgeEntry.importance.desc(), KnowledgeEntry.created_at.desc()).limit(limit).all()

def get_videos_by_tag(tag_name):
    """根据标签获取视频"""
    tag = Tag.query.filter_by(name=tag_name).first()
    if not tag:
        return []
    
    return Video.query.join(Video.analyses).join(Analysis.knowledge_entries).join(
        knowledge_tags, knowledge_tags.c.knowledge_entry_id == KnowledgeEntry.id
    ).join(Tag).filter(Tag.id == tag.id).distinct().all()

def get_popular_tags(limit=20):
    """获取热门标签"""
    return Tag.query.join(Tag.knowledge_entries).group_by(Tag.id).order_by(
        db.func.count(Tag.id).desc()
    ).limit(limit).all()

def get_recent_analyses(limit=10):
    """获取最近的分析"""
    return Analysis.query.order_by(Analysis.created_at.desc()).limit(limit).all()

def get_video_statistics():
    """获取视频统计信息"""
    return {
        'total_videos': Video.query.count(),
        'total_analyses': Analysis.query.count(),
        'total_knowledge_entries': KnowledgeEntry.query.count(),
        'total_tags': Tag.query.count(),
        'videos_with_analysis': Video.query.join(Video.analyses).distinct().count()
    }

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }