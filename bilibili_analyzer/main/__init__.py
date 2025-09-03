"""
Main蓝图 - 主要页面路由
"""

from flask import Blueprint, render_template, jsonify, request
from bilibili_analyzer.models import Channel, Video, AnalysisResult, KnowledgeEntry, Tag
from bilibili_analyzer import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """首页"""
    return render_template('index.html')

@bp.route('/dashboard')
def dashboard():
    """仪表板"""
    # 获取统计数据
    channel_count = Channel.query.count()
    video_count = Video.query.count()
    analysis_count = AnalysisResult.query.count()
    
    return render_template('dashboard.html', 
                         channel_count=channel_count,
                         video_count=video_count,
                         analysis_count=analysis_count)

@bp.route('/channels')
def channels():
    """频道列表"""
    page = request.args.get('page', 1, type=int)
    channels = Channel.query.paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('channels.html', channels=channels)

@bp.route('/channels/<int:channel_id>')
def channel_detail(channel_id):
    """频道详情"""
    channel = Channel.query.get_or_404(channel_id)
    videos = Video.query.filter_by(channel_id=channel_id).order_by(Video.published_at.desc()).limit(10).all()
    return render_template('channel_detail.html', channel=channel, videos=videos)

@bp.route('/videos')
def videos():
    """视频列表"""
    page = request.args.get('page', 1, type=int)
    videos = Video.query.order_by(Video.published_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('videos.html', videos=videos)

@bp.route('/videos/<int:video_id>')
def video_detail(video_id):
    """视频详情"""
    video = Video.query.get_or_404(video_id)
    analysis_results = AnalysisResult.query.filter_by(video_id=video_id).all()
    return render_template('video_detail.html', video=video, analysis_results=analysis_results)

@bp.route('/knowledge')
def knowledge():
    """知识库页面"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    knowledge_type = request.args.get('knowledge_type')
    
    # 构建查询
    query = KnowledgeEntry.query
    
    # 搜索过滤
    if search:
        query = query.filter(
            db.or_(
                KnowledgeEntry.title.contains(search),
                KnowledgeEntry.content.contains(search)
            )
        )
    
    # 类型过滤
    if knowledge_type:
        query = query.filter(KnowledgeEntry.knowledge_type == knowledge_type)
    
    # 分页查询
    entries = query.order_by(KnowledgeEntry.importance.desc(), KnowledgeEntry.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # 获取所有标签
    tags = Tag.query.all()
    
    return render_template('knowledge.html', 
                         entries=entries, 
                         tags=tags,
                         search=search,
                         knowledge_type=knowledge_type)

@bp.route('/knowledge/<int:entry_id>')
def knowledge_detail(entry_id):
    """知识条目详情"""
    entry = KnowledgeEntry.query.get_or_404(entry_id)
    return render_template('knowledge_detail.html', entry=entry)

@bp.route('/settings')
def settings():
    """设置页面"""
    return render_template('settings.html')

@bp.route('/analysis/<int:analysis_id>')
def analysis_detail(analysis_id):
    """分析结果详情"""
    # 需要导入Analysis模型
    from bilibili_analyzer.models import Analysis
    analysis = Analysis.query.get_or_404(analysis_id)
    return render_template('analysis_detail.html', analysis=analysis)

@bp.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')